import pytest

from app.geocode import Geocoder, Suggestion, normalize, number_key

ROWS: dict[str, list[str] | list[float]] = {
    "street": [
        "Ulica Đure Šimića",
        "Ulica Đure Šimića",
        "Ilica",
        "Ilica",
        "Trg kralja Tomislava",
        "Banjol",
        "Banjol",
        "1. ulica",
        "1. ulica",
        "Drinska",
        "Ulica 1. svibnja",
    ],
    "housenumber": ["1", "12A", "1", "191E", "4", "10", "12", "25", "25/2", "12B", "3"],
    "place": [
        "Testno",
        "Testno",
        "Zagreb",
        "Zagreb",
        "Testno",
        "Banjol",
        "Banjol",
        "Blato",
        "Blato",
        "Osijek",
        "Testno",
    ],
    "postcode": [
        "49000",
        "49000",
        "10000",
        "10000",
        "49000",
        "51280",
        "51280",
        "20271",
        "20271",
        "31000",
        "49000",
    ],
    "settlement_code": ["T", "T", "Z", "Z", "T", "B", "B", "BL", "BL", "O", "T"],
    "lon": [16.0, 16.001, 15.97, 15.94, 16.01, 14.78, 14.781, 16.79, 16.791, 18.69, 16.02],
    "lat": [45.0, 45.001, 45.81, 45.81, 45.01, 44.75, 44.751, 42.93, 42.931, 45.55, 45.02],
    "source": ["test"] * 11,
}
MUNICIPALITIES = {"T": "Općina Test", "Z": "Grad Zagreb", "B": "Rab", "BL": "Blato", "O": "Osijek"}


def settlement(name: str, municipality: str) -> Suggestion:
    return Suggestion(
        label=f"{name}, {municipality}", lat=45.0, lon=16.0, kind="settlement", source="test"
    )


def make() -> Geocoder:
    settlements = [
        settlement("Testno", "Općina Test"),
        settlement("Zagreb", "Grad Zagreb"),
        settlement("Banjol", "Rab"),
        settlement("Blato", "Blato"),
        settlement("Osijek", "Osijek"),
    ]
    return Geocoder.from_rows(ROWS, settlements, MUNICIPALITIES)


def first(query: str) -> Suggestion:
    results = make().search(query)
    assert results, query
    return results[0]


def test_normalize_strips_diacritics() -> None:
    assert normalize("Ulica Đ. Šimića") == "ulica d simica"
    assert normalize("Djure") == normalize("Đure") == "dure"


@pytest.mark.parametrize(
    ("written", "key"),
    [
        ("12", "12"),
        ("12A", "12a"),
        ("12 a", "12a"),
        ("12/B", "12b"),
        ("25 / 2", "25/2"),
        ("12A/1", "12a/1"),
    ],
)
def test_house_number_keys(written: str, key: str) -> None:
    assert number_key(written) == key


@pytest.mark.parametrize(
    ("query", "label"),
    [
        ("ulica dure simica 12A", "Ulica Đure Šimića 12A, Testno"),
        ("Đure Šimića 12 a, Testno", "Ulica Đure Šimića 12A, Testno"),
        ("Drinska 12/B, Osijek", "Drinska 12B, Osijek"),
        ("Drinska 12 b Osijek", "Drinska 12B, Osijek"),
        ("1. ulica 25/2, Blato", "1. ulica 25/2, Blato"),
        ("Ilica 1 Zagreb", "Ilica 1, Zagreb"),
        ("Ilica 1, 10000 Zagreb, Hrvatska", "Ilica 1, Zagreb"),
        ("Ilica 1, Grad Zagreb", "Ilica 1, Zagreb"),
        ("Banjol 10, Rab", "Banjol 10, Banjol"),
        ("Banjol 12, 51280", "Banjol 12, Banjol"),
        ("Ulica 1. svibnja 3", "Ulica 1. svibnja 3, Testno"),
    ],
)
def test_addresses_written_the_way_people_write_them(query: str, label: str) -> None:
    found = first(query)
    assert (found.label, found.kind, found.note) == (label, "address", None)


def test_prefix_tokens_and_place_filter() -> None:
    results = make().search("ilica 191e, zag")
    assert [r.label for r in results] == ["Ilica 191E, Zagreb"]


def test_street_without_number() -> None:
    found = first("trg kralja")
    assert (found.kind, found.label) == ("street", "Trg kralja Tomislava, Testno")


def test_number_in_the_street_name_stays_in_the_street() -> None:
    found = first("Ulica 1. svibnja")
    assert (found.kind, found.label) == ("street", "Ulica 1. svibnja, Testno")


def test_street_and_town_without_comma() -> None:
    found = first("Ilica Zagreb")
    assert (found.kind, found.label) == ("street", "Ilica, Zagreb")


def test_settlement_suggestion() -> None:
    assert first("testn").kind == "settlement"


def test_missing_house_number_offers_the_street_and_says_so() -> None:
    found = first("Ilica 999")
    assert (found.kind, found.label) == ("street", "Ilica, Zagreb")
    assert found.note == "Kućni broj 999 nije u registru adresa; prikazana je sredina ulice."


def test_missing_letter_offers_the_number_without_it() -> None:
    found = first("Ilica 1b, Zagreb")
    assert (found.kind, found.label) == ("address", "Ilica 1, Zagreb")
    assert found.note == "Kućni broj 1B nije u registru adresa; prikazan je broj 1."


def test_village_without_streets_falls_back_to_its_centre() -> None:
    found = first("Banjol 161")
    assert (found.kind, found.label) == ("settlement", "Banjol, Rab")
    assert found.note is not None and "središte naselja" in found.note


def test_bb_gives_the_street_with_a_note() -> None:
    found = first("Ilica bb, Zagreb")
    assert (found.kind, found.label) == ("street", "Ilica, Zagreb")
    assert found.note is not None and "(bb)" in found.note


def test_unknown_street_in_a_known_place_gives_the_settlement() -> None:
    found = first("Nepostojeća 5, Testno")
    assert (found.kind, found.label) == ("settlement", "Testno, Općina Test")
    assert found.note == "Ulica nije pronađena u registru adresa; prikazano je središte naselja."


def test_other_form_of_a_street_name_is_found_and_named() -> None:
    found = first("Đure Šimićeva 1, Testno")
    assert (found.kind, found.label) == ("address", "Ulica Đure Šimića 1, Testno")
    assert found.note == "Ulica je u registru adresa upisana kao „Ulica Đure Šimića”."


def test_nothing_for_nonsense() -> None:
    assert make().search("qwxz 5") == []
