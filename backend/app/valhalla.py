"""Client for the Valhalla walking router (isochrones, walking-time matrix and routes)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from app.config import get_settings

# 4.5 km/h, see docs/ODLUKE.md and docs/METODOLOGIJA.md.
WALKING_SPEED_KMH = 4.5
COSTING_OPTIONS = {"pedestrian": {"walking_speed": WALKING_SPEED_KMH}}
MAX_TARGETS_PER_REQUEST = 200
# A route is asked for on a click; the browser gives up after about 8 s.
ROUTE_TIMEOUT_S = 7.0
# Valhalla encodes route shapes as polylines with six decimal places.
SHAPE_PRECISION = 6


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


@dataclass(frozen=True)
class WalkPath:
    """A walking route along streets and paths."""

    coordinates: list[tuple[float, float]]  # (lon, lat)
    length_m: float
    time_s: float


def route_payload(start: tuple[float, float], end: tuple[float, float]) -> dict[str, Any]:
    """Request for a walking route between two (lat, lon) points.

    Same costing and walking speed as the isochrones and the matrix, so the time of a
    route equals the walking time in the report.
    """
    return {
        "locations": [{"lat": start[0], "lon": start[1]}, {"lat": end[0], "lon": end[1]}],
        "costing": "pedestrian",
        "costing_options": COSTING_OPTIONS,
        "units": "kilometers",
        "directions_type": "none",
    }


def decode_shape(encoded: str, precision: int = SHAPE_PRECISION) -> list[tuple[float, float]]:
    """Decode an encoded polyline to (lon, lat) pairs.

    The usual polyline algorithm: each value is the difference from the previous one,
    multiplied by 10**precision, zigzag-encoded and written in 5-bit chunks offset by 63.
    """
    factor = 10.0**precision
    coordinates: list[tuple[float, float]] = []
    index = lat = lon = 0
    while index < len(encoded):
        deltas = []
        for _ in range(2):
            shift = result = 0
            while True:
                if index >= len(encoded):
                    raise ValueError("polyline ends in the middle of a value")
                chunk = ord(encoded[index]) - 63
                index += 1
                if not 0 <= chunk < 64:
                    raise ValueError(f"invalid polyline character at {index - 1}")
                result |= (chunk & 0x1F) << shift
                shift += 5
                if chunk < 0x20:
                    break
            deltas.append(~(result >> 1) if result & 1 else result >> 1)
        lat += deltas[0]
        lon += deltas[1]
        coordinates.append((round(lon / factor, precision), round(lat / factor, precision)))
    return coordinates


def parse_route(data: Any) -> WalkPath | None:
    """Shape, length and time of a Valhalla `route` answer (units: kilometers)."""
    if not isinstance(data, dict) or "trip" not in data:
        return None
    trip = data["trip"]
    if trip.get("status", 0) != 0:
        return None
    coordinates: list[tuple[float, float]] = []
    for leg in trip.get("legs", []):
        points = decode_shape(leg["shape"])
        # consecutive legs share their joining point
        coordinates.extend(points[1:] if coordinates and points else points)
    if len(coordinates) < 2:
        return None
    summary = trip["summary"]
    return WalkPath(
        coordinates=coordinates,
        length_m=float(summary["length"]) * 1000.0,
        time_s=float(summary["time"]),
    )


def route(start: tuple[float, float], end: tuple[float, float]) -> WalkPath | None:
    """Walking route between two (lat, lon) points, or None when there is no path."""
    return parse_route(_post("route", route_payload(start, end), timeout=ROUTE_TIMEOUT_S))
