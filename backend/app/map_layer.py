"""Karta Hrvatske: settlements coloured by precomputed indicators.

Nothing here runs the address analysis. Colours and the short card come from the
settlement profiles that also feed "Predloži mjesto" (ingest/settlement_profiles.py).

* `geometry(level)`: DGU settlement boundaries, simplified as a coverage (shared edges
  stay shared, so no gaps), in a compact delta-encoded JSON that the browser turns
  into GeoJSON. "overview" (300 m, ~0.3 MB gzip) is for the whole country; "detail"
  (80 m) is loaded only when the map is zoomed in.
* `table()`: one row per profiled settlement with the values the map colours by.
* `point(lat, lon)`: what a click hits: a settlement, the sea or a place outside
  Croatia, and whether the point is in the populated part of the settlement.
"""

from __future__ import annotations

import gzip
import json
import math
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Literal

import numpy as np
import pyarrow.parquet as pq
import shapely
from pydantic import BaseModel
from pyproj import Transformer
from shapely import STRtree
from shapely.geometry import Point

from analysis import score
from analysis.environment import (
    WORLDCOVER_WATER,
    _dataset,
    _worldcover_path,
    air_category,
    flood_category,
)
from app.config import get_settings
from app.finder import SCORED, profiles
from app.geo import in_bbox, to_htrs, to_htrs_arrays
from app.geocode import get_geocoder
from app.profiles import weights as profile_weights
from app.sources import retrieved_at

Level = Literal["overview", "detail"]
# Simplification tolerance (metres, EPSG:3765) and coordinate step (degrees) per level.
LEVELS: dict[str, tuple[float, float]] = {"overview": (300.0, 1e-3), "detail": (80.0, 1e-4)}
# A point counts as being in the populated part of a settlement when a house number
# (DGU or OpenStreetMap address) lies in the same or a neighbouring cell of this size.
POPULATED_CELL_M = 150.0
# A click this close to a settlement boundary still belongs to it (simplified outlines).
NEAR_BOUNDARY_M = 300.0
MAP_PROFILES = ("opci", "obitelj", "umirovljenik", "student", "rad-od-kuce")
AIR_ORDER = ["vrlo niska", "niska", "umjerena", "visoka"]

_FROM_HTRS = Transformer.from_crs("EPSG:3765", "EPSG:4326", always_xy=True)


# --- Geometry ----------------------------------------------------------------------------


@dataclass(frozen=True)
class Settlements:
    codes: list[str]
    names: list[str]
    municipalities: list[str]
    county_of: list[str]
    geoms: np.ndarray  # shapely geometries, EPSG:3765
    tree: STRtree
    centre: dict[str, tuple[float, float]]  # code -> (lon, lat)
    population: dict[str, int]


@lru_cache
def settlements() -> Settlements | None:
    d = get_settings().processed_dir
    path = d / "admin_units.parquet"
    if not path.exists():
        return None
    t = pq.read_table(path).to_pydict()
    county_name = {
        t["code"][i]: t["name"][i] for i in range(len(t["code"])) if t["level"][i] == "county"
    }
    county_of_jls = {
        t["code"][i]: county_name.get(t["parent_code"][i], "")
        for i in range(len(t["code"]))
        if t["level"][i] == "municipality"
    }
    idx = [i for i, level in enumerate(t["level"]) if level == "settlement"]
    geoms = shapely.from_wkb([t["geometry"][i] for i in idx])
    centre: dict[str, tuple[float, float]] = {}
    if (d / "settlements.parquet").exists():
        s = pq.read_table(d / "settlements.parquet", columns=["code", "lon", "lat"]).to_pydict()
        centre = {
            str(c): (float(x), float(y))
            for c, x, y in zip(s["code"], s["lon"], s["lat"], strict=True)
        }
    population: dict[str, int] = {}
    if (d / "settlement_population.parquet").exists():
        p = pq.read_table(d / "settlement_population.parquet").to_pydict()
        population = {
            str(c): int(n) for c, n in zip(p["settlement_code"], p["population"], strict=True)
        }
    return Settlements(
        codes=[str(t["code"][i]) for i in idx],
        names=[str(t["name"][i]) for i in idx],
        municipalities=[str(t["parent_name"][i]) for i in idx],
        county_of=[county_of_jls.get(str(t["parent_code"][i]), "") for i in idx],
        geoms=geoms,
        tree=STRtree(geoms),
        centre=centre,
        population=population,
    )


def encode_rings(geom: shapely.Geometry, step: float) -> list[list[list[int]]]:
    """Polygon or MultiPolygon (lon/lat) -> polygons -> rings of delta-encoded integers.

    Each ring is [x0, y0, dx1, dy1, ...] in units of `step` degrees; repeated points
    after rounding are dropped and rings with fewer than four points are left out.
    """
    out: list[list[list[int]]] = []
    for poly in getattr(geom, "geoms", [geom]):
        if poly.is_empty or poly.geom_type != "Polygon":
            continue
        rings: list[list[int]] = []
        for ring in [poly.exterior, *poly.interiors]:
            a = np.round(np.asarray(ring.coords)[:, :2] / step).astype(np.int64)
            keep = np.r_[True, np.any(np.diff(a, axis=0) != 0, axis=1)]
            a = a[keep]
            if len(a) < 4:
                continue
            rings.append(np.vstack([a[:1], np.diff(a, axis=0)]).ravel().tolist())
        if rings:
            out.append(rings)
    return out


@lru_cache(maxsize=2)
def geometry(level: Level) -> bytes:
    """Gzipped JSON: {"step": s, "features": [[id, polygons], ...]}; id = settlement code."""
    data = settlements()
    features: list[list[Any]] = []
    tolerance, step = LEVELS[level]
    if data is not None:
        simple = shapely.coverage_simplify(data.geoms, tolerance)

        def to_wgs84(xy: np.ndarray) -> np.ndarray:
            lon, lat = _FROM_HTRS.transform(xy[:, 0], xy[:, 1])
            return np.column_stack([lon, lat])

        wgs = shapely.transform(simple, to_wgs84)
        for code, geom in zip(data.codes, wgs, strict=True):
            polygons = encode_rings(geom, step)
            if polygons:
                features.append([int(code), polygons])
    body = json.dumps({"step": step, "features": features}, separators=(",", ":"))
    return gzip.compress(body.encode("utf-8"), compresslevel=9)


# --- Table of indicators ----------------------------------------------------------------


class MapRow(BaseModel):
    id: int
    code: str
    name: str
    municipality: str
    county: str
    population: int | None
    lat: float
    lon: float
    air: str | None
    pm25: float | None
    flood: str | None
    tree: float | None
    needs: int | None
    departures: float | None
    stops: bool
    scores: dict[str, int | None]


class LayerSource(BaseModel):
    title: str
    retrieved_at: str | None


class MapTable(BaseModel):
    rows: list[MapRow]
    profiles_date: str | None
    sources: dict[str, list[LayerSource]]


LAYER_SOURCES: dict[str, list[str]] = {
    "score": ["eea_pm25", "jrc_flood", "worldcover", "osm", "gtfs_zet", "dzs_popis"],
    "air": ["eea_pm25", "eea_no2"],
    "flood": ["jrc_flood"],
    "needs": ["osm", "mzom_vrtici", "mzom_skole", "hzzo_doctor", "hzzo_ljekarne"],
    "transit": ["gtfs_zet", "gtfs_hzpp", "gtfs_sibenik", "autotrolej", "osm"],
}
SOURCE_SHORT: dict[str, str] = {
    "eea_pm25": "EEA, karta PM2,5 za 2024.",
    "eea_no2": "EEA, karta NO2 za 2024.",
    "jrc_flood": "JRC, karte riječnih poplava",
    "worldcover": "ESA WorldCover 2021.",
    "osm": "OpenStreetMap",
    "gtfs_zet": "ZET, vozni red",
    "gtfs_hzpp": "HŽPP, vozni red",
    "gtfs_sibenik": "Gradski parking Šibenik, vozni red",
    "autotrolej": "Autotrolej, vozni red",
    "dzs_popis": "DZS, Popis 2021.",
    "mzom_vrtici": "Registar dječjih vrtića",
    "mzom_skole": "Popis osnovnih škola",
    "hzzo_doctor": "HZZO, obiteljski liječnici",
    "hzzo_ljekarne": "HZZO, ljekarne",
}


def _num(x: Any) -> float | None:
    return None if x is None or (isinstance(x, float) and math.isnan(x)) else float(x)


@lru_cache
def table() -> MapTable:
    df = profiles()
    rows: list[MapRow] = []
    weights = {p: profile_weights(p) for p in MAP_PROFILES}
    for rec in df.to_dict("records") if not df.empty else []:
        subs = {c: _num(rec.get(f"score_{c}")) for c in SCORED}
        scores: dict[str, int | None] = {}
        for p, w in weights.items():
            s = score.weighted(subs, {k: v for k, v in w.items() if k in SCORED})
            scores[p] = None if s is None else int(s)
        router_ok = bool(rec.get("router_ok", True))
        needs = _num(rec.get("needs_15min"))
        rows.append(
            MapRow(
                id=int(rec["code"]),
                code=str(rec["code"]),
                name=str(rec["name"]),
                municipality=str(rec["municipality"]),
                county=str(rec["county"]),
                population=None if _num(rec.get("population")) is None else int(rec["population"]),
                lat=round(float(rec["lat"]), 6),
                lon=round(float(rec["lon"]), 6),
                air=rec["air_band"] if rec.get("air_band") in AIR_ORDER else None,
                pm25=_num(rec.get("pm25")),
                flood=rec["flood_status"]
                if rec.get("flood_status") in ("good", "warning", "bad")
                else None,
                tree=_num(rec.get("tree_share")),
                needs=None if needs is None or not router_ok else int(needs),
                departures=_num(rec.get("max_departures")) if router_ok else None,
                stops=bool(rec.get("has_stops")) and router_ok,
                scores=scores,
            )
        )
    sources = {
        layer: [LayerSource(title=SOURCE_SHORT[s], retrieved_at=retrieved_at(s)) for s in ids]
        for layer, ids in LAYER_SOURCES.items()
    }
    return MapTable(
        rows=rows,
        profiles_date=retrieved_at("settlement_profiles"),
        sources=sources,
    )


@lru_cache
def profiled_codes() -> frozenset[str]:
    return frozenset(r.code for r in table().rows)


class MapColumns(BaseModel):
    """The table by columns: element i of every list belongs to settlement i.

    About 40 % smaller than one object per row once compressed. The settlement code is
    `id` written with six digits; centres are rounded to 4 decimals (about 10 m).
    """

    id: list[int]
    name: list[str]
    municipality: list[str]
    county: list[str]
    population: list[int | None]
    lat: list[float]
    lon: list[float]
    air: list[str | None]
    pm25: list[float | None]
    flood: list[str | None]
    tree: list[float | None]
    needs: list[int | None]
    departures: list[float | None]
    stops: list[bool]
    scores: dict[str, list[int | None]]
    profiles_date: str | None
    sources: dict[str, list[LayerSource]]


def columns() -> MapColumns:
    t = table()
    rows = t.rows
    return MapColumns(
        id=[r.id for r in rows],
        name=[r.name for r in rows],
        municipality=[r.municipality for r in rows],
        county=[r.county for r in rows],
        population=[r.population for r in rows],
        lat=[round(r.lat, 4) for r in rows],
        lon=[round(r.lon, 4) for r in rows],
        air=[r.air for r in rows],
        pm25=[r.pm25 for r in rows],
        flood=[r.flood for r in rows],
        tree=[r.tree for r in rows],
        needs=[r.needs for r in rows],
        departures=[r.departures for r in rows],
        stops=[r.stops for r in rows],
        scores={p: [r.scores.get(p) for r in rows] for p in MAP_PROFILES},
        profiles_date=t.profiles_date,
        sources=t.sources,
    )


@lru_cache
def table_json() -> bytes:
    return gzip.compress(columns().model_dump_json().encode("utf-8"), compresslevel=9)


# --- What a click hits -----------------------------------------------------------------


class PointTag(BaseModel):
    id: str
    title: str
    text: str
    status: str


class MapPoint(BaseModel):
    kind: Literal["settlement", "sea", "outside"]
    message: str | None = None
    id: int | None = None
    code: str | None = None
    name: str | None = None
    municipality: str | None = None
    county: str | None = None
    population: int | None = None
    profiled: bool = False
    populated: bool = True
    centre_lat: float | None = None
    centre_lon: float | None = None
    centre_km: float | None = None
    at_point: list[PointTag] = []


SEA_MESSAGE = "Odaberite točku na kopnu."
OUTSIDE_MESSAGE = "Podaci su dostupni samo za Hrvatsku."


@lru_cache
def address_cells() -> np.ndarray:
    """Sorted keys of the cells that contain at least one house number."""
    geocoder = get_geocoder()
    if not geocoder.lon:
        return np.array([], dtype=np.int64)
    x, y = to_htrs_arrays(
        np.asarray(geocoder.lon, dtype=np.float64), np.asarray(geocoder.lat, dtype=np.float64)
    )
    keys = _cell_keys(x, y)
    return np.unique(keys)


def _cell_keys(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    cx = np.floor(x / POPULATED_CELL_M).astype(np.int64)
    cy = np.floor(y / POPULATED_CELL_M).astype(np.int64)
    return cx * 1_000_000 + cy


def is_populated(lon: float, lat: float) -> bool:
    cells = address_cells()
    if cells.size == 0:
        return True  # unknown: do not claim the point is outside the populated part
    x, y = to_htrs(lon, lat)
    xs = np.array([x + dx * POPULATED_CELL_M for dx in (-1, 0, 1) for _ in (-1, 0, 1)])
    ys = np.array([y + dy * POPULATED_CELL_M for _ in (-1, 0, 1) for dy in (-1, 0, 1)])
    keys = _cell_keys(xs, ys)
    pos = np.searchsorted(cells, keys)
    pos = np.minimum(pos, cells.size - 1)
    return bool(np.any(cells[pos] == keys))


def landcover_at(lon: float, lat: float) -> int | None:
    """ESA WorldCover class at the point; None when the tile is not available."""
    ds = _dataset(_worldcover_path(lon, lat))
    if ds is None:
        return None
    row, col = ds.index(lon, lat)
    if not (0 <= row < ds.height and 0 <= col < ds.width):
        return None
    value = ds.read(1, window=((row, row + 1), (col, col + 1)))
    return int(value[0, 0])


def _at_point(lon: float, lat: float) -> list[PointTag]:
    tags: list[PointTag] = []
    flood = flood_category(lon, lat)
    if flood.status != "no_data":
        tags.append(PointTag(id="flood", title="Poplave", text=flood.headline, status=flood.status))
    air = air_category(lon, lat)
    if air.status != "no_data":
        tags.append(
            PointTag(id="air", title="Kvaliteta zraka", text=air.status_label, status=air.status)
        )
    return tags


def point(lat: float, lon: float) -> MapPoint:
    if not in_bbox(lon, lat):
        return MapPoint(kind="outside", message=OUTSIDE_MESSAGE)
    data = settlements()
    if data is None:
        return MapPoint(kind="outside", message=OUTSIDE_MESSAGE)
    x, y = to_htrs(lon, lat)
    p = Point(x, y)
    hits = data.tree.query(p, predicate="within")
    if len(hits) == 0:
        cover = landcover_at(lon, lat)
        if cover is None or cover == 0 or cover in WORLDCOVER_WATER:
            return MapPoint(kind="sea", message=SEA_MESSAGE)
        near = data.tree.query(p, predicate="dwithin", distance=NEAR_BOUNDARY_M)
        if len(near) == 0:
            return MapPoint(kind="outside", message=OUTSIDE_MESSAGE)
        hits = near
    i = int(hits[0])
    code = data.codes[i]
    profiled = code in profiled_codes()
    centre = data.centre.get(code)
    centre_km: float | None = None
    if centre is not None:
        cx, cy = to_htrs(*centre)
        centre_km = round(math.hypot(cx - x, cy - y) / 1000.0, 1)
    populated = is_populated(lon, lat)
    return MapPoint(
        kind="settlement",
        id=int(code),
        code=code,
        name=data.names[i],
        municipality=data.municipalities[i],
        county=data.county_of[i],
        population=data.population.get(code),
        profiled=profiled,
        populated=populated,
        centre_lat=None if centre is None else round(centre[1], 6),
        centre_lon=None if centre is None else round(centre[0], 6),
        centre_km=centre_km,
        at_point=[] if populated else _at_point(lon, lat),
    )


def warm() -> None:
    settlements()
    geometry("overview")
    table_json()
    geometry("detail")
    address_cells()
