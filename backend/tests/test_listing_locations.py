"""Index Oglasi location ids for listing links (ingest/listing_locations.py)."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from ingest.listing_locations import (
    OUTPUT,
    county_slug,
    load,
    municipality_name,
    parse_route,
    plan,
    save,
    slugify,
)

SPLIT_ID = "52eb9db8-6dc1-4ed5-acf7-e1669df05240"
UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$")


@pytest.mark.parametrize(
    ("name", "slug"),
    [
        ("Đakovo", "dakovo"),
        ("Šibenik", "sibenik"),
        ("Čakovec", "cakovec"),
        ("Mali Lošinj", "mali-losinj"),
        ("Ivanić-Grad", "ivanic-grad"),
        ("Grad Zagreb", "grad-zagreb"),
        ("Murter - Kornati", "murter-kornati"),
        ("Splitsko-dalmatinska županija", "splitsko-dalmatinska-zupanija"),
        ("  Đurđevac  ", "durdevac"),
        ("Sv. Filip i Jakov", "sv-filip-i-jakov"),
    ],
)
def test_slugify_matches_frontend_rules(name: str, slug: str) -> None:
    assert slugify(name) == slug


def test_istrian_bilingual_names_use_the_croatian_part() -> None:
    istria = "Istarska županija"
    assert municipality_name("Pula - Pola", istria) == "Pula"
    assert municipality_name("Kaštelir-Labinci - Castelliere-S. Domenica", istria) == (
        "Kaštelir-Labinci"
    )
    assert municipality_name("Murter - Kornati", "Šibensko-kninska županija") == "Murter - Kornati"


def test_county_slug_has_no_suffix() -> None:
    assert county_slug("Splitsko-dalmatinska županija") == "splitsko-dalmatinska"
    assert county_slug("Grad Zagreb") == "grad-zagreb"


def test_plan_skips_names_shared_by_several_counties() -> None:
    rows = [
        {"level": "municipality", "name": "Split", "parent_name": "Splitsko-dalmatinska županija"},
        {"level": "municipality", "name": "Otok", "parent_name": "Splitsko-dalmatinska županija"},
        {"level": "municipality", "name": "Otok", "parent_name": "Vukovarsko-srijemska županija"},
        {"level": "municipality", "name": "Novigrad", "parent_name": "Zadarska županija"},
        {
            "level": "municipality",
            "name": "Novigrad - Cittanova",
            "parent_name": "Istarska županija",
        },
        {"level": "municipality", "name": "Grad Zagreb", "parent_name": "Grad Zagreb"},
        {"level": "county", "name": "Grad Zagreb", "parent_name": ""},
        {"level": "county", "name": "Splitsko-dalmatinska županija", "parent_name": ""},
        {"level": "settlement", "name": "Nerezine", "parent_name": "Mali Lošinj"},
    ]
    slugs, ambiguous = plan(rows)
    assert slugs == ["grad-zagreb", "split", "splitsko-dalmatinska"]
    assert ambiguous == ["Novigrad", "Novigrad - Cittanova", "Otok"]


def test_parse_route_reads_city_and_county_ids() -> None:
    city = [
        {
            "H1": "Prodaja stanova Split",
            "searchQuery": "%7B%22category%22%3A%22prodaja-stanova%22%2C%22module%22%3A%22"
            "nekretnine%22%2C%22sortOption%22%3A4%2C%22includeCityIds%22%3A%5B%22"
            f"{SPLIT_ID}%22%5D%7D",
        }
    ]
    assert parse_route(city) == {"type": "city", "id": SPLIT_ID}
    county = [{"searchQuery": '{"includeCountyIds":["191f5ede-cf31-4c40-b353-257a9061462e"]}'}]
    assert parse_route(county) == {"type": "county", "id": "191f5ede-cf31-4c40-b353-257a9061462e"}
    assert parse_route([{}]) is None
    with pytest.raises(ValueError):
        parse_route("Bad request")


def test_save_round_trip_is_sorted(tmp_path: Path) -> None:
    path = tmp_path / "locations.json"
    save(
        {
            "updated": "2026-11-05",
            "ambiguous_municipalities": ["Otok", "Novigrad"],
            "index_oglasi": {
                "split": {"type": "city", "id": SPLIT_ID},
                "bale": {"type": "city", "id": SPLIT_ID},
            },
            "index_oglasi_not_found": ["b", "a", "a"],
        },
        path,
    )
    data = load(path)
    assert list(data["index_oglasi"]) == ["bale", "split"]
    assert data["ambiguous_municipalities"] == ["Novigrad", "Otok"]
    assert data["index_oglasi_not_found"] == ["a", "b"]


def test_committed_file_is_well_formed() -> None:
    data = load(OUTPUT)
    assert data["index_oglasi"], "config/listing_locations.json has no Index locations"
    for slug, location in data["index_oglasi"].items():
        assert slug == slugify(slug)
        assert location["type"] in {"city", "county"}
        assert UUID.match(location["id"]), slug
    assert data["index_oglasi"]["split"] == {"type": "city", "id": SPLIT_ID}
    assert {"Otok", "Privlaka", "Sveta Nedelja"} <= set(data["ambiguous_municipalities"])
    assert not set(data["index_oglasi"]) & set(data["index_oglasi_not_found"])
