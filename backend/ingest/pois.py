"""Merge official registries, OpenStreetMap and timetabled stops into pois.parquet.

Rules (docs/METODOLOGIJA.md):
  * official registries come first; OSM objects are added only when no official
    object of the same category lies within OSM_DEDUP_M;
  * family doctors and paediatricians come only from HZZO (OSM `amenity=doctors`
    mixes in specialists and private practices);
  * OSM schools are limited to primary schools by name;
  * stops with a timetable (GTFS, Autotrolej) replace OSM stops within STOP_DEDUP_M.

Output columns: category, name, lon, lat, source, detail
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from app.geo import to_htrs_arrays
from app.geocode import normalize
from ingest.common import processed_dir

OSM_DEDUP_M = 100.0
STOP_DEDUP_M = 60.0
OFFICIAL_ONLY = {"doctor", "pediatrician"}
PRIMARY_SCHOOL_PREFIXES = ("osnovna skola", "os ", "podrucna skola", "ps ")


def _xy(df: pd.DataFrame) -> np.ndarray:
    x, y = to_htrs_arrays(df["lon"].to_numpy(float), df["lat"].to_numpy(float))
    return np.column_stack([x, y])


def _far_from(candidates: pd.DataFrame, reference: pd.DataFrame, radius: float) -> pd.DataFrame:
    """Rows of `candidates` farther than `radius` metres from every row of `reference`."""
    if reference.empty or candidates.empty:
        return candidates
    ref = _xy(reference)
    cand = _xy(candidates)
    keep = np.ones(len(cand), dtype=bool)
    # Grid bucketing keeps this linear for tens of thousands of points.
    cell = radius
    buckets: dict[tuple[int, int], list[int]] = {}
    for i, (x, y) in enumerate(ref):
        buckets.setdefault((int(x // cell), int(y // cell)), []).append(i)
    for j, (x, y) in enumerate(cand):
        cx, cy = int(x // cell), int(y // cell)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for i in buckets.get((cx + dx, cy + dy), []):
                    if (ref[i, 0] - x) ** 2 + (ref[i, 1] - y) ** 2 <= radius * radius:
                        keep[j] = False
                        break
                if not keep[j]:
                    break
            if not keep[j]:
                break
    return candidates[keep]


def _is_primary_school(name: str) -> bool:
    n = normalize(name) + " "
    return n.startswith(PRIMARY_SCHOOL_PREFIXES) or "osnovna skola" in n


def build() -> pd.DataFrame:
    d = processed_dir()
    osm = pd.read_parquet(d / "osm_pois.parquet").rename(columns={"extra": "detail"})
    osm["source"] = "osm"
    reg = pd.read_parquet(d / "registry_pois.parquet")
    reg = reg.drop_duplicates(["category", "lon", "lat"])
    cols = ["category", "name", "lon", "lat", "source", "detail"]
    frames = [reg[cols]]

    for category in ("kindergarten", "school", "pharmacy"):
        extra = osm[osm["category"] == category]
        if category == "school":
            extra = extra[extra["name"].map(_is_primary_school)]
        official = reg[reg["category"] == category]
        frames.append(_far_from(extra, official, OSM_DEDUP_M)[cols])

    for category in ("grocery", "playground"):
        frames.append(osm[osm["category"] == category][cols])

    recycling_path = d / "recycling.parquet"  # municipal datasets + OSM, ingest/recycling.py
    if recycling_path.exists():
        frames.append(pd.read_parquet(recycling_path)[cols])
    else:
        frames.append(osm[osm["category"] == "recycling"][cols])

    transit_path = d / "transit_stops.parquet"
    timetabled = pd.read_parquet(transit_path) if transit_path.exists() else pd.DataFrame()
    if not timetabled.empty:
        tt = pd.DataFrame(
            {
                "category": "stop",
                "name": timetabled["name"],
                "lon": timetabled["lon"],
                "lat": timetabled["lat"],
                "source": timetabled["source"],
                "detail": timetabled["mode"]
                + "|"
                + timetabled["departures_per_hour"].astype(str)
                + "|"
                + timetabled["service_date"],
            }
        )
        frames.append(tt)
    osm_stops = osm[osm["category"] == "stop"]
    if not timetabled.empty:
        osm_stops = _far_from(osm_stops, timetabled, STOP_DEDUP_M)
    frames.append(osm_stops[cols])

    out = pd.concat(frames, ignore_index=True)
    out = out[~out["category"].isin(OFFICIAL_ONLY) | out["source"].str.startswith("hzzo")]
    out["name"] = out["name"].fillna("")
    out["detail"] = out["detail"].fillna("")
    return out


def run() -> None:
    out = build()
    pq.write_table(
        pa.Table.from_pandas(out, preserve_index=False), processed_dir() / "pois.parquet"
    )
    print(out.groupby(["category", "source"]).size().to_string())


if __name__ == "__main__":
    run()
