"""OpenStreetMap: points of interest, addresses, parks, major roads and railways.

Source: Geofabrik extract of Croatia (ODbL). One pass over the PBF writes:
  osm_pois.parquet      category, name, lon, lat, osm_id (+ tags used)
  osm_parks.parquet     park polygons (WKB, EPSG:4326)
  osm_addresses.parquet street, housenumber, place, postcode, lon, lat
  osm_noise_lines.parquet  major roads and main railways as lines (WKB)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import osmium
import pyarrow as pa
import pyarrow.parquet as pq
from shapely import wkb

from ingest.common import download, file_date, processed_dir, raw_dir, record_source

PBF_URL = "https://download.geofabrik.de/europe/croatia-latest.osm.pbf"

GROCERY_SHOPS = {"supermarket", "convenience", "greengrocer"}
MAJOR_ROADS = {"motorway", "trunk", "primary"}
RAIL_EXCLUDED_SERVICE = {"yard", "siding", "spur", "crossover"}

FILTER_KEYS = (
    "amenity",
    "shop",
    "leisure",
    "highway",
    "railway",
    "public_transport",
    "addr:housenumber",
)


def classify(tags: Any) -> list[str]:
    """Return POI categories for an OSM object's tags."""
    cats: list[str] = []
    amenity = tags.get("amenity")
    if tags.get("shop") in GROCERY_SHOPS:
        cats.append("grocery")
    if tags.get("leisure") == "playground":
        cats.append("playground")
    if amenity == "pharmacy":
        cats.append("pharmacy")
    if amenity == "doctors":
        cats.append("doctor")
    if amenity == "kindergarten":
        cats.append("kindergarten")
    if amenity == "school":
        cats.append("school")
    if amenity == "recycling":
        cats.append("recycling")
    railway = tags.get("railway")
    if (
        tags.get("highway") == "bus_stop"
        or railway in {"tram_stop", "halt", "station"}
        or (tags.get("public_transport") == "platform" and tags.get("bus") == "yes")
    ):
        cats.append("stop")
    return cats


def stop_mode(tags: Any) -> str:
    railway = tags.get("railway")
    if railway == "tram_stop" or tags.get("tram") == "yes":
        return "tram"
    if railway in {"halt", "station"}:
        return "train" if tags.get("station") not in {"subway", "light_rail"} else "rail"
    return "bus"


class _Collector:
    def __init__(self) -> None:
        self.pois: dict[str, list[Any]] = {
            k: [] for k in ("category", "name", "lon", "lat", "osm_id", "extra")
        }
        self.parks: dict[str, list[Any]] = {k: [] for k in ("name", "osm_id", "geometry")}
        self.addr: dict[str, list[Any]] = {
            k: [] for k in ("street", "housenumber", "place", "postcode", "lon", "lat")
        }
        self.lines: dict[str, list[Any]] = {k: [] for k in ("kind", "ref", "osm_id", "geometry")}

    def add_point(self, osm_id: str, tags: Any, lon: float, lat: float) -> None:
        for cat in classify(tags):
            extra = ""
            if cat == "stop":
                extra = stop_mode(tags)
            elif cat == "recycling":
                extra = tags.get("recycling_type", "")
            elif cat == "grocery":
                extra = tags.get("shop", "")
            self.pois["category"].append(cat)
            self.pois["name"].append(tags.get("name", ""))
            self.pois["lon"].append(lon)
            self.pois["lat"].append(lat)
            self.pois["osm_id"].append(osm_id)
            self.pois["extra"].append(extra)
        housenumber = tags.get("addr:housenumber")
        street = tags.get("addr:street") or tags.get("addr:place")
        if housenumber and street:
            self.addr["street"].append(street)
            self.addr["housenumber"].append(housenumber)
            self.addr["place"].append(tags.get("addr:city") or tags.get("addr:place") or "")
            self.addr["postcode"].append(tags.get("addr:postcode", ""))
            self.addr["lon"].append(lon)
            self.addr["lat"].append(lat)


def extract(pbf: Path) -> _Collector:
    wkb_factory = osmium.geom.WKBFactory()
    col = _Collector()
    processor = (
        osmium.FileProcessor(str(pbf))
        .with_locations()
        .with_areas(osmium.filter.KeyFilter("leisure", "amenity", "shop", "addr:housenumber"))
        .with_filter(osmium.filter.KeyFilter(*FILTER_KEYS))
    )
    obj: Any
    for obj in processor:
        tags = obj.tags
        if obj.is_node():
            loc = obj.location
            if loc.valid():
                col.add_point(f"n{obj.id}", tags, loc.lon, loc.lat)
        elif obj.is_way():
            highway = tags.get("highway")
            railway = tags.get("railway")
            kind = None
            if highway in MAJOR_ROADS:
                kind = highway
            elif railway == "rail" and tags.get("service") not in RAIL_EXCLUDED_SERVICE:
                kind = "rail"
            if kind is not None:
                try:
                    geom = wkb_factory.create_linestring(obj)
                except (osmium.InvalidLocationError, RuntimeError):
                    continue
                col.lines["kind"].append(kind)
                col.lines["ref"].append(tags.get("ref", ""))
                col.lines["osm_id"].append(f"w{obj.id}")
                col.lines["geometry"].append(bytes.fromhex(geom))
        elif obj.is_area():
            try:
                geom_hex = wkb_factory.create_multipolygon(obj)
            except (osmium.InvalidLocationError, RuntimeError):
                continue
            shape = wkb.loads(bytes.fromhex(geom_hex))
            osm_id = f"{'w' if obj.from_way() else 'r'}{obj.orig_id()}"
            point = shape.representative_point()
            col.add_point(osm_id, tags, point.x, point.y)
            if tags.get("leisure") == "park":
                col.parks["name"].append(tags.get("name", ""))
                col.parks["osm_id"].append(osm_id)
                col.parks["geometry"].append(bytes.fromhex(geom_hex))
    return col


def run() -> None:
    pbf = download(PBF_URL, raw_dir("osm") / "croatia-latest.osm.pbf")
    col = extract(pbf)
    out = processed_dir()
    pq.write_table(pa.table(col.pois), out / "osm_pois.parquet")
    pq.write_table(pa.table(col.parks), out / "osm_parks.parquet")
    pq.write_table(pa.table(col.addr), out / "osm_addresses.parquet")
    pq.write_table(pa.table(col.lines), out / "osm_noise_lines.parquet")
    record_source(
        "osm",
        title="OpenStreetMap, izvadak za Hrvatsku (Geofabrik)",
        publisher="suradnici OpenStreetMapa",
        url=PBF_URL,
        license="ODbL 1.0",
        retrieved_at=file_date(pbf),
    )
    print(
        f"osm: {len(col.pois['category'])} POI, {len(col.parks['osm_id'])} parkova, "
        f"{len(col.addr['street'])} adresa, {len(col.lines['kind'])} linija"
    )


if __name__ == "__main__":
    run()
