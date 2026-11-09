"""Public transport lines at each stop, from the route relations in the OSM extract.

Where operators publish no open timetable (Osijek, Split, Zadar, Pula, Dubrovnik,
Bjelovar …) the report can still say which lines stop nearby: "tram 1 and 2, bus 4
(GPP Osijek)". That is a fact mapped in OpenStreetMap, not a frequency, and it is shown
as such. Long-distance lines (Flixbus and other intercity routes) say nothing about
getting around town, so a route whose stops lie more than MAX_SPAN_KM apart is left out,
and so is a route with fewer than MIN_STOPS mapped stops (in the extract, intercity
routes are often only a few stops of a longer line).

Output: data/processed/osm_stop_lines.parquet, one row per stop node of a local route:
  lon, lat, mode (tram | trolleybus | bus), ref, operator
"""

from __future__ import annotations

import math
import re
from collections.abc import Iterable
from typing import Any

import osmium
import pyarrow as pa
import pyarrow.parquet as pq

from ingest.common import processed_dir, raw_dir

PBF_NAME = "croatia-latest.osm.pbf"
MODES = {"tram": "tram", "trolleybus": "trolleybus", "bus": "bus", "minibus": "bus"}
MAX_SPAN_KM = 30.0
MIN_STOPS = 5

Route = tuple[dict[str, str], list[int]]


def _km(a: tuple[float, float], b: tuple[float, float]) -> float:
    """Straight-line distance between two (lat, lon) points, equirectangular."""
    dy = (a[0] - b[0]) * 111.32
    dx = (a[1] - b[1]) * 111.32 * math.cos(math.radians((a[0] + b[0]) / 2))
    return math.hypot(dx, dy)


def local_routes(
    routes: Iterable[Route], locations: dict[int, tuple[float, float]]
) -> dict[str, list[Any]]:
    """Rows for the stops of local routes (see the module docstring for what is left out)."""
    rows: dict[str, list[Any]] = {"lon": [], "lat": [], "mode": [], "ref": [], "operator": []}
    for tags, nodes in routes:
        mode = MODES.get(tags.get("route", ""))
        ref = (tags.get("ref") or "").strip()
        points = list(dict.fromkeys(locations[n] for n in nodes if n in locations))
        if mode is None or not ref or len(points) < MIN_STOPS:
            continue
        span = max(_km(p, q) for p in points for q in (points[0], points[-1]))
        if span > MAX_SPAN_KM:
            continue
        operator = (tags.get("operator") or tags.get("network") or "").strip()
        operator = re.sub(r"^[a-z]{2}:", "", operator)  # "hr:Liburnija Zadar"
        for lat, lon in points:
            rows["lon"].append(lon)
            rows["lat"].append(lat)
            rows["mode"].append(mode)
            rows["ref"].append(ref)
            rows["operator"].append(operator)
    return rows


def _routes(pbf: str) -> list[Route]:
    out: list[Route] = []
    obj: Any
    processor = osmium.FileProcessor(pbf, osmium.osm.RELATION).with_filter(
        osmium.filter.KeyFilter("route")
    )
    for obj in processor:
        tags = {t.k: t.v for t in obj.tags}
        if tags.get("type") != "route" or tags.get("route") not in MODES:
            continue
        nodes = [
            m.ref
            for m in obj.members
            if m.type == "n" and (m.role == "" or m.role.startswith(("stop", "platform")))
        ]
        out.append((tags, nodes))
    return out


def _locations(pbf: str, ids: set[int]) -> dict[int, tuple[float, float]]:
    out: dict[int, tuple[float, float]] = {}
    obj: Any
    processor = osmium.FileProcessor(pbf, osmium.osm.NODE).with_filter(osmium.filter.IdFilter(ids))
    for obj in processor:
        if obj.location.valid():
            out[obj.id] = (obj.location.lat, obj.location.lon)
    return out


def run() -> None:
    pbf = str(raw_dir("osm") / PBF_NAME)
    routes = _routes(pbf)
    locations = _locations(pbf, {n for _, nodes in routes for n in nodes})
    rows = local_routes(routes, locations)
    pq.write_table(pa.table(rows), processed_dir() / "osm_stop_lines.parquet")
    print(f"linije javnog prijevoza (OSM): {len(routes)} relacija, {len(rows['ref'])} stajališta")


if __name__ == "__main__":
    run()
