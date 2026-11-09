"""The report summary: plain sentences from statuses; a flood leads only when it is there."""

from app.models import Category, Scale, ScaleBand, Value
from app.report import summary


def cat(cid: str, status: str, **kw: object) -> Category:
    return Category(
        id=cid,
        group="environment",
        title=cid,
        status=status,  # type: ignore[arg-type]
        status_label=status,
        headline="",
        **kw,  # type: ignore[arg-type]
    )


def air(band: str) -> Category:
    scale = Scale(
        key="pm25",
        label="PM2,5",
        unit="µg/m³",
        value=1.0,
        band=band,
        bands=[ScaleBand(upto=None, label=band, status="good")],
        markers=[],
    )
    return cat("air", "good", scales=[scale])


def needs(have: int, missing: str) -> Category:
    values = [
        Value(
            key="needs_within_15min",
            label="",
            value=have,
            display="",
            source="x",
            retrieved_at=None,
            kind="modelled",
        ),
        Value(
            key="needs_missing",
            label="",
            value=missing,
            display=missing,
            source="x",
            retrieved_at=None,
            kind="modelled",
        ),
    ]
    return cat("car_free", "good", values=values)


def test_no_flood_does_not_lead_and_a_flood_area_does() -> None:
    calm = summary(
        {
            "flood": cat("flood", "good"),
            "air": air("niska"),
            "green": cat("green", "good"),
            "noise": cat("noise", "good"),
            "car_free": needs(7, "ništa"),
        }
    )
    assert calm[0] == (
        "Mirno mjesto s dobrim zrakom, puno prirode okolo i bez opasnosti od riječnih poplava."
    )
    assert calm[1] == "Sve što trebate svaki dan imate pješice unutar 15 minuta."
    wet = summary(
        {
            "flood": cat("flood", "bad"),
            "air": air("umjerena"),
            "green": cat("green", "bad"),
            "noise": cat("noise", "warning"),
            "car_free": needs(2, "park"),
        }
    )
    assert wet[0].startswith("Pažnja:")
    assert wet[-1] == "Na što obratiti pažnju: velika cesta je blizu."


def test_only_safety_from_floods_comes_last() -> None:
    plain = summary(
        {
            "flood": cat("flood", "good"),
            "air": air("umjerena"),
            "green": cat("green", "warning"),
            "noise": cat("noise", "info"),
            "car_free": needs(7, "ništa"),
        }
    )
    assert plain[0].startswith("Sve što trebate")
    assert plain[1] == "Riječne poplave ovdje ne prijete."
