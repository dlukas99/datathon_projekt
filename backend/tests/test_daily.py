from analysis.daily import car_free_category, transit_category
from analysis.walking import Reach
from app.models import Place


def place(category: str, minutes: float | None, detail: str | None = None) -> Place:
    return Place(
        category=category,
        name="test",
        lat=45.0,
        lon=16.0,
        walk_minutes=minutes,
        distance_m=100,
        source="test",
        retrieved_at=None,
        kind="modelled",
        detail=detail,
    )


def reach_with(**places: list[Place]) -> Reach:
    return Reach(places=dict(places))


def test_car_free_counts_needs_within_15_minutes() -> None:
    reach = reach_with(
        grocery=[place("grocery", 4)],
        pharmacy=[place("pharmacy", 16)],
        doctor=[place("doctor", 9)],
        kindergarten=[place("kindergarten", 12)],
        school=[place("school", 14.9)],
        park=[place("park", 2)],
        stop=[place("stop", 3, "bus|4.5|2026-11-04")],
    )
    cat = car_free_category(reach)
    assert cat.values[0].value == 6
    assert "ljekarna" in cat.headline


def test_stop_without_timetable_is_not_counted_as_missing() -> None:
    reach = reach_with(stop=[place("stop", 3, "bus")])
    cat = car_free_category(reach)
    assert "Nije provjereno" in cat.headline
    assert "stajalište" not in cat.values[1].display


def test_infrequent_stop_is_missing() -> None:
    reach = reach_with(stop=[place("stop", 3, "bus|0.5|2026-11-04")])
    cat = car_free_category(reach)
    assert "stajalište" in cat.values[1].display


def test_transit_reports_best_stop() -> None:
    reach = reach_with(
        stop=[place("stop", 3, "tram|12.0|2026-11-04"), place("stop", 8, "bus|2.0|2026-11-04")]
    )
    cat = transit_category(reach, has_timetables=True)
    assert cat.values[1].value == 12.0
    assert "nalaze se 2 stajališta" in cat.headline
