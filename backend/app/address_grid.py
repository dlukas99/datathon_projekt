"""How many house numbers (DGU addresses) lie within a radius of a point.

The satellite land cover often counts single village houses among gardens and trees as
nature, so the greenery card also says how many house numbers there are around. The
addresses are bucketed in square cells of CELL_M metres in HTRS96/TM, so a query reads
only the neighbouring cells (numpy only, about 40 MB for 1.7 million addresses).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import lru_cache

import numpy as np
import pyarrow.parquet as pq
from numpy.typing import NDArray

from app.config import get_settings
from app.geo import to_htrs, to_htrs_arrays

CELL_M = 300.0
_SPAN = 1 << 20  # cells per row in the key; HTRS96/TM coordinates fit comfortably


@dataclass(frozen=True)
class AddressGrid:
    keys: NDArray[np.int64]  # cell key of each address, sorted
    x: NDArray[np.float64]
    y: NDArray[np.float64]

    @classmethod
    def from_points(cls, x: NDArray[np.float64], y: NDArray[np.float64]) -> AddressGrid:
        keys = _key(np.floor(x / CELL_M).astype(np.int64), np.floor(y / CELL_M).astype(np.int64))
        order = np.argsort(keys, kind="stable")
        return cls(keys=keys[order], x=x[order], y=y[order])

    def count_within(self, lon: float, lat: float, radius_m: float) -> int:
        px, py = to_htrs(lon, lat)
        reach = math.ceil(radius_m / CELL_M)
        cx, cy = math.floor(px / CELL_M), math.floor(py / CELL_M)
        total = 0
        for dx in range(-reach, reach + 1):
            for dy in range(-reach, reach + 1):
                key = int(_key(np.int64(cx + dx), np.int64(cy + dy)))
                lo = int(np.searchsorted(self.keys, key, side="left"))
                hi = int(np.searchsorted(self.keys, key, side="right"))
                if hi > lo:
                    d = np.hypot(self.x[lo:hi] - px, self.y[lo:hi] - py)
                    total += int((d <= radius_m).sum())
        return total


def _key(ix: NDArray[np.int64] | np.int64, iy: NDArray[np.int64] | np.int64) -> NDArray[np.int64]:
    return np.asarray(ix * _SPAN + iy, dtype=np.int64)


@lru_cache
def get_address_grid() -> AddressGrid | None:
    path = get_settings().processed_dir / "addresses.parquet"
    if not path.exists():
        return None
    t = pq.read_table(path, columns=["lon", "lat"])
    lon = t.column("lon").to_numpy().astype(np.float64)
    lat = t.column("lat").to_numpy().astype(np.float64)
    x, y = to_htrs_arrays(lon, lat)
    return AddressGrid.from_points(x, y)


def addresses_within(lon: float, lat: float, radius_m: float) -> int | None:
    """Number of DGU house numbers within radius_m metres, or None without address data."""
    grid = get_address_grid()
    return None if grid is None else grid.count_within(lon, lat, radius_m)
