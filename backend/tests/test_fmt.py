from app import fmt


def test_num_uses_croatian_separators() -> None:
    assert fmt.num(1235.33, 1) == "1.235,3"
    assert fmt.num(12) == "12"


def test_minutes_and_metres() -> None:
    assert fmt.minutes(0.4) == "manje od minute"
    assert fmt.minutes(1.2) == "1 minuta"
    assert fmt.minutes(3.6) == "4 minute"
    assert fmt.minutes(7.6) == "8 minuta"
    assert fmt.minutes(21) == "21 minuta"
    assert fmt.minutes(22) == "22 minute"
    assert fmt.metres(1260) == "1,3 km"
    assert fmt.metres(234) == "230 m"
    assert fmt.metres(999.6) == "1,0 km"


def test_plural() -> None:
    assert fmt.plural(1, "park", "parka", "parkova") == "park"
    assert fmt.plural(3, "park", "parka", "parkova") == "parka"
    assert fmt.plural(12, "park", "parka", "parkova") == "parkova"
    assert fmt.plural(21, "park", "parka", "parkova") == "park"
