"""Pronađi mjesto za život: deterministic ranking of settlements.

Filters and the weighted Skor za život run over precomputed settlement profiles
(ingest/settlement_profiles.py). A language model, when configured, may only turn
a free-text question into these filters; it never sees or produces numbers.
"""

from __future__ import annotations

import json
import re
from functools import lru_cache
from typing import Any, Literal

import httpx
import pandas as pd
from pydantic import BaseModel, Field, ValidationError

from analysis import score
from app import fmt
from app.config import get_settings
from app.profiles import load as load_profiles
from app.profiles import weights as profile_weights

Need = Literal[
    "kindergarten", "school", "doctor", "pediatrician", "pharmacy", "grocery", "park", "transit"
]
Size = Literal["any", "village", "town", "city"]
AirLimit = Literal["any", "niska", "umjerena"]

NEED_LABELS: dict[str, str] = {
    "kindergarten": "vrtić",
    "school": "osnovna škola",
    "doctor": "obiteljski liječnik",
    "pediatrician": "pedijatar",
    "pharmacy": "ljekarna",
    "grocery": "trgovina namirnicama",
    "park": "park",
    "transit": "javni prijevoz barem jednom na sat (vozni red)",
}
SIZE_LIMITS: dict[str, tuple[int, int | None]] = {
    "any": (0, None),
    "village": (0, 2000),
    "town": (2000, 20000),
    "city": (20000, None),
}
SIZE_LABELS = {
    "any": "bilo koje veličine",
    "village": "do 2.000 stanovnika",
    "town": "2.000 do 20.000 stanovnika",
    "city": "više od 20.000 stanovnika",
}
AIR_ORDER = ["vrlo niska", "niska", "umjerena", "visoka"]
SCORED = ("flood", "air", "green", "noise", "fire", "car_free", "transit", "daily")


class FindRequest(BaseModel):
    profile: str = "opci"
    weights: dict[str, float] | None = None
    county: str | None = None
    size: Size = "any"
    must: list[Need] = []
    max_air: AirLimit = "any"
    avoid_flood: bool = False
    limit: int = Field(default=10, ge=1, le=30)


class FindResult(BaseModel):
    code: str
    name: str
    municipality: str
    county: str
    population: int
    lat: float
    lon: float
    score: int | None
    reasons: list[str]
    facts: list[str]


class FindResponse(BaseModel):
    matching: int
    searched: int
    criteria: list[str]
    results: list[FindResult]
    note: str


class FindOptions(BaseModel):
    counties: list[str]
    settlements: int
    min_population: int
    llm: bool


@lru_cache
def profiles() -> pd.DataFrame:
    path = get_settings().processed_dir / "settlement_profiles.parquet"
    if not path.exists():
        return pd.DataFrame()
    return pd.read_parquet(path)


def options() -> FindOptions:
    df = profiles()
    settings = get_settings()
    return FindOptions(
        counties=sorted(df["county"].dropna().unique().tolist()) if not df.empty else [],
        settlements=len(df),
        min_population=200,
        llm=bool(settings.llm_base_url and settings.llm_model),
    )


def _criteria(req: FindRequest) -> list[str]:
    label = next(
        (p["label"] for p in load_profiles()["profiles"] if p["id"] == req.profile), req.profile
    )
    out = [f"profil: {label}", f"područje: {req.county or 'cijela Hrvatska'}"]
    out.append(f"veličina: {SIZE_LABELS[req.size]}")
    if req.must:
        out.append("pješice do 15 min: " + ", ".join(NEED_LABELS[n] for n in req.must))
    if req.max_air != "any":
        out.append(f"zrak: najviše razina „{req.max_air}”")
    if req.avoid_flood:
        out.append("izvan modeliranih poplavnih područja")
    return out


def _facts(row: pd.Series) -> list[str]:
    facts = []
    if row["flood_status"] == "good":
        facts.append("Središte nije u modeliranom poplavnom području.")
    elif row["flood_status"] == "bad":
        facts.append("Središte je u modeliranom poplavnom području.")
    else:
        facts.append("Modelirano poplavno područje je blizu središta.")
    if pd.notna(row["pm25"]):
        facts.append(
            f"Zrak: razina {row['air_band']} (PM2,5 {fmt.num(float(row['pm25']), 1)} µg/m³)."
        )
    if pd.notna(row["needs_15min"]):
        facts.append(f"Pješice do 15 min: {int(row['needs_15min'])} od 7 svakodnevnih potreba.")
    if pd.notna(row["max_departures"]):
        facts.append(
            f"Javni prijevoz: do {fmt.num(float(row['max_departures']), 1)} polazaka na sat."
        )
    if pd.notna(row["tree_share"]):
        facts.append(f"Drveće pokriva {fmt.num(float(row['tree_share']))} % okolice središta.")
    return facts


def _reasons(row: pd.Series, weights: dict[str, float], total: int | None) -> list[str]:
    labels = {c["id"]: c["label"] for c in load_profiles()["categories"]}
    pulls = []
    for cid in SCORED:
        s = row.get(f"score_{cid}")
        w = weights.get(cid, 0.0)
        if s is None or pd.isna(s) or w <= 0 or total is None:
            continue
        pulls.append((w * (float(s) - total), cid, int(s)))
    pulls.sort(reverse=True)
    best = [f"{labels[c]} ({s}/100)" for p, c, s in pulls[:2] if p > 0]
    out = ["Najjače: " + ", ".join(best)] if best else []
    weakest = [x for x in pulls if x[0] < 0]
    if weakest:
        _, c, s = weakest[-1]
        out.append(f"Najslabije: {labels[c]} ({s}/100)")
    return out


def find(req: FindRequest) -> FindResponse:
    df = profiles()
    note = (
        "Rang je izračun nad unaprijed pripremljenim podacima za središte svakog naselja s "
        "najmanje 200 stanovnika. Za konkretnu adresu otvorite izvještaj."
    )
    if df.empty:
        return FindResponse(matching=0, searched=0, criteria=_criteria(req), results=[], note=note)
    weights = {**profile_weights(req.profile), **(req.weights or {})}
    weights = {k: v for k, v in weights.items() if k in SCORED}
    sel = df
    if req.county:
        sel = sel[sel["county"] == req.county]
    low, high = SIZE_LIMITS[req.size]
    sel = sel[sel["population"] >= low]
    if high is not None:
        sel = sel[sel["population"] < high]
    for need in req.must:
        if need == "transit":
            sel = sel[sel["max_departures"].fillna(0) >= 1.0]
        else:
            sel = sel[sel[f"has_{need}"]]
    if req.max_air != "any":
        allowed = AIR_ORDER[: AIR_ORDER.index(req.max_air) + 1]
        sel = sel[sel["air_band"].isin(allowed)]
    if req.avoid_flood:
        sel = sel[sel["flood_status"] == "good"]
    scored = []
    for _, row in sel.iterrows():
        subs = {
            c: (None if pd.isna(row.get(f"score_{c}")) else float(row[f"score_{c}"]))
            for c in SCORED
        }
        scored.append((score.weighted(subs, weights), row))
    scored.sort(key=lambda x: (x[0] if x[0] is not None else -1, x[1]["population"]), reverse=True)
    results = [
        FindResult(
            code=str(row["code"]),
            name=str(row["name"]),
            municipality=str(row["municipality"]),
            county=str(row["county"]),
            population=int(row["population"]),
            lat=float(row["lat"]),
            lon=float(row["lon"]),
            score=None if s is None else int(s),
            reasons=_reasons(row, weights, None if s is None else int(s)),
            facts=_facts(row),
        )
        for s, row in scored[: req.limit]
    ]
    return FindResponse(
        matching=len(scored),
        searched=len(df),
        criteria=_criteria(req),
        results=results,
        note=note,
    )


PARSE_PROMPT = (
    "Pretvori pitanje o tome gdje živjeti u Hrvatskoj u JSON filtre. Vrati isključivo JSON s "
    "poljima: profile (opci|obitelj|umirovljenik|student|rad-od-kuce), county (točan naziv "
    "županije s popisa ili null), size (any|village|town|city; village < 2000, town 2000–20000, "
    "city > 20000 stanovnika), must (popis od: kindergarten, school, doctor, pediatrician, "
    "pharmacy, grocery, park, transit), max_air (any|niska|umjerena), avoid_flood (true|false). "
    "Ne izmišljaj ništa što nije u pitanju. Županije: "
)


class ParseUnavailable(RuntimeError):
    pass


def parse_question(question: str) -> FindRequest:
    """Free text -> filters with the language model. Raises ParseUnavailable."""
    settings = get_settings()
    if not (settings.llm_base_url and settings.llm_model):
        raise ParseUnavailable("Jezični model nije postavljen.")
    headers = {"Content-Type": "application/json"}
    if settings.llm_api_key:
        headers["Authorization"] = f"Bearer {settings.llm_api_key}"
    counties = ", ".join(options().counties)
    try:
        response = httpx.post(
            f"{settings.llm_base_url.rstrip('/')}/chat/completions",
            headers=headers,
            json={
                "model": settings.llm_model,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": PARSE_PROMPT + counties},
                    {"role": "user", "content": question},
                ],
            },
            timeout=30.0,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        match = re.search(r"\{.*\}", content, re.DOTALL)
        data: dict[str, Any] = json.loads(match.group(0) if match else content)
        if data.get("county") not in options().counties:
            data["county"] = None
        return FindRequest.model_validate({k: v for k, v in data.items() if v is not None})
    except (httpx.HTTPError, KeyError, IndexError, ValueError, ValidationError) as exc:
        raise ParseUnavailable("Pitanje nije moguće pretvoriti u filtre.") from exc
