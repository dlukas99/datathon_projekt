"""Coordinate helpers. Distances are computed in HTRS96/TM (EPSG:3765), metres."""

from __future__ import annotations

import numpy as np
from numpy.typing import NDArray
from pyproj import Transformer

_TO_HTRS = Transformer.from_crs("EPSG:4326", "EPSG:3765", always_xy=True)
_FROM_HTRS = Transformer.from_crs("EPSG:3765", "EPSG:4326", always_xy=True)

# Rough bounding box of Croatia (lon/lat), used to reject points far outside.
CROATIA_BBOX = (13.2, 42.2, 19.6, 46.7)


def to_htrs(lon: float, lat: float) -> tuple[float, float]:
    x, y = _TO_HTRS.transform(lon, lat)
    return float(x), float(y)


def to_htrs_arrays(
    lon: NDArray[np.float64], lat: NDArray[np.float64]
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    x, y = _TO_HTRS.transform(lon, lat)
    return np.asarray(x, dtype=np.float64), np.asarray(y, dtype=np.float64)


def to_wgs84(x: float, y: float) -> tuple[float, float]:
    lon, lat = _FROM_HTRS.transform(x, y)
    return float(lon), float(lat)


def in_bbox(lon: float, lat: float) -> bool:
    w, s, e, n = CROATIA_BBOX
    return w <= lon <= e and s <= lat <= n
