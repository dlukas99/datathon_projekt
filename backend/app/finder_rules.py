"""Profile rules for "Predloži mjesto" (config/finder_rules.json).

Each profile has mandatory requirements (a settlement that misses one is not proposed,
or only with a clear note when too few settlements qualify) and extra criteria that
join the Skor za život sub-scores in the ranking. Every check returns a sentence with
the concrete value behind it, so each proposal explains why it was proposed and what
it lacks. Deterministic: no language model is involved.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from functools import lru_cache
from typing import Any

import pandas as pd

from app import fmt
from app.config import REPO_ROOT

RULES_PATH = REPO_ROOT / "config" / "finder_rules.json"

WALK_LABELS: dict[str, tuple[str, str]] = {
    # need: (nominative, genitive for "nema ...")
    "grocery": ("Trgovina namirnicama", "trgovine namirnicama"),
    "pharmacy": ("Ljekarna", "ljekarne"),
    "doctor": ("Obiteljski liječnik", "obiteljskog liječnika"),
    "pediatrician": ("Pedijatar", "pedijatra"),
    "kindergarten": ("Vrtić", "vrtića"),
    "school": ("Osnovna škola", "osnovne škole"),
    "park": ("Park", "parka"),
    "playground": ("Igralište", "igrališta"),
}


@lru_cache
def rules() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    return data


def profile_rules(profile_id: str) -> dict[str, Any]:
    profiles: dict[str, Any] = rules()["profiles"]
    found: dict[str, Any] = profiles.get(profile_id, profiles["opci"])
    return found


@dataclass(frozen=True)
class Check:
    ok: bool
    text: str


def _num(row: pd.Series, key: str) -> float | None:
    value = row.get(key)
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return None
    return float(value)


def _flag(row: pd.Series, key: str) -> bool:
    value = row.get(key)
    return bool(value) if value is not None and not pd.isna(value) else False


def _programmes(n: int) -> str:
    word = fmt.plural(n, "studijski program", "studijska programa", "studijskih programa")
    return f"{fmt.num(n)} {word}"


def higher_ed_places(row: pd.Series) -> list[dict[str, Any]]:
    raw = row.get("higher_ed")
    if not isinstance(raw, str) or not raw:
        return []
    places: list[dict[str, Any]] = json.loads(raw)
    return places


def programme_score(programmes: int) -> float:
    """Choice of studies in a place, 60–100: any higher education is a solid base and
    the log of the number of programmes adds up to 40 (full at `full_programmes`)."""
    full = float(rules()["higher_ed"]["full_programmes"])
    if programmes <= 0:
        return 60.0
    return 60.0 + 40.0 * min(1.0, math.log1p(programmes) / math.log1p(full))


def reach_score(place: dict[str, Any]) -> float:
    """Studies in another settlement count less, and less with distance."""
    cfg = rules()["higher_ed"]
    if place["km"] == 0:
        return programme_score(int(place["programmes"]))
    factor = float(cfg["reach_factor"]) * (1.0 - 0.5 * float(place["km"]) / float(cfg["max_km"]))
    return programme_score(int(place["programmes"])) * factor


def best_higher_ed(row: pd.Series) -> dict[str, Any] | None:
    """The settlement's own studies, else the best-scoring larger centre within reach."""
    cfg = rules()["higher_ed"]
    places = higher_ed_places(row)
    own = next((p for p in places if p["km"] == 0), None)
    if own is not None:
        return own
    reachable = [
        p
        for p in places
        if float(p["km"]) <= float(cfg["max_km"])
        and int(p["programmes"]) >= int(cfg["reach_min_programmes"])
    ]
    return max(reachable, key=reach_score) if reachable else None


def _higher_ed_text(place: dict[str, Any]) -> str:
    example = f", npr. {place['example']}" if place.get("example") else ""
    count = _programmes(int(place["programmes"]))
    if place["km"] == 0:
        return f"Studiji u naselju: {count}{example}"
    return (
        f"Studiji u blizini: {place['name']}, {fmt.num(float(place['km']), 1)} km zračne linije "
        f"od središta naselja ({count}{example})"
    )


def check_requirement(req: str, row: pd.Series) -> Check:
    walk = int(rules()["walk_minutes"])
    if req.startswith("walk:"):
        need = req.split(":", 1)[1]
        label, genitive = WALK_LABELS[need]
        minutes = _num(row, f"min_{need}")
        if _flag(row, f"has_{need}"):
            when = fmt.minutes(minutes) if minutes is not None else f"do {walk} min"
            return Check(True, f"{label}: {when} hoda")
        nearest = ""
        if minutes is not None:
            far = minutes > 60
            nearest = (
                " (najbliže više od sat hoda)" if far else f" (najbliže {fmt.minutes(minutes)})"
            )
        return Check(False, f"Nema {genitive} do {walk} min hoda{nearest}")
    if req == "higher_ed":
        place = best_higher_ed(row)
        max_km = fmt.num(float(rules()["higher_ed"]["max_km"]))
        if place is None:
            return Check(
                False, f"Nema studija u naselju ni većeg studijskog središta do {max_km} km"
            )
        if place["km"] == 0:
            return Check(True, _higher_ed_text(place))
        if not _flag(row, "has_stops"):
            return Check(
                False,
                _higher_ed_text(place) + ", ali nema stajališta javnog prijevoza do 10 min hoda",
            )
        return Check(True, _higher_ed_text(place) + "; stajalište javnog prijevoza do 10 min hoda")
    raise ValueError(f"Nepoznat uvjet: {req}")


def criterion_score(cid: str, row: pd.Series) -> float | None:
    if cid.startswith("walk:"):
        need = cid.split(":", 1)[1]
        cfg = rules()["walk_score"]
        minutes = _num(row, f"min_{need}")
        if minutes is None:
            return 100.0 if _flag(row, f"has_{need}") else 0.0
        full, zero = float(cfg["full_minutes"]), float(cfg["zero_minutes"])
        return max(0.0, min(100.0, 100.0 * (zero - minutes) / (zero - full)))
    if cid == "higher_ed":
        place = best_higher_ed(row)
        return 0.0 if place is None else reach_score(place)
    if cid == "hospital":
        km = _num(row, "hospital_km")
        if km is None:
            return None
        cfg = rules()["hospital"]
        full, zero = float(cfg["full_km"]), float(cfg["zero_km"])
        return max(0.0, min(100.0, 100.0 * (zero - km) / (zero - full)))
    raise ValueError(f"Nepoznat kriterij: {cid}")


def criterion_gap(cid: str, row: pd.Series) -> str | None:
    """A sentence for an important criterion the settlement does poorly on."""
    s = criterion_score(cid, row)
    if s is None or s >= 50:
        return None
    if cid.startswith("walk:"):
        return check_requirement(cid, row).text if s == 0 else None
    if cid == "hospital":
        km = _num(row, "hospital_km")
        name = row.get("hospital_name") or "bolnica"
        return f"Najbliža opća ili klinička bolnica je daleko: {name}, {fmt.num(km or 0, 1)} km"
    return None


def profile_facts(profile_id: str, row: pd.Series) -> list[str]:
    """Facts only some profiles need: hospital, student dormitory and canteen (OSM)."""
    out = []
    if profile_id == "umirovljenik":
        km = _num(row, "hospital_km")
        if km is not None:
            out.append(
                f"Najbliža opća ili klinička bolnica: {row['hospital_name']}, "
                f"{fmt.num(km, 1)} km zračne linije (OpenStreetMap)."
            )
    if profile_id == "student":
        for key, label in (
            ("dormitory", "Studentski dom"),
            ("canteen", "Menza ili studentski restoran"),
        ):
            km = _num(row, f"{key}_km")
            if km is not None and km <= float(rules()["higher_ed"]["max_km"]):
                out.append(
                    f"{label} u OpenStreetMapu: {row[f'{key}_name']}, "
                    f"{fmt.num(km, 1)} km zračne linije."
                )
    return out
