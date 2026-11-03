"""JRC PVGIS API client: yearly PV output per kWp at the optimal slope."""

from __future__ import annotations

import threading
from concurrent.futures import Future, ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout
from dataclasses import dataclass
from datetime import UTC, datetime

import httpx

from app.config import get_settings

PVGIS_URL = "https://re.jrc.ec.europa.eu/api/v5_3/PVcalc"
# PVGIS default system loss in percent (PVGIS user manual).
SYSTEM_LOSS_PCT = 14


@dataclass(frozen=True)
class SolarResult:
    kwh_per_kwp_year: float
    optimal_slope_deg: float
    optimal_azimuth_deg: float
    radiation_db: str
    years: str
    retrieved_at: str


class SolarUnavailable(RuntimeError):
    pass


class SolarPending(SolarUnavailable):
    """The answer is on its way; it will be cached for the next request."""


def _round(value: float) -> float:
    # About 1 km; PVGIS radiation data has a resolution of a few kilometres.
    return round(value, 2)


# PVGIS answers in 1 to 15 seconds. Requests run in the background (at most two at
# a time, polite to the service); a report waits at most WAIT_SECONDS and the
# answer still lands in the cache for the next visit.
WAIT_SECONDS = 6.0
REQUEST_TIMEOUT = 25.0
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="pvgis")
_lock = threading.Lock()
_cache: dict[tuple[float, float], SolarResult] = {}
_pending: dict[tuple[float, float], Future[SolarResult]] = {}
MAX_CACHE = 4096


def _query(lat: float, lon: float) -> SolarResult:
    params: dict[str, str | int | float] = {
        "lat": lat,
        "lon": lon,
        "peakpower": 1,
        "loss": SYSTEM_LOSS_PCT,
        "optimalangles": 1,
        "outputformat": "json",
    }
    try:
        response = httpx.get(
            PVGIS_URL,
            params=params,
            headers={"User-Agent": get_settings().user_agent},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        data = response.json()
        fixed = data["outputs"]["totals"]["fixed"]
        mounting = data["inputs"]["mounting_system"]["fixed"]
        meteo = data["inputs"]["meteo_data"]
    except (httpx.HTTPError, KeyError, ValueError) as exc:
        raise SolarUnavailable(str(exc)) from exc
    return SolarResult(
        kwh_per_kwp_year=float(fixed["E_y"]),
        optimal_slope_deg=float(mounting["slope"]["value"]),
        optimal_azimuth_deg=float(mounting["azimuth"]["value"]),
        radiation_db=str(meteo.get("radiation_db", "")),
        years=f"{meteo.get('year_min')}–{meteo.get('year_max')}",
        retrieved_at=datetime.now(UTC).isoformat(timespec="seconds"),
    )


def _fetch(key: tuple[float, float]) -> SolarResult:
    try:
        result = _query(*key)
        with _lock:
            if len(_cache) >= MAX_CACHE:
                _cache.clear()
            _cache[key] = result
        return result
    finally:
        with _lock:
            _pending.pop(key, None)


def yearly_output(lat: float, lon: float, wait: float = WAIT_SECONDS) -> SolarResult:
    """Cached PVGIS result; raises SolarUnavailable (or SolarPending) when not ready."""
    key = (_round(lat), _round(lon))
    with _lock:
        cached = _cache.get(key)
        if cached is not None:
            return cached
        future = _pending.get(key)
        if future is None:
            future = _executor.submit(_fetch, key)
            _pending[key] = future
    try:
        return future.result(timeout=wait)
    except FutureTimeout as exc:
        raise SolarPending("PVGIS još računa") from exc


def warm(points: list[tuple[float, float]]) -> None:
    """Start background requests (e.g. for the demo addresses at start-up)."""
    for lat, lon in points:
        key = (_round(lat), _round(lon))
        with _lock:
            if key in _cache or key in _pending:
                continue
            _pending[key] = _executor.submit(_fetch, key)
