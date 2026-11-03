"""Processed layers loaded into memory once, at application start."""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq
import shapely
from numpy.typing import NDArray
from shapely import STRtree
from shapely.geometry.base import BaseGeometry

from app.config import get_settings
from app.geo import _TO_HTRS, to_htrs_arrays


@dataclass
class PointLayer:
    """Points of one category with coordinates in WGS84 and HTRS96/TM."""

    names: list[str]
    details: list[str]
    sources: list[str]
    lon: NDArray[np.float64]
    lat: NDArray[np.float64]
    x: NDArray[np.float64]
    y: NDArray[np.float64]

    def __len__(self) -> int:
        return len(self.names)

    def nearest(self, x: float, y: float, radius: float, k_min: int, k_max: int) -> list[int]:
        """Indices within `radius` metres (at most k_max), but at least the k_min nearest."""
        if len(self) == 0:
            return []
        d2 = (self.x - x) ** 2 + (self.y - y) ** 2
        order = np.argsort(d2)
        within = int(np.searchsorted(d2[order], radius * radius))
        take = min(max(within, k_min), k_max, len(order))
        return [int(i) for i in order[:take]]

    def distance(self, i: int, x: float, y: float) -> float:
        return float(np.hypot(self.x[i] - x, self.y[i] - y))


@dataclass
class PolygonLayer:
    names: list[str]
    geoms: list[BaseGeometry]  # in EPSG:3765
    tree: STRtree


@dataclass
class LineLayer:
    kinds: list[str]
    refs: list[str]
    geoms: list[BaseGeometry]  # in EPSG:3765
    tree: STRtree


def _empty_points() -> PointLayer:
    e = np.zeros(0, dtype=np.float64)
    return PointLayer([], [], [], e, e, e, e)


def load_points(path: Path) -> dict[str, PointLayer]:
    """Read pois.parquet (category, name, lon, lat, source, detail) grouped by category."""
    if not path.exists():
        return {}
    table = pq.read_table(path).to_pydict()
    cats: dict[str, list[int]] = {}
    for i, cat in enumerate(table["category"]):
        cats.setdefault(cat, []).append(i)
    layers: dict[str, PointLayer] = {}
    for cat, idx in cats.items():
        lon = np.asarray([table["lon"][i] for i in idx], dtype=np.float64)
        lat = np.asarray([table["lat"][i] for i in idx], dtype=np.float64)
        x, y = to_htrs_arrays(lon, lat)
        layers[cat] = PointLayer(
            names=[table["name"][i] or "" for i in idx],
            details=[table["detail"][i] or "" for i in idx],
            sources=[table["source"][i] for i in idx],
            lon=lon,
            lat=lat,
            x=x,
            y=y,
        )
    return layers


def _project_all(wkbs: list[bytes]) -> list[BaseGeometry]:
    """WKB in EPSG:4326 -> geometries in EPSG:3765, vectorised."""

    def to_htrs(x: NDArray[np.float64], y: NDArray[np.float64]) -> tuple[Any, Any]:
        return _TO_HTRS.transform(x, y)

    projected = shapely.transform(shapely.from_wkb(wkbs), to_htrs, interleaved=False)
    return list(projected)


def load_polygons(path: Path) -> PolygonLayer | None:
    if not path.exists():
        return None
    table = pq.read_table(path).to_pydict()
    geoms = _project_all(table["geometry"])
    return PolygonLayer(names=list(table["name"]), geoms=geoms, tree=STRtree(geoms))


def load_lines(path: Path) -> LineLayer | None:
    if not path.exists():
        return None
    table = pq.read_table(path).to_pydict()
    geoms = _project_all(table["geometry"])
    return LineLayer(
        kinds=list(table["kind"]), refs=list(table["ref"]), geoms=geoms, tree=STRtree(geoms)
    )


@dataclass
class BurntLayer:
    dates: list[str]
    areas: list[float]
    communes: list[str]
    geoms: list[BaseGeometry]  # in EPSG:3765
    tree: STRtree


def load_burnt(path: Path) -> BurntLayer | None:
    if not path.exists():
        return None
    table = pq.read_table(path).to_pydict()
    geoms = _project_all(table["geometry"])
    return BurntLayer(
        dates=list(table["fire_date"]),
        areas=[float(a) for a in table["area_ha"]],
        communes=list(table["commune"]),
        geoms=geoms,
        tree=STRtree(geoms),
    )


@dataclass
class Layers:
    points: dict[str, PointLayer]
    parks: PolygonLayer | None
    noise_lines: LineLayer | None
    burnt: BurntLayer | None = None

    def category(self, name: str) -> PointLayer:
        return self.points.get(name) or _empty_points()


@lru_cache
def get_layers() -> Layers:
    d = get_settings().processed_dir
    return Layers(
        points=load_points(d / "pois.parquet"),
        parks=load_polygons(d / "osm_parks.parquet"),
        noise_lines=load_lines(d / "osm_noise_lines.parquet"),
        burnt=load_burnt(d / "effis_burnt.parquet"),
    )
