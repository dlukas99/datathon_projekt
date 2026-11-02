"""Client for the Valhalla walking router (isochrones and walking-time matrix)."""

from __future__ import annotations

from typing import Any

import httpx

from app.config import get_settings

# 4.5 km/h, see docs/ODLUKE.md and docs/METODOLOGIJA.md.
WALKING_SPEED_KMH = 4.5
COSTING_OPTIONS = {"pedestrian": {"walking_speed": WALKING_SPEED_KMH}}
MAX_TARGETS_PER_REQUEST = 200


class RouterUnavailable(RuntimeError):
    """The walking router could not be reached or returned an error."""


def _post(endpoint: str, payload: dict[str, Any], timeout: float = 15.0) -> Any:
    url = f"{get_settings().valhalla_url.rstrip('/')}/{endpoint}"
    try:
        response = httpx.post(url, json=payload, timeout=timeout)
    except httpx.HTTPError as exc:
        raise RouterUnavailable(str(exc)) from exc
    if response.status_code == 400:
        # Valhalla answers 400 when a location cannot be snapped to the network.
        return None
    if response.status_code != 200:
        raise RouterUnavailable(f"Valhalla {endpoint}: HTTP {response.status_code}")
    return response.json()


def isochrones(lat: float, lon: float, minutes: tuple[int, ...] = (5, 10, 15)) -> Any:
    """GeoJSON FeatureCollection with one polygon per contour, or None."""
    payload = {
        "locations": [{"lat": lat, "lon": lon}],
        "costing": "pedestrian",
        "costing_options": COSTING_OPTIONS,
        "contours": [{"time": m} for m in minutes],
        "polygons": True,
        "denoise": 0.5,
        "generalize": 15,
    }
    return _post("isochrone", payload)


def walk_minutes(lat: float, lon: float, targets: list[tuple[float, float]]) -> list[float | None]:
    """Walking time in minutes from (lat, lon) to each (lat, lon) target."""
    result: list[float | None] = []
    for start in range(0, len(targets), MAX_TARGETS_PER_REQUEST):
        chunk = targets[start : start + MAX_TARGETS_PER_REQUEST]
        payload = {
            "sources": [{"lat": lat, "lon": lon}],
            "targets": [{"lat": t[0], "lon": t[1]} for t in chunk],
            "costing": "pedestrian",
            "costing_options": COSTING_OPTIONS,
        }
        data = _post("sources_to_targets", payload, timeout=30.0)
        if data is None:
            result.extend([None] * len(chunk))
            continue
        row = data["sources_to_targets"][0]
        for cell in row:
            time_s = cell.get("time")
            result.append(None if time_s is None else round(time_s / 60.0, 1))
    return result
