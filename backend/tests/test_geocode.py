from app.geocode import Geocoder, Suggestion, normalize

ROWS: dict[str, list[str] | list[float]] = {
    "street": ["Ulica Đure Šimića", "Ulica Đure Šimića", "Ilica", "Ilica", "Trg kralja Tomislava"],
    "housenumber": ["1", "12a", "1", "191E", "4"],
    "place": ["Testno", "Testno", "Zagreb", "Zagreb", "Testno"],
    "lon": [16.0, 16.001, 15.97, 15.94, 16.01],
    "lat": [45.0, 45.001, 45.81, 45.81, 45.01],
    "source": ["test"] * 5,
}


def make() -> Geocoder:
    settlements = [
        Suggestion(
            label="Testno, Općina Test", lat=45.0, lon=16.0, kind="settlement", source="test"
        )
    ]
    return Geocoder.from_rows(ROWS, settlements)


def test_normalize_strips_diacritics() -> None:
    assert normalize("Ulica Đ. Šimića") == "ulica d simica"
    assert normalize("Djure") == normalize("Đure") == "dure"


def test_exact_address_with_letter() -> None:
    results = make().search("ulica dure simica 12A")
    assert results[0].label == "Ulica Đure Šimića 12A, Testno"
    assert results[0].kind == "address"


def test_prefix_tokens_and_place_filter() -> None:
    results = make().search("ilica 191e, zag")
    assert [r.label for r in results] == ["Ilica 191E, Zagreb"]


def test_street_without_number() -> None:
    results = make().search("trg kralja")
    assert results[0].kind == "street"
    assert results[0].label == "Trg kralja Tomislava, Testno"


def test_settlement_suggestion() -> None:
    results = make().search("testn")
    assert results[0].kind == "settlement"


def test_unknown_number_gives_nothing() -> None:
    assert make().search("Ilica 999") == []
