import time

import pytest

from app import pvgis


def fake_result() -> pvgis.SolarResult:
    return pvgis.SolarResult(1234.0, 35.0, 0.0, "TEST", "2005–2023", "2026-11-03T00:00:00+00:00")


def test_slow_answer_is_pending_then_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    def slow(lat: float, lon: float) -> pvgis.SolarResult:
        time.sleep(0.3)
        return fake_result()

    monkeypatch.setattr(pvgis, "_query", slow)
    with pytest.raises(pvgis.SolarPending):
        pvgis.yearly_output(40.001, 10.001, wait=0.05)
    time.sleep(0.5)
    assert pvgis.yearly_output(40.001, 10.001, wait=0.05).kwh_per_kwp_year == 1234.0


def test_failure_is_not_cached(monkeypatch: pytest.MonkeyPatch) -> None:
    def broken(lat: float, lon: float) -> pvgis.SolarResult:
        raise pvgis.SolarUnavailable("down")

    monkeypatch.setattr(pvgis, "_query", broken)
    with pytest.raises(pvgis.SolarUnavailable):
        pvgis.yearly_output(41.5, 11.5, wait=1.0)
    monkeypatch.setattr(pvgis, "_query", lambda lat, lon: fake_result())
    assert pvgis.yearly_output(41.5, 11.5, wait=1.0).optimal_slope_deg == 35.0
