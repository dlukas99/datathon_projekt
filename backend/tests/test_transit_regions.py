"""A new timetable (Šibenik) must leave Zagreb and Rijeka exactly as they were.

Values recorded on 9. 11. 2026. from the data before the Šibenik feed was added. Needs the
processed data and a running Valhalla, like the golden reports.
"""

from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.main import app


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

EXPECTED = {
    # Trg Stjepana Radića 1, Zagreb (ZET, HŽPP)
    (45.801219, 15.977114): {
        "car_free": {"needs_within_15min": 7, "needs_missing": "ništa"},
        "transit": {
            "stops_10min": 30,
            "stops_without_timetable_10min": 3,
            "max_departures_per_hour": 32.2,
        },
    },
    # Korzo 16, Rijeka (Autotrolej)
    (45.327014, 14.442312): {
        "car_free": {"needs_within_15min": 7, "needs_missing": "ništa"},
        "transit": {"stops_10min": 20, "max_departures_per_hour": 28.8},
    },
}


@pytest.fixture(scope="module")
def client() -> Any:
    with TestClient(app) as c:
        yield c


@pytest.mark.parametrize("point", list(EXPECTED), ids=["zagreb", "rijeka"])
def test_zagreb_and_rijeka_transit_unchanged(
    client: TestClient, point: tuple[float, float]
) -> None:
    lat, lon = point
    report = client.get("/api/report", params={"lat": lat, "lon": lon}).json()
    values = {c["id"]: {v["key"]: v["value"] for v in c["values"]} for c in report["categories"]}
    for cat_id, expected in EXPECTED[point].items():
        assert values[cat_id] == expected, cat_id
