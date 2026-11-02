import pytest

from analysis import environment
from analysis.environment import FloodReading


@pytest.mark.parametrize(
    ("pollutant", "value", "status"),
    [
        ("pm25", 5.0, "good"),
        ("pm25", 5.1, "warning"),
        ("pm25", 10.0, "warning"),
        ("pm25", 10.1, "bad"),
        ("no2", 10.0, "good"),
        ("no2", 20.0, "warning"),
        ("no2", 20.5, "bad"),
    ],
)
def test_air_status_uses_who_and_eu_thresholds(pollutant: str, value: float, status: str) -> None:
    assert environment._air_status(pollutant, value) == status


def _flood(monkeypatch: pytest.MonkeyPatch, readings: list[FloodReading] | None) -> str:
    monkeypatch.setattr(environment, "read_flood", lambda lon, lat: readings)
    return environment.flood_category(16.0, 45.0).status


def test_flood_status(monkeypatch: pytest.MonkeyPatch) -> None:
    dry = [FloodReading(rp, None, None) for rp in (10, 100, 500)]
    assert _flood(monkeypatch, dry) == "good"
    rp100 = [
        FloodReading(10, None, None),
        FloodReading(100, 0.4, 0.8),
        FloodReading(500, 1.0, 1.2),
    ]
    assert _flood(monkeypatch, rp100) == "bad"
    rp500 = [
        FloodReading(10, None, None),
        FloodReading(100, None, None),
        FloodReading(500, 0.3, 0.5),
    ]
    assert _flood(monkeypatch, rp500) == "warning"
    near = [FloodReading(10, None, None), FloodReading(100, None, 0.6)]
    near.append(FloodReading(500, None, 1.0))
    assert _flood(monkeypatch, near) == "warning"
    assert _flood(monkeypatch, None) == "no_data"
