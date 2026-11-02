"""Environmental categories read from rasters and vector layers at a point."""

from __future__ import annotations

import atexit
import math
import threading
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import rasterio
from numpy.typing import NDArray
from rasterio.warp import transform as warp_transform
from rasterio.windows import Window
from shapely.geometry import Point

from analysis.status import label
from app import fmt
from app.config import get_settings
from app.geo import to_htrs
from app.layers import Layers
from app.models import Category, Link, Place, Status, Value
from app.sources import retrieved_at

# --- Thresholds (sources in docs/METODOLOGIJA.md) -----------------------------------------
WHO_2021 = {"pm25": 5.0, "no2": 10.0}  # WHO Global Air Quality Guidelines 2021, annual
EU_2030 = {"pm25": 10.0, "no2": 20.0}  # Directive (EU) 2024/2881, Annex I, annual, 2030
FLOOD_RETURN_PERIODS = (10, 100, 500)
FLOOD_BUFFER_M = 100.0
GREEN_BUFFER_M = 300.0
TREE_COVER_TARGET_PCT = 30.0  # 3-30-300 rule (Konijnendijk 2023)
PARK_DISTANCE_TARGET_M = 300.0  # 3-30-300 rule (Konijnendijk 2023)

HV_VIEWER = (
    "https://preglednik.voda.hr/?lang=hr&topic=Opasnosti%20od%20poplava"
    "&bgLayer=hr.raster.tk-crno-bijeli&layers=hr.karta-vjerojatnosti-pojavljivanja_2019"
    "&catalogNodes=1275"
)
EEA_NOISE_VIEWER = "https://noise.discomap.eea.europa.eu/"

POLLUTANT_NAMES = {"pm25": "PM2,5", "no2": "NO2"}

WORLDCOVER_TREE = {10}
WORLDCOVER_GREEN = {10, 20, 30, 90}  # trees, shrubs, grassland, wetland
WORLDCOVER_BUILT = {50}
WORLDCOVER_WATER = {80}


def _processed(name: str) -> Path:
    return get_settings().processed_dir / name


_DATASETS: dict[Path, rasterio.io.DatasetReader] = {}
_DATASETS_LOCK = threading.Lock()
_READ_LOCK = threading.Lock()


def _dataset(path: Path) -> rasterio.io.DatasetReader | None:
    """Open each raster once; GDAL handles are closed explicitly at exit."""
    with _DATASETS_LOCK:
        ds = _DATASETS.get(path)
        if ds is None:
            if not path.exists():
                return None
            ds = rasterio.open(path)
            _DATASETS[path] = ds
        return ds


@atexit.register
def _close_datasets() -> None:
    for ds in _DATASETS.values():
        ds.close()
    _DATASETS.clear()


def _window_around(
    ds: rasterio.io.DatasetReader, lon: float, lat: float, radius_m: float
) -> tuple[NDArray[np.float64], NDArray[np.float64], NDArray[np.float64]] | None:
    """Pixel values within radius of the point and their distances in metres.

    Works for rasters in EPSG:4326 (degrees) and projected CRSs in metres.
    Returns (values, distances, centre_value) or None when outside the raster.
    """
    xs, ys = warp_transform("EPSG:4326", ds.crs, [lon], [lat])
    x, y = xs[0], ys[0]
    row, col = ds.index(x, y)
    if not (0 <= row < ds.height and 0 <= col < ds.width):
        return None
    if ds.crs.is_geographic:
        m_per_px_x = abs(ds.transform.a) * 111_320.0 * math.cos(math.radians(lat))
        m_per_px_y = abs(ds.transform.e) * 110_574.0
    else:
        m_per_px_x, m_per_px_y = abs(ds.transform.a), abs(ds.transform.e)
    rx = math.ceil(radius_m / m_per_px_x)
    ry = math.ceil(radius_m / m_per_px_y)
    window = Window(col - rx, row - ry, 2 * rx + 1, 2 * ry + 1)
    # GDAL dataset handles are not thread-safe; requests run in a thread pool.
    with _READ_LOCK:
        data = ds.read(1, window=window, boundless=True, fill_value=ds.nodata or 0)
    data = data.astype(np.float64)
    yy, xx = np.mgrid[-ry : ry + 1, -rx : rx + 1]
    dist = np.hypot(xx * m_per_px_x, yy * m_per_px_y)
    inside = dist <= radius_m
    return data[inside], dist[inside], np.asarray([data[ry, rx]])


# --- Floods -----------------------------------------------------------------------------


@dataclass
class FloodReading:
    rp: int
    depth_at_point: float | None  # metres, None when dry
    max_depth_100m: float | None


def read_flood(lon: float, lat: float) -> list[FloodReading] | None:
    readings = []
    for rp in FLOOD_RETURN_PERIODS:
        ds = _dataset(_processed(f"flood_rp{rp}.tif"))
        if ds is None:
            return None
        found = _window_around(ds, lon, lat, FLOOD_BUFFER_M)
        if found is None:
            return None
        values, _, centre = found
        wet = values[values > 0]
        c = float(centre[0])
        readings.append(
            FloodReading(
                rp=rp,
                depth_at_point=c if c > 0 else None,
                max_depth_100m=float(wet.max()) if wet.size else None,
            )
        )
    return readings


def flood_category(lon: float, lat: float) -> Category:
    readings = read_flood(lon, lat)
    links = [Link(label="Službene karte opasnosti od poplava (Hrvatske vode)", url=HV_VIEWER)]
    notes = [
        "Karte JRC-a modeliraju samo riječne poplave većih rijeka u rezoluciji od oko 90 m. "
        "Ne obuhvaćaju bujice, poplave mora ni oborinske vode, a lokacija izvan modeliranog "
        "područja ne znači da rizika nema.",
        "Za službenu procjenu pogledajte karte Hrvatskih voda.",
    ]
    if readings is None:
        return Category(
            id="flood",
            group="environment",
            title="Poplave",
            status="no_data",
            status_label=label("no_data"),
            headline="Podaci o poplavama za ovu lokaciju nisu dostupni.",
            links=links,
            notes=notes,
        )
    src = "jrc_flood"
    when = retrieved_at(src)
    values: list[Value] = []
    for r in readings:
        at_point = r.depth_at_point is not None
        values.append(
            Value(
                key=f"flood_rp{r.rp}_point",
                label=f"U modeliranom poplavnom području, povratno razdoblje {r.rp} godina",
                value=at_point,
                display=(
                    f"da, dubina vode do {fmt.num(r.depth_at_point or 0, 1)} m"
                    if at_point
                    else "ne"
                ),
                source=src,
                retrieved_at=when,
                kind="modelled",
            )
        )
        values.append(
            Value(
                key=f"flood_rp{r.rp}_100m",
                label=f"Poplavno područje u krugu od 100 m, povratno razdoblje {r.rp} godina",
                value=r.max_depth_100m is not None,
                display=(
                    f"da, najveća dubina {fmt.num(r.max_depth_100m or 0, 1)} m"
                    if r.max_depth_100m is not None
                    else "ne"
                ),
                source=src,
                retrieved_at=when,
                kind="modelled",
            )
        )
    by_rp = {r.rp: r for r in readings}
    status: Status
    if by_rp[10].depth_at_point is not None:
        status = "bad"
        headline = (
            "Lokacija je u modeliranom poplavnom području velike vjerojatnosti "
            "(povratno razdoblje 10 godina)."
        )
    elif by_rp[100].depth_at_point is not None:
        status = "bad"
        headline = (
            "Lokacija je u modeliranom poplavnom području srednje vjerojatnosti "
            "(povratno razdoblje 100 godina)."
        )
    elif by_rp[500].depth_at_point is not None:
        status = "warning"
        headline = (
            "Lokacija je u modeliranom poplavnom području male vjerojatnosti "
            "(povratno razdoblje 500 godina)."
        )
    elif any(r.max_depth_100m is not None for r in readings):
        status = "warning"
        rp = min(r.rp for r in readings if r.max_depth_100m is not None)
        headline = (
            "Lokacija nije u modeliranom poplavnom području, ali je unutar 100 m od područja "
            f"s povratnim razdobljem od {rp} godina."
        )
    else:
        status = "good"
        headline = (
            "Lokacija nije u modeliranom području riječnih poplava ni za povratno razdoblje "
            "od 500 godina."
        )
    return Category(
        id="flood",
        group="environment",
        title="Poplave",
        status=status,
        status_label=label(status),
        headline=headline,
        values=values,
        links=links,
        notes=notes,
    )


# --- Air quality ------------------------------------------------------------------------


def read_air(lon: float, lat: float, pollutant: str, year: int = 2024) -> float | None:
    ds = _dataset(_processed(f"air_{pollutant}_{year}.tif"))
    if ds is None:
        return None
    found = _window_around(ds, lon, lat, 0.0)
    if found is None:
        return None
    value = float(found[2][0])
    if not math.isfinite(value) or value < 0 or value > 1000:
        return None
    return value


def _air_status(pollutant: str, value: float) -> Status:
    if value <= WHO_2021[pollutant]:
        return "good"
    if value <= EU_2030[pollutant]:
        return "warning"
    return "bad"


_STATUS_ORDER: dict[Status, int] = {"good": 0, "info": 0, "warning": 1, "bad": 2, "no_data": -1}


def air_category(lon: float, lat: float) -> Category:
    values: list[Value] = []
    statuses: list[Status] = []
    parts: list[str] = []
    for pollutant in ("pm25", "no2"):
        value = read_air(lon, lat, pollutant)
        name = POLLUTANT_NAMES[pollutant]
        src = f"eea_{pollutant}"
        if value is None:
            continue
        st = _air_status(pollutant, value)
        statuses.append(st)
        who, eu = WHO_2021[pollutant], EU_2030[pollutant]
        values.append(
            Value(
                key=f"{pollutant}_annual",
                label=f"{name}, godišnji prosjek 2024.",
                value=round(value, 1),
                unit="µg/m³",
                display=f"{fmt.num(value, 1)} µg/m³",
                source=src,
                retrieved_at=retrieved_at(src),
                kind="modelled",
                note=(
                    f"Smjernica WHO-a (2021): {fmt.num(who)} µg/m³; "
                    f"granična vrijednost EU-a od 2030.: {fmt.num(eu)} µg/m³."
                ),
            )
        )
        if st == "good":
            parts.append(f"{name} je unutar smjernice WHO-a")
        elif st == "warning":
            parts.append(
                f"{name} je iznad smjernice WHO-a, ali unutar granične vrijednosti EU-a "
                "koja vrijedi od 2030. godine"
            )
        else:
            parts.append(f"{name} je iznad granične vrijednosti EU-a koja vrijedi od 2030. godine")
    links = [
        Link(
            label="Kvaliteta zraka u stvarnom vremenu (Ministarstvo zaštite okoliša)",
            url="https://iszz.azo.hr/iskzl/",
        )
    ]
    if not values:
        return Category(
            id="air",
            group="environment",
            title="Kvaliteta zraka",
            status="no_data",
            status_label=label("no_data"),
            headline="Podaci o kvaliteti zraka za ovu lokaciju nisu dostupni.",
            links=links,
        )
    status = max(statuses, key=lambda s: _STATUS_ORDER[s])
    headline = "Prema modeliranoj karti za 2024. godinu, " + "; ".join(parts) + "."
    return Category(
        id="air",
        group="environment",
        title="Kvaliteta zraka",
        status=status,
        status_label=label(status),
        headline=headline,
        values=values,
        links=links,
        notes=[
            "Karta EEA-e procjena je godišnjeg prosjeka na mreži od 1 km, izrađena iz mjerenja "
            "i modela. Nije mjerenje na samoj adresi i ne služi za službenu provjeru "
            "usklađenosti s graničnim vrijednostima.",
        ],
    )


# --- Greenery and heat -------------------------------------------------------------------


def _worldcover_path(lon: float, lat: float) -> Path:
    lat0 = int(math.floor(lat / 3.0) * 3)
    lon0 = int(math.floor(lon / 3.0) * 3)
    tile = f"N{lat0:02d}E{lon0:03d}"
    return _processed("worldcover") / f"ESA_WorldCover_10m_2021_v200_{tile}_Map.tif"


def read_landcover(lon: float, lat: float) -> dict[str, float] | None:
    """Share (%) of trees, green and built-up land within 300 m, from WorldCover."""
    ds = _dataset(_worldcover_path(lon, lat))
    if ds is None:
        return None
    found = _window_around(ds, lon, lat, GREEN_BUFFER_M)
    if found is None:
        return None
    values = found[0]
    valid = values[values > 0]  # 0 is nodata
    land = valid[~np.isin(valid, list(WORLDCOVER_WATER))]
    if land.size == 0:
        return None
    total = float(land.size)
    return {
        "tree": 100.0 * float(np.isin(land, list(WORLDCOVER_TREE)).sum()) / total,
        "green": 100.0 * float(np.isin(land, list(WORLDCOVER_GREEN)).sum()) / total,
        "built": 100.0 * float(np.isin(land, list(WORLDCOVER_BUILT)).sum()) / total,
    }


def green_category(lon: float, lat: float, nearest_park: Place | None) -> Category:
    cover = read_landcover(lon, lat)
    src = "worldcover"
    values: list[Value] = []
    if cover is not None:
        for key, title in (
            ("tree", "Udio drveća u krugu od 300 m"),
            ("green", "Udio zelenih površina u krugu od 300 m"),
            ("built", "Udio izgrađenih površina u krugu od 300 m"),
        ):
            values.append(
                Value(
                    key=f"{key}_share_300m",
                    label=title,
                    value=round(cover[key], 1),
                    unit="%",
                    display=f"{fmt.num(cover[key])} %",
                    source=src,
                    retrieved_at=retrieved_at(src),
                    kind="modelled",
                    note="Udio kopnenih površina; vodene površine nisu uračunate."
                    if key == "built"
                    else None,
                )
            )
    park_ok: bool | None = None
    if nearest_park is not None:
        dist = nearest_park.distance_m
        park_ok = dist is not None and dist <= PARK_DISTANCE_TARGET_M
        if nearest_park.walk_minutes is not None:
            display = f"{fmt.minutes(nearest_park.walk_minutes)} hoda"
            value: float | None = nearest_park.walk_minutes
            unit = "min"
        else:
            display = f"{fmt.metres(dist)} zračne udaljenosti"
            value, unit = dist, "m"
        values.append(
            Value(
                key="nearest_park",
                label="Najbliži park",
                value=value,
                unit=unit,
                display=f"{display} ({nearest_park.name}), zračno {fmt.metres(dist)}",
                source="osm",
                retrieved_at=nearest_park.retrieved_at,
                kind="modelled",
            )
        )
    if cover is None:
        return Category(
            id="green",
            group="environment",
            title="Toplina i zelenilo",
            status="no_data",
            status_label=label("no_data"),
            headline="Podaci o pokrovu tla za ovu lokaciju nisu dostupni.",
            values=values,
        )
    tree_ok = cover["tree"] >= TREE_COVER_TARGET_PCT
    status: Status
    if tree_ok and park_ok:
        status = "good"
    elif tree_ok or park_ok:
        status = "warning"
    else:
        status = "bad"
    tree_txt = (
        f"Drveće pokriva {fmt.num(cover['tree'])} % površine u krugu od 300 m "
        f"({'na razini ili iznad' if tree_ok else 'ispod'} preporučenih 30 %)"
    )
    if park_ok is None:
        park_txt = "park nije pronađen u OpenStreetMapu u blizini"
    elif park_ok:
        park_txt = "park je unutar 300 m"
    else:
        park_txt = "najbliži park udaljen je više od 300 m"
    return Category(
        id="green",
        group="environment",
        title="Toplina i zelenilo",
        status=status,
        status_label=label(status),
        headline=f"{tree_txt}; {park_txt}.",
        values=values,
        places=[nearest_park] if nearest_park else [],
        notes=[
            "Drveće i zelene površine ublažavaju vrućine ljeti. Usporedba se temelji na "
            "pravilu 3-30-300 (najmanje 30 % krošnji u susjedstvu i javna zelena površina "
            "do 300 m od kuće).",
            "Pokrov tla iz satelitske karte ESA WorldCover za 2021. u rezoluciji 10 m.",
        ],
    )


# --- Noise (estimate) ------------------------------------------------------------------

NOISE_KINDS = {
    "motorway": "autocesta",
    "trunk": "brza cesta",
    "primary": "glavna cesta",
    "secondary": "važnija cesta",
    "rail": "željeznička pruga",
}


def noise_category(lon: float, lat: float, layers: Layers) -> Category:
    lines = layers.noise_lines
    links = [Link(label="Strateške karte buke (EEA, preglednik)", url=EEA_NOISE_VIEWER)]
    if lines is None:
        return Category(
            id="noise",
            group="environment",
            title="Buka",
            status="no_data",
            status_label=label("no_data"),
            headline="Podaci o prometnicama nisu dostupni.",
            links=links,
        )
    x, y = to_htrs(lon, lat)
    origin = Point(x, y)
    nearest: dict[str, tuple[float, str]] = {}
    for i in lines.tree.query(origin.buffer(2000.0), predicate="intersects"):
        kind = lines.kinds[int(i)]
        group = "rail" if kind == "rail" else "road"
        d = float(lines.geoms[int(i)].distance(origin))
        if group not in nearest or d < nearest[group][0]:
            nearest[group] = (d, kind)
    values: list[Value] = []
    for group, title in (("road", "Najbliža glavna cesta"), ("rail", "Najbliža pruga")):
        found = nearest.get(group)
        values.append(
            Value(
                key=f"distance_{group}",
                label=title,
                value=round(found[0]) if found else None,
                unit="m",
                display=(
                    f"{fmt.metres(found[0])} ({NOISE_KINDS[found[1]]})"
                    if found
                    else "dalje od 2 km"
                ),
                source="osm",
                retrieved_at=retrieved_at("osm"),
                kind="estimate",
            )
        )
    road = nearest.get("road")
    rail = nearest.get("rail")
    bits = []
    if road:
        bits.append(f"{NOISE_KINDS[road[1]]} je udaljena {fmt.metres(road[0])}")
    if rail:
        bits.append(f"pruga je udaljena {fmt.metres(rail[0])}")
    headline = (
        "Procjena prema udaljenosti od prometnica: " + "; ".join(bits) + "."
        if bits
        else "U krugu od 2 km nema autoceste, brze, glavne ili važnije ceste ni željezničke pruge."
    )
    return Category(
        id="noise",
        group="environment",
        title="Buka",
        status="info",
        status_label=label("info"),
        headline=headline[0].upper() + headline[1:],
        values=values,
        links=links,
        notes=[
            "Ovo je procjena, a ne izmjerena razina buke: prikazana je samo udaljenost od "
            "autocesta, brzih, glavnih i važnijih cesta te pruga iz OpenStreetMapa.",
            "Strateške karte buke za veće gradove i glavne prometnice mogu se pogledati u "
            "pregledniku EEA-e. Svjetska zdravstvena organizacija preporučuje da buka "
            "cestovnog prometa bude ispod 53 dB Lden danju i 45 dB Lnight noću.",
        ],
    )
