"""Karta Hrvatske: geometry encoding, the indicator table and what a click hits."""

from __future__ import annotations

import json
from collections.abc import Iterator

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from shapely import STRtree
from shapely.geometry import Polygon, box

from app import map_layer
from app.config import get_settings
from app.geo import to_htrs, to_wgs84
from app.main import app
from tests.test_finder import row


def decode(rings: list[list[int]], step: float) -> list[list[tuple[float, float]]]:
    out = []
    for ring in rings:
        x = y = 0
        pts = []
        for i in range(0, len(ring), 2):
            x += ring[i]
            y += ring[i + 1]
            pts.append((round(x * step, 6), round(y * step, 6)))
        out.append(pts)
    return out


def test_rings_are_delta_encoded_and_round_trip() -> None:
    poly = Polygon(
        [(15.0, 45.0), (15.01, 45.0), (15.01, 45.01), (15.0, 45.01), (15.0, 45.0)],
        holes=[[(15.002, 45.002), (15.004, 45.002), (15.004, 45.004), (15.002, 45.002)]],
    )
    encoded = map_layer.encode_rings(poly, 1e-3)
    assert len(encoded) == 1 and len(encoded[0]) == 2
    outer = decode(encoded[0], 1e-3)[0]
    assert outer[0] == (15.0, 45.0)
    assert outer[2] == (15.01, 45.01)
    assert outer[-1] == outer[0]
    # Deltas after the first point stay small.
    assert max(abs(v) for v in encoded[0][0][2:]) <= 10


def test_tiny_rings_are_dropped() -> None:
    tiny = box(15.0, 45.0, 15.0002, 45.0002)
    assert map_layer.encode_rings(tiny, 1e-3) == []


@pytest.fixture
def profiles(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    a = row("000001", 800, "A", "good", "niska", True, flood=100, air=80)
    b = row("000002", 3000, "A", "bad", "visoka", False, flood=0, air=10)
    b["router_ok"] = False
    b["max_departures"] = 3.5
    df = pd.DataFrame([a, b])
    monkeypatch.setattr(map_layer, "profiles", lambda: df)
    map_layer.table.cache_clear()
    map_layer.table_json.cache_clear()
    map_layer.profiled_codes.cache_clear()
    yield
    map_layer.table.cache_clear()
    map_layer.table_json.cache_clear()
    map_layer.profiled_codes.cache_clear()


@pytest.mark.usefixtures("profiles")
def test_table_has_scores_for_every_map_profile() -> None:
    t = map_layer.table()
    first, second = t.rows
    assert first.id == 1 and first.air == "niska" and first.flood == "good"
    assert set(first.scores) == set(map_layer.MAP_PROFILES)
    assert all(isinstance(v, int) for v in first.scores.values())
    assert first.scores["opci"] > second.scores["opci"]  # type: ignore[operator]
    # Without the walking router the walking values are unknown, not zero.
    assert second.needs is None and second.departures is None and second.stops is False
    assert set(t.sources) == {"score", "air", "flood", "needs", "transit"}


def _fake_settlements() -> map_layer.Settlements:
    # One square settlement of 4 x 4 km around a point in Slavonia (EPSG:3765).
    cx, cy = to_htrs(18.0, 45.3)
    square = box(cx - 2000, cy - 2000, cx + 2000, cy + 2000)
    geoms = np.array([square])
    return map_layer.Settlements(
        codes=["000001"],
        names=["Aselo"],
        municipalities=["Aopćina"],
        county_of=["A"],
        geoms=geoms,
        tree=STRtree(geoms),
        centre={"000001": (18.0, 45.3)},
        population={"000001": 800},
    )


@pytest.fixture
def fake_world(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(map_layer, "settlements", _fake_settlements)
    monkeypatch.setattr(map_layer, "profiled_codes", lambda: frozenset({"000001"}))
    cx, cy = to_htrs(18.0, 45.3)
    # House numbers only near the centre.
    monkeypatch.setattr(
        map_layer,
        "address_cells",
        lambda: np.unique(map_layer._cell_keys(np.array([cx]), np.array([cy]))),
    )
    tags = [map_layer.PointTag(id="air", title="Kvaliteta zraka", text="Dobar", status="good")]
    monkeypatch.setattr(map_layer, "_at_point", lambda lon, lat: tags)


@pytest.mark.usefixtures("fake_world")
def test_click_in_the_populated_part_shows_the_settlement() -> None:
    p = map_layer.point(45.3, 18.0)
    assert p.kind == "settlement" and p.name == "Aselo" and p.profiled
    assert p.populated and p.centre_km == 0.0 and p.at_point == []


@pytest.mark.usefixtures("fake_world")
def test_click_outside_the_populated_part_names_the_settlement_and_distance() -> None:
    cx, cy = to_htrs(18.0, 45.3)
    lon, lat = to_wgs84(cx + 1500, cy)
    p = map_layer.point(lat, lon)
    assert p.kind == "settlement" and p.name == "Aselo"
    assert not p.populated
    assert p.centre_km == pytest.approx(1.5, abs=0.1)
    assert [t.id for t in p.at_point] == ["air"]


@pytest.mark.usefixtures("fake_world")
def test_click_on_water_or_abroad(monkeypatch: pytest.MonkeyPatch) -> None:
    cx, cy = to_htrs(18.0, 45.3)
    lon, lat = to_wgs84(cx + 10000, cy)
    monkeypatch.setattr(map_layer, "landcover_at", lambda lon, lat: 80)
    assert map_layer.point(lat, lon).kind == "sea"
    monkeypatch.setattr(map_layer, "landcover_at", lambda lon, lat: 10)
    assert map_layer.point(lat, lon).kind == "outside"
    # Far outside the bounding box of Croatia, nothing is read at all.
    out = map_layer.point(48.2, 16.37)
    assert out.kind == "outside" and out.message == map_layer.OUTSIDE_MESSAGE


@pytest.mark.usefixtures("fake_world")
def test_click_just_off_a_simplified_boundary_still_hits_land(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(map_layer, "landcover_at", lambda lon, lat: 40)
    cx, cy = to_htrs(18.0, 45.3)
    lon, lat = to_wgs84(cx + 2100, cy)
    assert map_layer.point(lat, lon).name == "Aselo"


# --- Real data (skipped in a fresh checkout) --------------------------------------------

REAL = (get_settings().processed_dir / "admin_units.parquet").exists() and (
    get_settings().processed_dir / "settlement_profiles.parquet"
).exists()


@pytest.mark.skipif(not REAL, reason="processed data missing (run `make data`)")
def test_three_kinds_of_clicks_on_real_data() -> None:
    town = map_layer.point(45.2883, 18.8047)  # Vinkovci, town centre
    assert town.kind == "settlement" and town.name == "Vinkovci" and town.populated
    assert town.profiled
    sea = map_layer.point(43.45, 16.40)  # Brač channel off Split
    assert sea.kind == "sea"
    abroad = map_layer.point(46.05, 14.505)  # Ljubljana
    assert abroad.kind == "outside"


@pytest.mark.skipif(not REAL, reason="processed data missing (run `make data`)")
def test_map_endpoints_are_compressed_and_complete() -> None:
    client = TestClient(app)
    res = client.get("/api/map/geometry/overview", headers={"Accept-Encoding": "gzip"})
    assert res.status_code == 200
    assert res.headers["content-encoding"] == "gzip"
    assert int(res.headers["content-length"]) < 400_000
    data = res.json()
    assert len(data["features"]) > 6000
    table = client.get("/api/map/settlements").json()
    assert len(table["rows"]) > 2000
    ids = {f[0] for f in data["features"]}
    assert all(r["id"] in ids for r in table["rows"])
    res = client.get("/api/map/geometry/overview", headers={"Accept-Encoding": "identity"})
    assert "content-encoding" not in res.headers
    assert json.loads(res.content)["step"] == pytest.approx(1e-3)
    assert client.get("/api/map/point", params={"lat": 43.45, "lon": 16.40}).json()["kind"] == "sea"
