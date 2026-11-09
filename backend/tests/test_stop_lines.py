"""Lines at stops without an open timetable (OSM route relations): facts, never frequencies."""

import pandas as pd
import pytest

from analysis.daily import car_free_category, transit_category
from analysis.walking import Reach
from app import stop_lines
from app.models import Place
from ingest.transit_lines import local_routes


def rows(*lines: tuple[str, str, str]) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "lon": [16.0] * len(lines),
            "lat": [45.0] * len(lines),
            "mode": [m for m, _, _ in lines],
            "ref": [r for _, r, _ in lines],
            "operator": [o for _, _, o in lines],
        }
    )


def test_lines_are_grouped_by_operator_and_mode_in_natural_order() -> None:
    text = stop_lines.describe(
        rows(
            ("bus", "8", "GPP Osijek"),
            ("tram", "2", "GPP Osijek"),
            ("bus", "10", "GPP Osijek"),
            ("tram", "1", "GPP Osijek"),
            ("bus", "3", "GPP Osijek"),
            ("bus", "21", "Promet Split"),
        )
    )
    assert text == "tramvaj 1 i 2, autobus 3, 8 i 10 (GPP Osijek); autobus 21 (Promet Split)"


def test_a_line_without_operator_repeating_a_named_one_is_not_repeated() -> None:
    text = stop_lines.describe(rows(("bus", "7", "Promet Split"), ("bus", "7", "")))
    assert text == "autobus 7 (Promet Split)"


def test_long_lists_are_cut() -> None:
    text = stop_lines.describe(rows(*[("bus", str(i), "ZET") for i in range(1, 14)]))
    assert text == "autobus 1, 2, 3, 4, 5, 6, 7, 8, 9, 10 i još 3 (ZET)"


def stop(lat: float, lon: float, detail: str) -> Place:
    return Place(
        category="stop",
        name="test",
        lat=lat,
        lon=lon,
        walk_minutes=3,
        distance_m=100,
        source="osm",
        retrieved_at=None,
        kind="modelled",
        detail=detail,
    )


def test_lines_at_matches_stops_within_30_m(monkeypatch: pytest.MonkeyPatch) -> None:
    table = rows(("tram", "2", "GPP Osijek"), ("bus", "4", "GPP Osijek"))
    table.loc[1, "lat"] = 45.001  # about 110 m away: another stop
    monkeypatch.setattr(stop_lines, "_table", lambda: table)
    assert stop_lines.lines_at([stop(45.0001, 16.0, "tram")]) == "tramvaj 2 (GPP Osijek)"
    assert stop_lines.lines_at([stop(46.0, 16.0, "bus")]) is None


def test_only_local_routes_are_kept() -> None:
    town = {i: (45.55 + i * 0.002, 18.69) for i in range(6)}  # six stops, about 1 km
    far = {
        10: (45.55, 18.69),
        11: (45.7, 18.9),
        12: (45.9, 19.0),
        13: (46.0, 19.1),
        14: (46.1, 19.2),
    }
    routes = [
        ({"route": "tram", "ref": "2", "operator": "GPP Osijek"}, list(range(6))),
        ({"route": "bus", "ref": "N949", "operator": "Flixbus"}, [10, 11, 12, 13, 14]),  # > 30 km
        ({"route": "bus", "ref": "950", "operator": "Flixbus"}, [0, 1]),  # 2 mapped stops
        ({"route": "bus", "ref": "", "operator": "X"}, list(range(6))),  # no line number
        ({"route": "bus", "ref": "1", "network": "hr:Liburnija Zadar"}, list(range(6))),
    ]
    out = local_routes(routes, {**town, **far})
    assert set(zip(out["ref"], out["operator"], strict=True)) == {
        ("2", "GPP Osijek"),
        ("1", "Liburnija Zadar"),
    }
    assert len(out["ref"]) == 12


def lines(_: list[Place]) -> str:
    return "tramvaj 1 i 2 (GPP Osijek)"


def test_cards_name_the_lines_where_the_frequency_is_unknown() -> None:
    reach = Reach(places={"stop": [stop(45.0, 16.0, "tram"), stop(45.0, 16.0, "train|0.57|x")]})
    transit = transit_category(reach, has_timetables=True, lines_for=lines)
    assert transit.headline.endswith(
        "Prema OpenStreetMapu ondje staju: tramvaj 1 i 2 (GPP Osijek); koliko često voze, "
        "nije javno objavljeno."
    )
    assert {v.key: v.value for v in transit.values}["lines_without_timetable"] == (
        "tramvaj 1 i 2 (GPP Osijek)"
    )
    car_free = car_free_category(reach, lines_for=lines)
    assert "Prema OpenStreetMapu ondje staju: tramvaj 1 i 2" in car_free.headline


def test_no_lines_where_a_timetable_already_answers() -> None:
    reach = Reach(places={"stop": [stop(45.0, 16.0, "tram|12.0|x"), stop(45.0, 16.0, "bus")]})
    transit = transit_category(reach, has_timetables=True, lines_for=lines)
    assert "OpenStreetMapu" not in transit.headline
    assert "lines_without_timetable" not in {v.key for v in transit.values}
    car_free = car_free_category(reach, lines_for=lines)
    assert "OpenStreetMapu" not in car_free.headline


def test_one_operator_under_several_spellings_is_one() -> None:
    text = stop_lines.describe(
        rows(
            ("bus", "2", "Pulapromet d.o.o."),
            ("bus", "28", "pulapromet"),
            ("bus", "25b", "Pula promet"),
            ("bus", "22", "Pulapromet d.o.o."),
        )
    )
    assert text == "autobus 2, 22, 25b i 28 (Pulapromet d.o.o.)"
