from analysis import score
from app.models import Category, Scale, Value
from app.profiles import load, weights


def cat(cid: str, status: str = "info", status_label: str = "", values=None) -> Category:  # type: ignore[no-untyped-def]
    return Category(
        id=cid,
        group="environment",
        title=cid,
        status=status,  # type: ignore[arg-type]
        status_label=status_label,
        headline="",
        values=values or [],
    )


def air(*levels: str) -> Category:
    """Air category whose scales carry the PM2.5 and NO2 levels."""
    c = cat("air", "info", "Umjeren")
    c.scales = [
        Scale(key=f"p{i}", label="", unit="µg/m³", value=0.0, band=level, bands=[])
        for i, level in enumerate(levels)
    ]
    return c


def val(key: str, value: float) -> Value:
    return Value(
        key=key,
        label=key,
        value=value,
        display=str(value),
        source="t",
        retrieved_at=None,
        kind="modelled",
    )


def test_subscores_follow_documented_rules() -> None:
    assert score.subscore(cat("flood", "good")) == 100
    assert score.subscore(cat("flood", "bad")) == 0
    assert score.subscore(air("umjerena")) == 50
    assert score.subscore(air("niska", "umjerena")) == 50  # the worse level counts
    assert score.subscore(air("vrlo niska", "niska")) == 80
    assert score.subscore(cat("noise", "warning", "Blizu prometnice")) == 25
    assert score.subscore(cat("car_free", values=[val("needs_within_15min", 7)])) == 100
    assert score.subscore(cat("solar", values=[val("pv_kwh_per_kwp", 1250)])) == 50
    assert score.subscore(cat("transit", values=[val("max_departures_per_hour", 3)])) == 50
    assert score.subscore(cat("transit", values=[val("stops_10min", 2)])) is None
    assert score.subscore(cat("air", "no_data")) is None


def test_weighted_average_ignores_missing_and_zero_weights() -> None:
    scores = {"flood": 100.0, "air": 50.0, "solar": None}
    assert score.weighted(scores, {"flood": 1, "air": 1, "solar": 3}) == 75
    assert score.weighted(scores, {"flood": 3, "air": 1}) == 88
    assert score.weighted(scores, {"flood": 0, "air": 0}) is None


def test_every_profile_weights_every_category() -> None:
    ids = {c["id"] for c in load()["categories"]}
    for p in load()["profiles"]:
        assert set(weights(p["id"])) == ids
