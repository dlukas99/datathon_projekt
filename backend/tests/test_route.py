"""Walking routes for the map: Valhalla request, shape decoding, minutes and the API."""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from analysis.walking import Reach
from app import valhalla, walk_route
from app.main import app
from app.models import Place

client = TestClient(app)

SPLIT = (43.503528, 16.42797)  # Grad Split, demo address
NEARBY = (43.5085, 16.4337)


def encode(points: list[tuple[float, float]], precision: int = 6) -> str:
    """Reference encoder for (lon, lat) points, used to check the decoder."""
    factor = 10**precision
    out: list[str] = []
    prev_lat = prev_lon = 0
    for lon, lat in points:
        ilat, ilon = round(lat * factor), round(lon * factor)
        for delta in (ilat - prev_lat, ilon - prev_lon):
            value = ~(delta << 1) if delta < 0 else delta << 1
            while value >= 0x20:
                out.append(chr((0x20 | (value & 0x1F)) + 63))
                value >>= 5
            out.append(chr(value + 63))
        prev_lat, prev_lon = ilat, ilon
    return "".join(out)


def test_decode_shape_matches_the_published_example() -> None:
    # Example from the polyline algorithm description (precision 5).
    example = "_p~iF~ps|U_ulLnnqC_mqNvxq`@"
    assert valhalla.decode_shape(example, precision=5) == [
        (-120.2, 38.5),
        (-120.95, 40.7),
        (-126.453, 43.252),
    ]
    # Valhalla uses six decimals: the same string means ten times smaller degrees.
    assert valhalla.decode_shape(example) == [
        (-12.02, 3.85),
        (-12.095, 4.07),
        (-12.6453, 4.3252),
    ]


def test_decode_shape_round_trip() -> None:
    points = [(16.42797, 43.503528), (16.427841, 43.503446), (16.4337, 43.5085), (13.5, 45.1)]
    assert valhalla.decode_shape(encode(points)) == points
    assert valhalla.decode_shape("") == []


def test_decode_shape_rejects_broken_input() -> None:
    with pytest.raises(ValueError):
        valhalla.decode_shape("_p~iF~ps|")  # ends in the middle of a value
    with pytest.raises(ValueError):
        valhalla.decode_shape("_p~iF ps|U")  # space is not a polyline character


def test_route_payload_uses_the_report_walking_profile() -> None:
    payload = valhalla.route_payload(SPLIT, NEARBY)
    assert payload["locations"] == [
        {"lat": 43.503528, "lon": 16.42797},
        {"lat": 43.5085, "lon": 16.4337},
    ]
    assert payload["costing"] == "pedestrian"
    # same speed as the isochrones and the walking-time matrix
    assert payload["costing_options"] == valhalla.COSTING_OPTIONS
    assert payload["costing_options"]["pedestrian"]["walking_speed"] == 4.5
    assert payload["units"] == "kilometers"
    assert payload["directions_type"] == "none"


def trip(*legs: list[tuple[float, float]], length_km: float, time_s: float) -> dict[str, object]:
    return {
        "trip": {
            "status": 0,
            "legs": [{"shape": encode(points)} for points in legs],
            "summary": {"length": length_km, "time": time_s},
        }
    }


def test_parse_route_reads_shape_length_and_time() -> None:
    a, b, c = (16.42797, 43.503528), (16.4300, 43.5050), (16.4337, 43.5085)
    path = valhalla.parse_route(trip([a, b], [b, c], length_km=0.855, time_s=714.0))
    assert path is not None
    assert path.coordinates == [a, b, c]  # the joining point is not repeated
    assert path.length_m == pytest.approx(855.0)
    assert path.time_s == 714.0


def test_parse_route_without_a_path() -> None:
    assert valhalla.parse_route(None) is None  # Valhalla answered 400 (no path)
    assert valhalla.parse_route({"error": "No path could be found"}) is None
    failed = trip([(16.4, 43.5), (16.5, 43.6)], length_km=1, time_s=1)
    failed["trip"]["status"] = 442  # type: ignore[index]
    assert valhalla.parse_route(failed) is None


def test_minutes_come_from_the_router_time_like_the_report() -> None:
    # Valhalla adds time at some points of the network, so 855 m is 11.9 min here, not
    # 855 m / 4.5 km/h = 11.4 min. The report's walking times are the same router time
    # (rounded to 0.1 min).
    path = valhalla.WalkPath(coordinates=[SPLIT[::-1], NEARBY[::-1]], length_m=855.4, time_s=714.0)
    feature = walk_route.route_feature(path)
    assert feature.properties.walk_minutes == 11.9
    assert feature.properties.distance_m == 855
    assert feature.properties.walking_speed_kmh == valhalla.WALKING_SPEED_KMH
    assert feature.properties.source == "valhalla"
    assert feature.properties.kind == "modelled"
    assert feature.geometry.coordinates == [(16.42797, 43.503528), (16.4337, 43.5085)]


def test_far_destinations_are_refused_before_asking_the_router(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def unexpected(*_: object) -> None:
        raise AssertionError("router must not be called")

    monkeypatch.setattr(valhalla, "route", unexpected)
    with pytest.raises(walk_route.TooFar):
        walk_route.walk_route(SPLIT, (45.8, 15.97))  # Split to Zagreb


def fake_path(*_: object) -> valhalla.WalkPath:
    return valhalla.WalkPath(
        coordinates=[(16.42797, 43.503528), (16.4337, 43.5085)], length_m=855.0, time_s=714.0
    )


def route_params(start: tuple[float, float], end: tuple[float, float]) -> dict[str, float]:
    return {"from_lat": start[0], "from_lon": start[1], "to_lat": end[0], "to_lon": end[1]}


def test_route_api_returns_a_geojson_feature(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(valhalla, "route", fake_path)
    response = client.get("/api/route", params=route_params(SPLIT, NEARBY))
    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "Feature"
    assert body["geometry"]["type"] == "LineString"
    assert body["geometry"]["coordinates"] == [[16.42797, 43.503528], [16.4337, 43.5085]]
    assert body["properties"]["walk_minutes"] == 11.9
    assert body["properties"]["distance_m"] == 855
    assert {"source", "retrieved_at", "kind"} <= set(body["properties"])


def test_route_api_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    outside = client.get("/api/route", params=route_params((48.2, 16.37), NEARBY))
    assert outside.status_code == 422
    assert outside.json()["detail"] == "Lokacija nije u Hrvatskoj."

    too_far = client.get("/api/route", params=route_params(SPLIT, (45.8, 15.97)))
    assert too_far.status_code == 422

    monkeypatch.setattr(valhalla, "route", lambda *_: None)
    assert client.get("/api/route", params=route_params(SPLIT, NEARBY)).status_code == 404

    def down(*_: object) -> None:
        raise valhalla.RouterUnavailable("connection refused")

    monkeypatch.setattr(valhalla, "route", down)
    unavailable = client.get("/api/route", params=route_params(SPLIT, NEARBY))
    assert unavailable.status_code == 503
    assert unavailable.json()["detail"] == (
        "Put trenutačno nije moguće izračunati. Pokušajte ponovno."
    )


def test_route_is_in_the_openapi_description() -> None:
    assert "/api/route" in client.get("/api/openapi.json").json()["paths"]


def place(category: str, minutes: float | None, distance: float = 100.0) -> Place:
    return Place(
        category=category,
        name=f"{category} {minutes}",
        lat=45.0,
        lon=16.0,
        walk_minutes=minutes,
        distance_m=distance,
        source="test",
        retrieved_at=None,
        kind="modelled",
    )


def test_nearby_places_are_everything_within_15_minutes_and_the_three_nearest() -> None:
    reach = Reach(
        places={
            "grocery": [place("grocery", m) for m in (2, 5, 9, 12, 14.9, 16, 20)],
            "kindergarten": [place("kindergarten", m) for m in (31, 35, 40, 44)],
            "school": [place("school", 7)],
            "stop": [],
        }
    )
    nearby = reach.nearby(15.0)
    by_category: dict[str, list[float | None]] = {}
    for p in nearby:
        by_category.setdefault(p.category, []).append(p.walk_minutes)
    assert by_category == {
        "grocery": [2, 5, 9, 12, 14.9],
        "kindergarten": [31, 35, 40],
        "school": [7],
    }


def test_nearby_places_without_the_router_keep_the_nearest_by_distance() -> None:
    reach = Reach(places={"pharmacy": [place("pharmacy", None, d) for d in (50, 80, 90, 120)]})
    assert [p.distance_m for p in reach.nearby(15.0)] == [50, 80, 90]
