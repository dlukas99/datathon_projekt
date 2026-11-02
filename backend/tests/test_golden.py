"""Compare reports for the demo addresses with their golden snapshots.

Needs processed data (`make data`) and the walking router (`make valhalla`);
skipped otherwise, e.g. in a fresh checkout.
"""

from __future__ import annotations

import json
import math
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app
from app.models import Report
from tests.golden import GOLDEN_DIR, demo_addresses, snapshot

MINUTES_TOLERANCE = 1.0


def _ready() -> str | None:
    if not (get_settings().processed_dir / "pois.parquet").exists():
        return "processed data missing (run `make data`)"
    try:
        httpx.get(f"{get_settings().valhalla_url}/status", timeout=3).raise_for_status()
    except httpx.HTTPError:
        return "Valhalla not running (run `make valhalla`)"
    return None


SKIP_REASON = _ready()
pytestmark = pytest.mark.skipif(SKIP_REASON is not None, reason=SKIP_REASON or "")


def _close(expected: Any, actual: Any, key: str) -> bool:
    numbers = isinstance(expected, float | int) and isinstance(actual, float | int)
    if numbers and not isinstance(expected, bool) and not isinstance(actual, bool):
        tol = MINUTES_TOLERANCE if key.startswith("nearest") else 0.05
        return math.isclose(float(expected), float(actual), abs_tol=tol)
    return bool(expected == actual)


@pytest.fixture(scope="module")
def client() -> Any:
    with TestClient(app) as c:
        yield c


@pytest.mark.parametrize("demo", demo_addresses(), ids=lambda d: str(d["id"]))
def test_demo_report_matches_golden(client: TestClient, demo: dict[str, Any]) -> None:
    response = client.get("/api/report", params={"lat": demo["lat"], "lon": demo["lon"]})
    assert response.status_code == 200
    actual = snapshot(Report.model_validate(response.json()))
    expected = json.loads((GOLDEN_DIR / f"{demo['id']}.json").read_text(encoding="utf-8"))
    assert actual["location"] == expected["location"]
    for cat_id, exp in expected["categories"].items():
        act = actual["categories"][cat_id]
        assert act["status"] == exp["status"], cat_id
        for key, value in exp["values"].items():
            assert _close(value, act["values"].get(key), key), f"{cat_id}.{key}"


def test_geojson_format(client: TestClient) -> None:
    demo = demo_addresses()[0]
    response = client.get(
        "/api/report", params={"lat": demo["lat"], "lon": demo["lon"], "format": "geojson"}
    )
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/geo+json")
    data = response.json()
    roles = {f["properties"]["role"] for f in data["features"]}
    assert {"location", "isochrone", "place"} <= roles
