"""Nature, tree shade and air for whole settlements, as medians over their addresses.

One point (the settlement centre) does not describe a settlement: the centre of a
village is its most built-up part, and a town is greener at its edges than on its main
square. So for the map and "Predloži mjesto" every settlement gets the median and the
interquartile range (25th to 75th percentile) over its DGU addresses of:

- land cover within 300 m (ESA WorldCover 2021): trees, nature (trees, shrubs,
  grassland, fields, wetland) and built-up land; the share of addresses in densely
  built-up (urban) areas; the median greenery sub-score (analysis/score.py);
- annual PM2.5 and NO2 (EEA 2024, 1 km) and the median air sub-score.

The median, not the mean: a few addresses next to a forest or a park would pull a
mean up, while the median is the value of a typical address. Settlements with more
than SAMPLE addresses use a fixed random sample of SAMPLE addresses (seed 2026), the
rest all of them; settlements without addresses use their centre.

Output: data/processed/settlement_landcover.parquet
"""

from __future__ import annotations

import json
import os
import time
from concurrent.futures import ProcessPoolExecutor
from typing import Any

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import shapely
from shapely import STRtree

from analysis.environment import (
    _BAND_ORDER,
    URBAN_BUILT_PCT,
    air_band,
    is_urban,
    read_air,
    read_landcover,
)
from analysis.score import AIR_POINTS, green_points
from app.geo import to_htrs_arrays
from ingest.common import processed_dir, record_source

SAMPLE = 100
SEED = 2026
QUANTILES = (0.25, 0.5, 0.75)


def sample_points(addresses: pd.DataFrame, centres: pd.DataFrame) -> pd.DataFrame:
    """All addresses of small settlements, a fixed sample of large ones, centres of the
    settlements without addresses."""
    rng = np.random.default_rng(SEED)
    parts = []
    for code, group in addresses.groupby("settlement_code", sort=True):
        if len(group) > SAMPLE:
            group = group.iloc[np.sort(rng.choice(len(group), SAMPLE, replace=False))]
        parts.append(group.assign(code=str(code), real=True))
    missing = centres[~centres["code"].isin(set(addresses["settlement_code"]))]
    parts.append(missing.assign(real=False))
    return pd.concat(parts, ignore_index=True)[["code", "lon", "lat", "real"]]


def park_distances(lon: np.ndarray, lat: np.ndarray) -> np.ndarray:
    """Straight-line distance in metres to the nearest OpenStreetMap park (NaN when none
    within 5 km)."""
    parks = pd.read_parquet(processed_dir() / "osm_parks.parquet", columns=["geometry"])
    geoms = shapely.from_wkb(parks["geometry"].to_numpy())
    coords = shapely.get_coordinates(geoms)
    x, y = to_htrs_arrays(coords[:, 0], coords[:, 1])
    geoms = shapely.set_coordinates(geoms, np.column_stack([x, y]))
    tree = STRtree(geoms)
    px, py = to_htrs_arrays(lon.astype(np.float64), lat.astype(np.float64))
    pts = shapely.points(px, py)
    dist = np.full(len(pts), np.nan)
    idx, d = tree.query_nearest(pts, max_distance=5000.0, return_distance=True)
    np.fmin.at(dist, idx[0], d)
    return dist


def _measure(chunk: list[tuple[float, float, float]]) -> list[tuple[float, ...]]:
    """Land cover and air at each (lon, lat, park distance); runs in a worker process."""
    nan = float("nan")
    out: list[tuple[float, ...]] = []
    for lon, lat, park in chunk:
        cover = read_landcover(lon, lat)
        if cover is None:
            tree = nature = built = urban = green = nan
        else:
            tree, nature, built = cover["tree"], cover["nature"], cover["built"]
            urban = 1.0 if is_urban(cover) else 0.0
            green = green_points(tree, nature, bool(urban), None if park != park else park)
        pm25 = read_air(lon, lat, "pm25")
        no2 = read_air(lon, lat, "no2")
        air = nan
        if pm25 is not None and no2 is not None:
            air = min(AIR_POINTS[air_band("pm25", pm25)[0]], AIR_POINTS[air_band("no2", no2)[0]])
        out.append(
            (
                tree,
                nature,
                built,
                urban,
                green,
                nan if pm25 is None else pm25,
                nan if no2 is None else no2,
                air,
            )
        )
    return out


COLUMNS = ("tree", "nature", "built", "urban", "green", "pm25", "no2", "air")


def summarise(frame: pd.DataFrame) -> pd.DataFrame:
    """Median and quartiles per settlement, and the settlement-level bands and scores."""
    g = frame.groupby("code")
    out = pd.DataFrame({"sampled": g["real"].sum().astype(int)})
    for col in ("tree", "nature", "built", "pm25", "no2"):
        q = g[col].quantile(np.array(QUANTILES)).unstack()
        out[f"{col}_p25"], out[f"{col}_med"], out[f"{col}_p75"] = q[0.25], q[0.5], q[0.75]
    out["urban_share"] = g["urban"].mean()
    out["score_green"] = g["green"].median().round()
    out["score_air"] = g["air"].median().round()

    def band(pm25: float, no2: float) -> str | None:
        if pd.isna(pm25) or pd.isna(no2):
            return None
        bands = [air_band("pm25", pm25)[0], air_band("no2", no2)[0]]
        return max(bands, key=_BAND_ORDER.index)

    out["air_band_med"] = [band(p, n) for p, n in zip(out["pm25_med"], out["no2_med"], strict=True)]
    return out.reset_index()


def run(workers: int | None = None) -> None:
    d = processed_dir()
    addresses = pd.read_parquet(d / "addresses.parquet", columns=["settlement_code", "lon", "lat"])
    addresses = addresses.dropna(subset=["settlement_code"])
    addresses["settlement_code"] = addresses["settlement_code"].astype(str)
    centres = pd.read_parquet(d / "settlements.parquet", columns=["code", "lon", "lat"])
    centres["code"] = centres["code"].astype(str)
    points = sample_points(addresses, centres)
    points["park"] = park_distances(points["lon"].to_numpy(), points["lat"].to_numpy())
    # Nearby points share raster blocks: sort them, then cut into chunks for the workers.
    order = np.lexsort((points["lat"].round(2), points["lon"].round(2)))
    points = points.iloc[order].reset_index(drop=True)
    rows = list(zip(points["lon"], points["lat"], points["park"], strict=True))
    size = 2000
    chunks = [rows[i : i + size] for i in range(0, len(rows), size)]
    start = time.monotonic()
    workers = workers or max(1, min(8, (os.cpu_count() or 2) - 1))
    with ProcessPoolExecutor(max_workers=workers) as pool:
        measured = [m for part in pool.map(_measure, chunks) for m in part]
    values = pd.DataFrame(measured, columns=list(COLUMNS))
    frame = pd.concat([points[["code", "real"]], values], axis=1)
    table = summarise(frame)
    pq.write_table(
        pa.Table.from_pandas(table, preserve_index=False), d / "settlement_landcover.parquet"
    )
    notes: dict[str, Any] = {
        "settlements": len(table),
        "points": len(frame),
        "addresses": int(frame["real"].sum()),
        "sample": SAMPLE,
        "seed": SEED,
        "urban_built_pct": URBAN_BUILT_PCT,
    }
    record_source(
        "settlement_landcover",
        title="Priroda, drveće i zrak po adresama naselja (medijan), izračun aplikacije",
        publisher="izvedeno iz DGU adresa, ESA WorldCovera, EEA karata zraka i OpenStreetMapa",
        url="",
        license="CC BY 4.0 (izvedeni podaci); ulazni izvori zadržavaju svoje licence",
        retrieved_at=pd.Timestamp.now(tz="UTC").isoformat(timespec="seconds"),
        notes=json.dumps(notes),
    )
    print(
        f"priroda i zrak po adresama: {len(frame)} točaka u {len(table)} naselja za "
        f"{time.monotonic() - start:.0f} s; gradskih adresa {frame['urban'].mean():.0%}"
    )


if __name__ == "__main__":
    run()
