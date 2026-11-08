"""Distance from major roads for whole settlements, over every DGU address.

One point (the settlement centre) does not describe a town: the centre of Split lies in
the pedestrian old town, while most of its people live along busy roads, and the centre
of almost every village lies on the road through it. So for the map and "Predloži
mjesto" every DGU address in the settlement gets the same band as an address report
(analysis/environment.py: up to 300 m, 300–500 m, beyond 500 m from a motorway,
expressway, state road or main city street), and the settlement gets the shares of its
addresses in each band and the mean of their sub-scores. Settlements without addresses
keep the value at their centre.

Output: data/processed/settlement_traffic.parquet
  code, addresses, near_share, edge_share, far_share, score_noise
"""

from __future__ import annotations

import json

import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from shapely import STRtree, points

from analysis.environment import TRAFFIC_BANDS, is_traffic_road
from analysis.score import TRAFFIC_POINTS
from app.geo import to_htrs_arrays
from app.layers import load_lines
from ingest.common import processed_dir, record_source

NEAR_M = float(TRAFFIC_BANDS[0][0] or 300.0)
EDGE_M = float(TRAFFIC_BANDS[1][0] or 500.0)


def address_distances(lon: np.ndarray, lat: np.ndarray) -> np.ndarray:
    """Straight-line distance in metres from each point to the nearest major road
    (capped at EDGE_M + 1: only the band matters beyond 500 m)."""
    lines = load_lines(processed_dir() / "osm_noise_lines.parquet")
    if lines is None:
        raise RuntimeError("Nema osm_noise_lines.parquet: pokrenite `make data` (OSM).")
    roads = [
        g
        for g, k, r in zip(lines.geoms, lines.kinds, lines.refs, strict=True)
        if k != "rail" and is_traffic_road(k, r)
    ]
    tree = STRtree(roads)
    x, y = to_htrs_arrays(lon.astype(np.float64), lat.astype(np.float64))
    pts = points(x, y)
    cap = EDGE_M + 1.0
    dist = np.full(len(pts), cap)
    idx, d = tree.query_nearest(pts, max_distance=cap, return_distance=True, all_matches=False)
    # query_nearest returns (input index, tree index) pairs; keep the shortest per point.
    np.minimum.at(dist, idx[0], d)
    return dist


def run() -> None:
    d = processed_dir()
    addresses = pd.read_parquet(d / "addresses.parquet", columns=["settlement_code", "lon", "lat"])
    addresses = addresses.dropna(subset=["settlement_code"]).assign(real=True)
    # Settlements without any address are measured at their centre instead.
    centres = pd.read_parquet(d / "settlements.parquet", columns=["code", "lon", "lat"])
    centres = centres[~centres["code"].isin(set(addresses["settlement_code"]))]
    addresses = pd.concat(
        [addresses, centres.rename(columns={"code": "settlement_code"}).assign(real=False)],
        ignore_index=True,
    )
    dist = address_distances(addresses["lon"].to_numpy(), addresses["lat"].to_numpy())
    near = dist <= NEAR_M
    edge = (dist > NEAR_M) & (dist <= EDGE_M)
    far = dist > EDGE_M
    points_by_band = np.where(
        near,
        TRAFFIC_POINTS["Blizu prometnice"],
        np.where(edge, TRAFFIC_POINTS["Rub zone prometa"], TRAFFIC_POINTS["Podalje od prometnica"]),
    )
    frame = pd.DataFrame(
        {
            "code": addresses["settlement_code"].astype(str).to_numpy(),
            "near": near,
            "edge": edge,
            "far": far,
            "points": points_by_band,
            "real": addresses["real"].to_numpy(),
        }
    )
    grouped = frame.groupby("code")
    table = pd.DataFrame(
        {
            "addresses": grouped["real"].sum(),
            "near_share": grouped["near"].mean(),
            "edge_share": grouped["edge"].mean(),
            "far_share": grouped["far"].mean(),
            "score_noise": grouped["points"].mean().round(),
        }
    ).reset_index()
    pq.write_table(
        pa.Table.from_pandas(table, preserve_index=False), d / "settlement_traffic.parquet"
    )
    record_source(
        "settlement_traffic",
        title="Udaljenost adresa naselja od velikih prometnica, izračun aplikacije",
        publisher="izvedeno iz DGU adresa i OpenStreetMapa",
        url="",
        license="CC BY 4.0 (izvedeni podaci); ulazni izvori zadržavaju svoje licence",
        retrieved_at=pd.Timestamp.now(tz="UTC").isoformat(timespec="seconds"),
        notes=json.dumps({"settlements": len(table), "addresses": int(frame["real"].sum())}),
    )
    print(
        f"prometnice po adresama: {int(frame['real'].sum())} adresa u {len(table)} naselja, "
        f"blizu prometnice {near.mean():.0%}"
    )


if __name__ == "__main__":
    run()
