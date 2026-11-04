"""Settlement centres: the OSM `place=*` node instead of a point inside the polygon.

Mappers put the place node on the real centre (main square, church). A node is
used only when its name equals the DGU settlement name and it lies inside that
settlement's polygon; otherwise the DGU representative point stays.

Updates data/processed/settlements.parquet (lon, lat, center_source).
"""

from __future__ import annotations

from typing import Any

import osmium
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import shapely
from shapely import STRtree

from app.geo import to_htrs
from app.geocode import normalize
from ingest.common import processed_dir, raw_dir

PLACES = {"city", "town", "village", "hamlet", "suburb", "isolated_dwelling", "locality"}


def place_nodes() -> list[tuple[str, float, float]]:
    pbf = raw_dir("osm") / "croatia-latest.osm.pbf"
    out = []
    processor = osmium.FileProcessor(str(pbf)).with_filter(osmium.filter.KeyFilter("place"))
    obj: Any
    for obj in processor:
        if not obj.is_node() or obj.tags.get("place") not in PLACES:
            continue
        name = obj.tags.get("name:hr") or obj.tags.get("name")
        if name and obj.location.valid():
            out.append((name, obj.location.lon, obj.location.lat))
    return out


def run() -> None:
    d = processed_dir()
    units = pq.read_table(d / "admin_units.parquet").to_pandas()
    units = units[units["level"] == "settlement"].reset_index(drop=True)
    geoms = shapely.from_wkb(units["geometry"].to_numpy())
    tree = STRtree(geoms)
    by_code: dict[str, tuple[float, float]] = {}
    for name, lon, lat in place_nodes():
        x, y = to_htrs(lon, lat)
        for i in tree.query(shapely.Point(x, y), predicate="within"):
            row = units.iloc[int(i)]
            if normalize(row["name"]) == normalize(name) and row["code"] not in by_code:
                by_code[row["code"]] = (round(lon, 6), round(lat, 6))
    settlements = pd.read_parquet(d / "settlements.parquet")
    matched = settlements["code"].map(by_code)
    has = matched.notna()
    settlements.loc[has, "lon"] = [p[0] for p in matched[has]]
    settlements.loc[has, "lat"] = [p[1] for p in matched[has]]
    settlements["center_source"] = ["osm_place" if h else "dgu_au" for h in has]
    pq.write_table(
        pa.Table.from_pandas(settlements, preserve_index=False), d / "settlements.parquet"
    )
    print(f"središta: {int(has.sum())} od {len(settlements)} naselja iz OSM place čvorova")


if __name__ == "__main__":
    run()
