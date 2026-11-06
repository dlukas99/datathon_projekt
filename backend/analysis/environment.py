"""Environmental categories read from rasters and vector layers at a point."""

from __future__ import annotations

import atexit
import math
import re
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
from app.models import Category, Link, Place, Scale, ScaleBand, ScaleMarker, Status, Value
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
    # Translate the return period into the chance of at least one such flood during
    # a 30-year housing loan: 1 - (1 - 1/T)^30.
    zone_rp = next((r.rp for r in readings if r.depth_at_point is not None), None)
    near_rp = next((r.rp for r in readings if r.max_depth_100m is not None), None)
    rp_for_chance = zone_rp or near_rp
    if rp_for_chance is not None:
        chance = flood_chance(rp_for_chance)
        where = "na adresi" if zone_rp else "u krugu od 100 m"
        values.insert(
            0,
            Value(
                key="flood_30y_probability",
                label=f"Vjerojatnost barem jedne poplave {where} u 30 godina",
                value=round(chance * 100),
                unit="%",
                display=f"oko {fmt.num(round(chance * 100))} %",
                source=src,
                retrieved_at=when,
                kind="modelled",
                note=(
                    f"Za povratno razdoblje od {rp_for_chance} godina: 1 − (1 − 1/"
                    f"{rp_for_chance})³⁰. Trideset godina je uobičajeno trajanje stambenog kredita."
                ),
            ),
        )
        headline += (
            f" To znači oko {fmt.num(round(chance * 100))} % vjerojatnosti da u 30 godina "
            f"(trajanje stambenog kredita) {where} bude barem jedna takva poplava."
        )
    notes.append(
        "Povratno razdoblje od 100 godina ne znači poplavu jednom u sto godina, nego 1 % "
        "vjerojatnosti svake godine; tijekom 30 godina to je oko 26 %."
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


def flood_chance(return_period: int, years: int = 30) -> float:
    """Probability of at least one flood of this return period within `years`."""
    return 1.0 - (1.0 - 1.0 / return_period) ** years


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


# Graded scale, calmer than a pass/fail against WHO: the band limits are the WHO
# guideline, the EU limit from 2030 and the EU limit in force today
# (Directive (EU) 2024/2881, Annex I; WHO AQG 2021, Table 0.1).
AIR_BANDS: dict[str, list[tuple[float | None, str, Status]]] = {
    "pm25": [
        (5.0, "vrlo niska", "good"),
        (10.0, "niska", "good"),
        (25.0, "umjerena", "info"),
        (None, "visoka", "bad"),
    ],
    "no2": [
        (10.0, "vrlo niska", "good"),
        (20.0, "niska", "good"),
        (40.0, "umjerena", "info"),
        (None, "visoka", "bad"),
    ],
}
EU_NOW = {"pm25": 25.0, "no2": 40.0}  # EU limit values in force until the 2030 limits apply


def air_band(pollutant: str, value: float) -> tuple[str, Status]:
    for upto, name, status in AIR_BANDS[pollutant]:
        if upto is None or value <= upto:
            return name, status
    raise ValueError(pollutant)


def _air_status(pollutant: str, value: float) -> Status:
    return air_band(pollutant, value)[1]


_STATUS_ORDER: dict[Status, int] = {"good": 0, "info": 1, "warning": 2, "bad": 3, "no_data": -1}
_BAND_ORDER = ["vrlo niska", "niska", "umjerena", "visoka"]

# The card rates the air itself, so "low pollution" never reads as "low quality". The
# levels above stay the keys used by the score and the settlement finder.
AIR_RATINGS: dict[str, str] = {
    "vrlo niska": "Vrlo dobar",
    "niska": "Dobar",
    "umjerena": "Umjeren",
    "visoka": "Loš",
}
AIR_SENTENCES: dict[str, str] = {
    "vrlo niska": (
        "Kroz godinu je zrak ovdje vrlo čist: prosjek onečišćenja unutar je preporuke "
        "Svjetske zdravstvene organizacije."
    ),
    "niska": (
        "Kroz godinu je zrak ovdje uglavnom čist: prosjek onečišćenja unutar je granice EU-a "
        "za 2030., ali iznad strože preporuke Svjetske zdravstvene organizacije."
    ),
    "umjerena": (
        "Kroz godinu je zrak ovdje umjereno onečišćen: prosjek je unutar granice EU-a koja "
        "vrijedi danas, ali iznad strože granice za 2030."
    ),
    "visoka": (
        "Kroz godinu je zrak ovdje onečišćen: prosjek je iznad granične vrijednosti EU-a "
        "koja vrijedi danas."
    ),
}


def air_level(cat: Category) -> str | None:
    """The worse of the PM2.5 and NO2 levels ("vrlo niska" to "visoka"), or None."""
    levels = [s.band for s in cat.scales if s.band in _BAND_ORDER]
    return max(levels, key=_BAND_ORDER.index) if levels else None


def _pair(limits: dict[str, float]) -> str:
    return f"PM2,5 {fmt.num(limits['pm25'])} µg/m³, NO2 {fmt.num(limits['no2'])} µg/m³"


def _compare_sentence(name: str, pollutant: str, value: float) -> str:
    who, eu30, now = WHO_2021[pollutant], EU_2030[pollutant], EU_NOW[pollutant]
    if value <= who:
        return f"{name} je unutar smjernice WHO-a ({fmt.num(who)} µg/m³)."
    if value <= eu30:
        return (
            f"{name} je unutar granične vrijednosti EU-a za 2030. ({fmt.num(eu30)} µg/m³), "
            f"ali iznad strože smjernice WHO-a ({fmt.num(who)} µg/m³)."
        )
    if value <= now:
        return (
            f"{name} je unutar granične vrijednosti EU-a koja vrijedi danas "
            f"({fmt.num(now)} µg/m³), "
            f"a iznad buduće granice za 2030. ({fmt.num(eu30)} µg/m³)."
        )
    return f"{name} je iznad granične vrijednosti EU-a koja vrijedi danas ({fmt.num(now)} µg/m³)."


def air_category(lon: float, lat: float) -> Category:
    values: list[Value] = []
    scales: list[Scale] = []
    bands: list[tuple[str, Status]] = []
    compare: list[str] = []
    for pollutant in ("pm25", "no2"):
        value = read_air(lon, lat, pollutant)
        name = POLLUTANT_NAMES[pollutant]
        src = f"eea_{pollutant}"
        if value is None:
            continue
        band, status = air_band(pollutant, value)
        bands.append((band, status))
        compare.append(_compare_sentence(name, pollutant, value))
        values.append(
            Value(
                key=f"{pollutant}_annual",
                label=f"{name}, godišnji prosjek 2024.",
                value=round(value, 1),
                unit="µg/m³",
                display=f"{fmt.num(value, 1)} µg/m³ ({band} razina)",
                source=src,
                retrieved_at=retrieved_at(src),
                kind="modelled",
                note=compare[-1],
            )
        )
        scales.append(
            Scale(
                key=pollutant,
                label=f"Razina onečišćenja {name}, godišnji prosjek",
                unit="µg/m³",
                value=round(value, 1),
                band=band,
                bands=[ScaleBand(upto=u, label=n, status=st) for u, n, st in AIR_BANDS[pollutant]],
                markers=[
                    ScaleMarker(value=WHO_2021[pollutant], label="WHO"),
                    ScaleMarker(value=EU_2030[pollutant], label="EU 2030."),
                    ScaleMarker(value=EU_NOW[pollutant], label="EU danas"),
                ],
            )
        )
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
    worst = max(bands, key=lambda b: _BAND_ORDER.index(b[0]))
    return Category(
        id="air",
        group="environment",
        title="Kvaliteta zraka",
        status=worst[1],
        status_label=AIR_RATINGS[worst[0]],
        headline=AIR_SENTENCES[worst[0]],
        values=values,
        links=links,
        scales=scales,
        notes=[
            "Ocjena je lošija od ocjena za PM2,5 i NO2 (godišnji prosjek, karta EEA-e za "
            f"2024.): vrlo dobar do smjernice Svjetske zdravstvene organizacije "
            f"({_pair(WHO_2021)}), dobar do granične vrijednosti EU-a za 2030. "
            f"({_pair(EU_2030)}), umjeren do granične vrijednosti EU-a koja vrijedi danas "
            f"({_pair(EU_NOW)}), loš iznad nje.",
            "Karta EEA-e procjena je godišnjeg prosjeka na mreži od 1 km, izrađena iz mjerenja "
            "i modela. Nije mjerenje na samoj adresi i ne služi za službenu provjeru "
            "usklađenosti s graničnim vrijednostima.",
            "Karta prikazuje pozadinsku razinu: uz prometne ulice NO2 može biti znatno viši "
            "(u našoj provjeri prometne postaje u Zagrebu i Osijeku mjerile su 5–17 µg/m³ više "
            "od karte). Vidi i kategoriju „Udaljenost od prometnica”.",
        ],
    )


# --- Greenery and shade -------------------------------------------------------------------

# Tree cover and the nearest park stand in for shade; temperature is not measured.
GREEN_TITLE = "Zelenilo i hlad"


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
                    note="Udio kopna; more i druge vodene površine nisu uračunate."
                    if key == "tree"
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
            title=GREEN_TITLE,
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
        f"Drveće pokriva {fmt.num(cover['tree'])} % kopna u krugu od 300 m "
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
        title=GREEN_TITLE,
        status=status,
        status_label=label(status),
        headline=f"{tree_txt}; {park_txt}.",
        values=values,
        places=[nearest_park] if nearest_park else [],
        notes=[
            "Drveće ljeti daje hlad i ublažava vrućine. Temperaturu ne mjerimo; usporedba se "
            "temelji na pravilu 3-30-300 (najmanje 30 % krošnji u susjedstvu i javna zelena "
            "površina do 300 m od kuće).",
            "Udjeli su iz satelitske karte ESA WorldCover za 2021. u rezoluciji 10 m, za kopno "
            "u krugu od 300 m od lokacije; more i druge vodene površine nisu uračunate. Drveće "
            "su krošnje koje karta prepoznaje kao drveće; zelene površine uključuju i grmlje, "
            "travnjake i močvare.",
            "Karta u rezoluciji 10 m ne razlikuje pojedinačna stabla u dvorištima i uz ulice kad "
            "je oko njih izgrađeno, pa je udio drveća u gusto izgrađenim središtima i selima s "
            "vrtovima vjerojatno nešto veći.",
        ],
    )


# --- Distance from major roads (proxy for traffic noise and exhaust) ---------------------

NOISE_TITLE = "Udaljenost od prometnica"
# HEI (2010), Special Report 17: traffic pollution is highest within roughly 300 to 500 m
# of a major road and falls to background levels beyond that.
TRAFFIC_BANDS: list[tuple[float | None, str, Status]] = [
    (300.0, "Blizu prometnice", "warning"),
    (500.0, "Rub zone prometa", "info"),
    (None, "Podalje od prometnica", "good"),
]
_COUNTY_REF = re.compile(r"\d{4}")


def road_name(kind: str, ref: str) -> str:
    """Croatian road class from OSM tags (wiki "Croatia/Ceste"): motorway is an autocesta,
    trunk a brza cesta, primary a državna cesta (ref D…), secondary a županijska cesta
    (four-digit ref, no prefix in OSM) or a former one inside a city (no ref)."""
    first = (ref or "").split(";")[0].strip()
    if kind == "rail":
        return "željeznička pruga"
    if kind == "motorway":
        return f"autocesta {first}" if first.startswith("A") else "autocesta"
    if kind == "trunk":
        return f"brza cesta {first}" if first[:1] in ("A", "D") else "brza cesta"
    if kind == "primary":
        return f"državna cesta {first}" if first.startswith("D") else "glavna cesta"
    if _COUNTY_REF.fullmatch(first):
        return f"županijska cesta Ž{first}"
    return "županijska ili glavna gradska cesta" if not first else "važnija cesta"


def traffic_band(distance_m: float) -> tuple[str, Status]:
    for upto, name, status in TRAFFIC_BANDS:
        if upto is None or distance_m <= upto:
            return name, status
    raise ValueError(distance_m)


def _traffic_sentence(road: str, distance: float) -> str:
    where = f"{road[:1].upper()}{road[1:]} je {fmt.metres(distance)} od lokacije"
    if distance <= 300:
        return (
            f"{where}, unutar 300 m, gdje su buka i ispušni plinovi prometa obično najizraženiji."
        )
    if distance <= 500:
        return f"{where}, na rubu zone od 300 do 500 m u kojoj se utjecaj prometa smanjuje."
    return f"{where}; na toj udaljenosti utjecaj prometa obično je slab."


def noise_category(lon: float, lat: float, layers: Layers) -> Category:
    lines = layers.noise_lines
    links = [Link(label="Strateške karte buke (EEA, preglednik)", url=EEA_NOISE_VIEWER)]
    if lines is None:
        return Category(
            id="noise",
            group="environment",
            title=NOISE_TITLE,
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
            nearest[group] = (d, road_name(kind, lines.refs[int(i)]))
    values: list[Value] = []
    for group, value_label in (
        ("road", "Najbliža autocesta, brza, državna ili županijska cesta"),
        ("rail", "Najbliža pruga"),
    ):
        found = nearest.get(group)
        values.append(
            Value(
                key=f"distance_{group}",
                label=value_label,
                value=round(found[0]) if found else None,
                unit="m",
                display=f"{fmt.metres(found[0])} ({found[1]})" if found else "dalje od 2 km",
                source="osm",
                retrieved_at=retrieved_at("osm"),
                kind="estimate",
            )
        )
    road = nearest.get("road")
    rail = nearest.get("rail")
    distance = road[0] if road else 2000.0
    band, status = traffic_band(distance)
    sentences = [
        _traffic_sentence(road[1], road[0])
        if road
        else "U krugu od 2 km nema autoceste, brze, državne ni županijske ceste."
    ]
    if rail and rail[0] <= 500:
        sentences.append(f"Željeznička pruga je {fmt.metres(rail[0])} od lokacije.")
    scale = Scale(
        key="road_distance",
        label="Udaljenost od velike prometnice",
        unit="m",
        value=round(min(distance, 2000.0)),
        band=band.lower(),
        bands=[ScaleBand(upto=u, label=n.lower(), status=st) for u, n, st in TRAFFIC_BANDS],
        markers=[ScaleMarker(value=300, label="300 m"), ScaleMarker(value=500, label="500 m")],
    )
    return Category(
        id="noise",
        group="environment",
        title=NOISE_TITLE,
        status=status,
        status_label=band,
        headline=" ".join(sentences),
        values=values,
        links=links,
        scales=[scale],
        notes=[
            "Ne mjerimo buku: ovo je procjena prema zračnoj udaljenosti od lokacije (adrese ili "
            "središta naselja) do osi najbliže autoceste, brze, državne ili županijske ceste "
            "(u gradovima i bivše županijske ceste, danas glavne gradske ulice) te pruge iz "
            "OpenStreetMapa. Ostale ulice se ne broje.",
            "Pojasevi slijede pregled istraživanja Health Effects Institutea (2010.): "
            "onečišćenje od prometa najveće je unutar približno 300 do 500 m od velike "
            "prometnice, a dalje pada na pozadinsku razinu.",
            "U Skoru za život veći broj znači manje prometa: 100 je dalje od 500 m od velike "
            "prometnice, 60 od 300 do 500 m, a 25 do 300 m.",
            "Strateške karte buke za veće gradove mogu se pogledati u pregledniku EEA-e. "
            "Svjetska zdravstvena organizacija preporučuje da buka cestovnog prometa bude "
            "ispod 53 dB Lden danju i 45 dB Lnight noću.",
        ],
    )


# --- Wildfires (burnt areas) ---------------------------------------------------------------

FIRE_RADIUS_M = 2000.0
EFFIS_VIEWER = "https://forest-fire.emergency.copernicus.eu/apps/effis_current_situation/"


def fire_category(lon: float, lat: float, layers: Layers) -> Category:
    burnt = layers.burnt
    links = [Link(label="Požari u stvarnom vremenu (EFFIS)", url=EFFIS_VIEWER)]
    if burnt is None:
        return Category(
            id="fire",
            group="environment",
            title="Požari raslinja",
            status="no_data",
            status_label=label("no_data"),
            headline="Podaci o opožarenim površinama nisu dostupni.",
            links=links,
        )
    x, y = to_htrs(lon, lat)
    origin = Point(x, y)
    hits = []
    for i in burnt.tree.query(origin.buffer(FIRE_RADIUS_M), predicate="intersects"):
        idx = int(i)
        hits.append((burnt.dates[idx], burnt.areas[idx], float(burnt.geoms[idx].distance(origin))))
    hits.sort(key=lambda h: h[0], reverse=True)
    src = "effis"
    when = retrieved_at(src)
    values = [
        Value(
            key="burnt_areas_2km",
            label="Opožarene površine u krugu od 2 km",
            value=len(hits),
            display=str(len(hits)),
            source=src,
            retrieved_at=when,
            kind="measured",
        )
    ]
    if hits:
        nearest = min(hits, key=lambda h: h[2])
        largest = max(hits, key=lambda h: h[1])
        values.append(
            Value(
                key="burnt_nearest_m",
                label="Najbliža opožarena površina",
                value=round(nearest[2]),
                unit="m",
                display=(
                    "na samoj lokaciji"
                    if nearest[2] == 0
                    else f"{fmt.metres(nearest[2])} ({nearest[0][:4]}.)"
                ),
                source=src,
                retrieved_at=when,
                kind="measured",
            )
        )
        values.append(
            Value(
                key="burnt_largest_ha",
                label="Najveća opožarena površina u krugu od 2 km",
                value=round(largest[1]),
                unit="ha",
                display=f"{fmt.num(largest[1])} ha ({largest[0][:4]}.)",
                source=src,
                retrieved_at=when,
                kind="measured",
            )
        )
        years = sorted({h[0][:4] for h in hits})
        n = len(hits)
        verb = fmt.plural(n, "zabilježena je", "zabilježene su", "zabilježeno je")
        noun = fmt.plural(n, "opožarena površina", "opožarene površine", "opožarenih površina")
        headline = (
            f"U krugu od 2 km satelitom {verb} {n} {noun} ({', '.join(y + '.' for y in years)})."
        )
    else:
        headline = "U krugu od 2 km satelitom nije zabilježena nijedna opožarena površina od 2016."
    return Category(
        id="fire",
        group="environment",
        title="Požari raslinja",
        status="info",
        status_label=label("info"),
        headline=headline,
        values=values,
        links=links,
        notes=[
            "Opožarene površine kartira EFFIS iz satelitskih snimaka od 2016.; manji požari "
            "mogu nedostajati. Prošli požari pokazuju izloženost, a ne predviđaju buduće.",
        ],
    )
