"""JRC PVGIS API client: yearly PV output per kWp at the optimal slope."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from functools import lru_cache

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


def _round(value: float) -> float:
    # About 1 km; PVGIS radiation data has a resolution of a few kilometres.
    return round(value, 2)


@lru_cache(maxsize=4096)
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
            timeout=20.0,
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


def yearly_output(lat: float, lon: float) -> SolarResult:
    return _query(_round(lat), _round(lon))
