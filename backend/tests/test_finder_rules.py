"""The profile rules of "Predloži mjesto": tests check the RULES, not particular towns."""

import json
from typing import Any

import pandas as pd
import pytest

from app import finder
from app import finder_rules as fr
from app.config import get_settings

NEEDS = ("kindergarten", "school", "doctor", "pediatrician", "pharmacy", "grocery")


def place(
    name: str,
    *,
    pop: int = 5000,
    services: tuple[str, ...] = NEEDS,
    higher_ed: list[dict[str, Any]] | None = None,
    stops: bool = True,
    hospital_km: float | None = 5.0,
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "code": name,
        "name": name,
        "municipality": name,
        "county": "A",
        "population": pop,
        "lon": 16.0,
        "lat": 45.0,
        "router_ok": True,
        "flood_status": "good",
        "air_band": "niska",
        "pm25": 8.0,
        "no2": 10.0,
        "tree_share": 20.0,
        "traffic_band": "Podalje od prometnica",
        "burnt_areas": 0,
        "needs_15min": len(services),
        "max_departures": None,
        "has_stops": stops,
        "has_park": "park" in services,
        "has_playground": "playground" in services,
        "higher_ed": json.dumps(higher_ed or []),
        "hospital_km": hospital_km,
        "hospital_name": "Opća bolnica" if hospital_km is not None else None,
    }
    for need in (*NEEDS, "park", "playground"):
        row[f"has_{need}"] = need in services
        row[f"min_{need}"] = 6.0 if need in services else 25.0
    for c in finder.SCORED:
        row[f"score_{c}"] = 70.0
    return row


def he(name: str, km: float, programmes: int) -> dict[str, Any]:
    return {
        "code": name,
        "name": name,
        "km": km,
        "programmes": programmes,
        "institutions": 1,
        "example": f"Sveučilište u {name}",
    }


UNI = [he("Unigrad", 0.0, 150)]
SUBURB = [he("Unigrad", 8.0, 150)]
FAR = [he("Unigrad", 30.0, 150)]
SMALL_NEAR = [he("Malomjesto", 5.0, 3)]


@pytest.fixture
def towns(monkeypatch: pytest.MonkeyPatch) -> pd.DataFrame:
    df = pd.DataFrame(
        [
            place("Unigrad", pop=80000, higher_ed=UNI),
            place("Predgrađe", higher_ed=SUBURB),
            place("Predgrađe bez busa", higher_ed=SUBURB, stops=False),
            place("Daleko", higher_ed=FAR),
            place("Kraj malog učilišta", higher_ed=SMALL_NEAR),
            place("Bez ljekarne", services=("grocery", "doctor", "kindergarten", "school")),
            place("Bez vrtića", services=("grocery", "doctor", "pharmacy", "school")),
            place("Bez trgovine", services=("doctor", "pharmacy", "kindergarten", "school")),
            place("Selo", pop=400, services=("grocery",)),
        ]
    )
    monkeypatch.setattr(finder, "profiles", lambda: df)
    return df


def _rows(df: pd.DataFrame) -> dict[str, pd.Series]:
    return {str(r["name"]): r for _, r in df.iterrows()}


def strict(profile: str, **kw: Any) -> list[finder.FindResult]:
    res = finder.find(finder.FindRequest(profile=profile, limit=30, **kw))
    return [r for r in res.results if not r.relaxed]


def test_every_profile_has_rules_and_known_checks() -> None:
    profiles = fr.rules()["profiles"]
    assert set(profiles) == {"opci", "obitelj", "umirovljenik", "student", "rad-od-kuce"}
    row = pd.Series(place("X", higher_ed=UNI))
    for rules in profiles.values():
        assert rules["summary"] and rules["rationale"]
        for req in rules["requires"]:
            assert fr.check_requirement(req, row).text
        for c in rules["criteria"]:
            assert c["weight"] > 0
            assert fr.criterion_score(c["id"], row) is not None


def test_student_proposals_have_studies_within_reach(towns: pd.DataFrame) -> None:
    rows = _rows(towns)
    cfg = fr.rules()["higher_ed"]
    results = strict("student")
    assert results
    for r in results:
        hits = fr.higher_ed_places(rows[r.name])
        own = any(p["km"] == 0 for p in hits)
        reach = any(
            p["km"] <= cfg["max_km"] and p["programmes"] >= cfg["reach_min_programmes"]
            for p in hits
        )
        assert own or (reach and bool(rows[r.name]["has_stops"])), r.name
        assert any(m.startswith("Studiji") for m in r.met)
    names = {r.name for r in results}
    assert not names & {"Predgrađe bez busa", "Daleko", "Kraj malog učilišta", "Selo"}


def test_a_university_town_outranks_its_suburb(towns: pd.DataFrame) -> None:
    names = [r.name for r in strict("student")]
    assert names.index("Unigrad") < names.index("Predgrađe")
    suburb = next(r for r in strict("student") if r.name == "Predgrađe")
    assert any("km zračne linije" in m and "stajalište" in m for m in suburb.met)


def test_retiree_proposals_have_shop_pharmacy_and_doctor_on_foot(towns: pd.DataFrame) -> None:
    rows = _rows(towns)
    results = strict("umirovljenik")
    assert results
    for r in results:
        for need in ("grocery", "pharmacy", "doctor"):
            assert rows[r.name][f"has_{need}"], (r.name, need)
        assert len(r.met) == 3
    assert "Bez ljekarne" not in {r.name for r in results}


def test_family_proposals_have_kindergarten_and_school_on_foot(towns: pd.DataFrame) -> None:
    rows = _rows(towns)
    results = strict("obitelj")
    assert results
    for r in results:
        assert rows[r.name]["has_kindergarten"] and rows[r.name]["has_school"]
    assert "Bez vrtića" not in {r.name for r in results}


@pytest.mark.parametrize("profile", ["opci", "rad-od-kuce"])
def test_general_profiles_need_a_shop_on_foot(towns: pd.DataFrame, profile: str) -> None:
    rows = _rows(towns)
    results = strict(profile)
    assert results
    assert all(rows[r.name]["has_grocery"] for r in results)
    assert "Bez trgovine" not in {r.name for r in results}


def test_met_requirements_carry_their_values(towns: pd.DataFrame) -> None:
    r = strict("umirovljenik")[0]
    assert any("6 minuta hoda" in m for m in r.met)


def test_too_few_strict_results_are_filled_with_one_missing_and_flagged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    df = pd.DataFrame(
        [
            place("Sve ima"),
            place("Bez ljekarne", services=("grocery", "doctor")),
            place("Samo trgovina", services=("grocery",)),
        ]
    )
    monkeypatch.setattr(finder, "profiles", lambda: df)
    res = finder.find(finder.FindRequest(profile="umirovljenik"))
    assert res.matching == 1
    assert res.relaxed_note
    assert [(r.name, r.relaxed) for r in res.results] == [
        ("Sve ima", False),
        ("Bez ljekarne", True),
    ]
    flagged = res.results[1]
    assert any("ljekarne" in m for m in flagged.missing)


def test_enough_strict_results_show_no_relaxed_places(monkeypatch: pytest.MonkeyPatch) -> None:
    df = pd.DataFrame(
        [place(f"Mjesto {i}") for i in range(6)] + [place("Bez", services=("grocery",))]
    )
    monkeypatch.setattr(finder, "profiles", lambda: df)
    res = finder.find(finder.FindRequest(profile="umirovljenik", limit=30))
    assert res.relaxed_note is None
    assert not any(r.relaxed for r in res.results)


def test_programme_score_grows_with_choice_and_suburbs_count_less() -> None:
    assert fr.programme_score(1) < fr.programme_score(10) < fr.programme_score(150)
    assert fr.programme_score(10_000) == 100.0
    own = fr.reach_score(he("A", 0.0, 150))
    near = fr.reach_score(he("A", 5.0, 150))
    farther = fr.reach_score(he("A", 14.0, 150))
    assert own > near > farther > 0


REAL = get_settings().processed_dir / "settlement_facilities.parquet"


@pytest.mark.skipif(not REAL.exists(), reason="needs processed data (make data)")
@pytest.mark.parametrize("profile", ["opci", "obitelj", "umirovljenik", "student", "rad-od-kuce"])
def test_real_data_top_proposals_follow_the_rules(profile: str) -> None:
    finder.profiles.cache_clear()
    rows = {str(r["code"]): r for _, r in finder.profiles().iterrows()}
    rules = fr.profile_rules(profile)
    for county in (None, "Osječko-baranjska županija"):
        res = finder.find(finder.FindRequest(profile=profile, county=county, limit=10))
        assert res.results
        for r in res.results:
            failed = [q for q in rules["requires"] if not fr.check_requirement(q, rows[r.code]).ok]
            assert len(failed) == (1 if r.relaxed else 0), (profile, r.name, failed)
