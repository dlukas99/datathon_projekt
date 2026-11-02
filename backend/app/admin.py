"""Settlement, municipality (JLS) and county for a point, from DGU administrative units."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

import pyarrow.parquet as pq
import shapely
from shapely import STRtree
from shapely.geometry import Point
from shapely.geometry.base import BaseGeometry

from app.config import get_settings
from app.geo import to_htrs


@dataclass(frozen=True)
class AdminPlace:
    settlement: str
    settlement_code: str
    municipality: str
    county: str


class AdminIndex:
    def __init__(
        self,
        names: list[str],
        codes: list[str],
        parents: list[str],
        geoms: list[BaseGeometry],
        county_of_jls: dict[str, str],
    ) -> None:
        self.names = names
        self.codes = codes
        self.parents = parents
        self.geoms = geoms
        self.tree = STRtree(geoms)
        self.county_of_jls = county_of_jls

    def lookup(self, lon: float, lat: float) -> AdminPlace | None:
        x, y = to_htrs(lon, lat)
        hits = self.tree.query(Point(x, y), predicate="within")
        if len(hits) == 0:
            hits = self.tree.query(Point(x, y), predicate="dwithin", distance=200.0)
            if len(hits) == 0:
                return None
        i = int(hits[0])
        jls_code, jls_name = self.parents[i].split("|", 1)
        return AdminPlace(
            settlement=self.names[i],
            settlement_code=self.codes[i],
            municipality=jls_name,
            county=self.county_of_jls.get(jls_code, ""),
        )


@lru_cache
def get_admin() -> AdminIndex | None:
    path = get_settings().processed_dir / "admin_units.parquet"
    if not path.exists():
        return None
    t = pq.read_table(path).to_pydict()
    names, codes, parents, geoms = [], [], [], []
    county_name = {
        t["code"][i]: t["name"][i] for i in range(len(t["code"])) if t["level"][i] == "county"
    }
    county_of_jls = {
        t["code"][i]: county_name.get(t["parent_code"][i], "")
        for i in range(len(t["code"]))
        if t["level"][i] == "municipality"
    }
    for i in range(len(t["code"])):
        if t["level"][i] != "settlement":
            continue
        names.append(t["name"][i])
        codes.append(t["code"][i])
        parents.append(f"{t['parent_code'][i]}|{t['parent_name'][i]}")
        geoms.append(shapely.from_wkb(t["geometry"][i]))
    return AdminIndex(names, codes, parents, geoms, county_of_jls)
