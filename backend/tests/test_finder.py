import pandas as pd
import pytest

from app import finder


def row(
    name: str, pop: int, county: str, flood_status: str, air_band: str, kg: bool, **scores: float
) -> dict:  # type: ignore[type-arg]
    base = {
        "code": name,
        "name": name,
        "municipality": name,
        "county": county,
        "population": pop,
        "lon": 16.0,
        "lat": 45.0,
        "router_ok": True,
        "flood_status": flood_status,
        "air_band": air_band,
        "pm25": 12.0,
        "no2": 10.0,
        "tree_share": 20.0,
        "traffic_band": "Rub zone prometa",
        "burnt_areas": 0,
        "needs_15min": 5,
        "max_departures": None,
        "has_stops": True,
        "has_kindergarten": kg,
        "has_school": True,
        "has_doctor": True,
        "has_pediatrician": False,
        "has_pharmacy": True,
        "has_grocery": True,
        "has_park": False,
    }
    for c in finder.SCORED:
        base[f"score_{c}"] = scores.get(c, 50.0)
    return base


@pytest.fixture
def data(monkeypatch: pytest.MonkeyPatch) -> None:
    df = pd.DataFrame(
        [
            row("Aselo", 800, "A", "good", "niska", True, flood=100, air=80),
            row("Bgrad", 30000, "A", "bad", "umjerena", True, flood=0, air=50),
            row("Cmjesto", 5000, "B", "good", "umjerena", False, flood=100, air=50),
        ]
    )
    monkeypatch.setattr(finder, "profiles", lambda: df)


@pytest.mark.usefixtures("data")
def test_filters_and_ranking_are_deterministic() -> None:
    res = finder.find(finder.FindRequest())
    assert [r.name for r in res.results] == ["Aselo", "Cmjesto", "Bgrad"]
    res = finder.find(finder.FindRequest(must=["kindergarten"], avoid_flood=True))
    assert [r.name for r in res.results] == ["Aselo"]
    res = finder.find(finder.FindRequest(county="A", size="city"))
    assert [r.name for r in res.results] == ["Bgrad"]
    res = finder.find(finder.FindRequest(max_air="niska"))
    assert [r.name for r in res.results] == ["Aselo"]


@pytest.mark.usefixtures("data")
def test_results_explain_themselves() -> None:
    top = finder.find(finder.FindRequest()).results[0]
    assert top.reasons and top.reasons[0].startswith("Najjače:")
    assert any("poplavnom" in f for f in top.facts)


def test_parse_without_model_is_unavailable() -> None:
    with pytest.raises(finder.ParseUnavailable):
        finder.parse_question("mirno mjesto s vrtićem")
