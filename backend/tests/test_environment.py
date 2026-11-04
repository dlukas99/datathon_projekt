import pytest

from analysis import environment
from analysis.environment import FloodReading


@pytest.mark.parametrize(
    ("pollutant", "value", "band", "status"),
    [
        ("pm25", 5.0, "vrlo niska", "good"),
        ("pm25", 10.0, "niska", "good"),
        ("pm25", 18.2, "umjerena", "info"),
        ("pm25", 25.0, "umjerena", "info"),
        ("pm25", 25.1, "visoka", "bad"),
        ("no2", 10.0, "vrlo niska", "good"),
        ("no2", 20.0, "niska", "good"),
        ("no2", 40.0, "umjerena", "info"),
        ("no2", 40.5, "visoka", "bad"),
    ],
)
def test_air_bands_follow_who_and_eu_limits(
    pollutant: str, value: float, band: str, status: str
) -> None:
    assert environment.air_band(pollutant, value) == (band, status)


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


@pytest.mark.parametrize(
    ("distance", "band", "status"),
    [
        (10, "Blizu prometnice", "warning"),
        (300, "Blizu prometnice", "warning"),
        (450, "Rub zone prometa", "info"),
        (800, "Podalje od prometnica", "good"),
    ],
)
def test_traffic_bands_follow_hei_zone(distance: float, band: str, status: str) -> None:
    assert environment.traffic_band(distance) == (band, status)


def test_flood_chance_over_a_30_year_loan() -> None:
    assert round(environment.flood_chance(100) * 100) == 26
    assert round(environment.flood_chance(10) * 100) == 96
    assert round(environment.flood_chance(500) * 100) == 6
