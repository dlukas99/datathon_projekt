"""Ocjena mjesta (rating of a place): a 0–100 sub-score per category and a weighted average.

The sub-scores translate each category's own result into 0–100 with fixed,
documented rules (docs/METODOLOGIJA.md, "Ocjena mjesta"). Where a sourced
threshold exists it sets the steps (WHO/EU for air, 3-30-300 for urban greenery,
HEI 300/500 m for traffic, flood scenarios); elsewhere the scale is our
transparent normalisation. Weights are visible and adjustable in the UI.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable

from app.models import Category

AIR_POINTS = {"vrlo niska": 100.0, "niska": 80.0, "umjerena": 50.0, "visoka": 10.0}
TRAFFIC_POINTS = {
    "Podalje od prometnica": 100.0,
    "Rub zone prometa": 60.0,
    "Blizu prometnice": 25.0,
}
FLOOD_POINTS = {"good": 100.0, "warning": 50.0, "bad": 0.0}
SOLAR_LOW, SOLAR_HIGH = 1000.0, 1500.0  # kWh/kWp per year; Croatia lies roughly in between
FREQUENT_DEPARTURES = 6.0  # departures per hour: a bus every 10 minutes counts as full score


def _value(cat: Category, key: str) -> float | None:
    for v in cat.values:
        if v.key == key and isinstance(v.value, int | float) and not isinstance(v.value, bool):
            return float(v.value)
    return None


def _clip(x: float) -> float:
    return max(0.0, min(100.0, x))


def _flood(cat: Category) -> float | None:
    return FLOOD_POINTS.get(cat.status)


def _air(cat: Category) -> float | None:
    # The worse of the PM2.5 and NO2 levels; the card label is a rating, not a level.
    return min((AIR_POINTS[s.band] for s in cat.scales if s.band in AIR_POINTS), default=None)


def green_points(tree: float, nature: float, urban: bool, park_distance_m: float | None) -> float:
    """Urban places: up to 60 points for tree cover (30 % = full) and 40 for a park within
    300 m (20 within 600 m), the 3-30-300 rule. Elsewhere the share of nature: 50 % or more
    of the land around is full score, so a village among fields is not judged by a rule
    made for cities."""
    if not urban:
        return _clip(nature * 2.0)
    score = min(tree / 30.0, 1.0) * 60.0
    if park_distance_m is not None:
        if park_distance_m <= 300:
            score += 40.0
        elif park_distance_m <= 600:
            score += 20.0
    return _clip(score)


def _green(cat: Category) -> float | None:
    tree = _value(cat, "tree_share_300m")
    nature = _value(cat, "nature_share_300m")
    if tree is None or nature is None:
        return None
    urban = _value(cat, "urban_area") == 1.0
    park = next((p for p in cat.places if p.category == "park"), None)
    return green_points(tree, nature, urban, park.distance_m if park else None)


def _traffic(cat: Category) -> float | None:
    return TRAFFIC_POINTS.get(cat.status_label)


def _fire(cat: Category) -> float | None:
    n = _value(cat, "burnt_areas_2km")
    if n is None:
        return None
    return 100.0 if n == 0 else 60.0 if n == 1 else 30.0


def _solar(cat: Category) -> float | None:
    kwh = _value(cat, "pv_kwh_per_kwp")
    if kwh is None:
        return None
    return _clip((kwh - SOLAR_LOW) / (SOLAR_HIGH - SOLAR_LOW) * 100.0)


def _car_free(cat: Category) -> float | None:
    n = _value(cat, "needs_within_15min")
    return None if n is None else _clip(n / 7.0 * 100.0)


def _transit(cat: Category) -> float | None:
    best = _value(cat, "max_departures_per_hour")
    if best is not None:
        # Stops without an open timetable nearby may run more often: below full score the
        # timetabled best is only a lower bound, so the frequency is unknown.
        if best < FREQUENT_DEPARTURES and _value(cat, "stops_without_timetable_10min"):
            return None
        return _clip(best / FREQUENT_DEPARTURES * 100.0)
    stops = _value(cat, "stops_10min")
    if stops is None:
        return None
    # Stops without an open timetable: their frequency is unknown, so no score.
    return 0.0 if stops == 0 else None


def _daily(cat: Category) -> float | None:
    counts = [v for v in cat.values if v.key.startswith("count15_")]
    if not counts or any(v.value is None for v in counts):
        return None
    present = sum(1 for v in counts if isinstance(v.value, int | float) and v.value > 0)
    return _clip(present / len(counts) * 100.0)


RULES: dict[str, Callable[[Category], float | None]] = {
    "flood": _flood,
    "air": _air,
    "green": _green,
    "noise": _traffic,
    "fire": _fire,
    "solar": _solar,
    "car_free": _car_free,
    "transit": _transit,
    "daily": _daily,
}


def subscore(cat: Category) -> float | None:
    if cat.status == "no_data":
        return None
    rule = RULES.get(cat.id)
    value = rule(cat) if rule else None
    return None if value is None else round(value)


def weighted(scores: dict[str, float | None], weights: dict[str, float]) -> float | None:
    used = [(scores[k], w) for k, w in weights.items() if w > 0 and scores.get(k) is not None]
    total = sum(w for _, w in used)
    if total == 0:
        return None
    return round(sum(s * w for s, w in used if s is not None) / total)


def attach(categories: Iterable[Category]) -> None:
    for cat in categories:
        cat.subscore = subscore(cat)
