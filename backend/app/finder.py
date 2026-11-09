"""Predloži mjesto za život: deterministic ranking of settlements.

Each profile has mandatory requirements and extra criteria (config/finder_rules.json,
app/finder_rules.py). Settlements that meet the requirements are ranked by the
weighted rating (Ocjena mjesta) sub-scores plus the profile's criteria, all over precomputed
settlement profiles (ingest/settlement_profiles.py, ingest/facilities.py). A language
model, when configured, may only turn a free-text question into these filters; it
never sees or produces numbers.
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
from analysis.daily import departures
from analysis.environment import AIR_RATINGS
from app import finder_rules as fr
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
    score: int | None = Field(description="Rang za profil, 0–100")
    met: list[str] = Field(default=[], description="Ispunjeni obavezni uvjeti s vrijednostima")
    missing: list[str] = Field(default=[], description="Neispunjeni uvjeti i slabi kriteriji")
    relaxed: bool = Field(
        default=False, description="Ne ispunjava jedan obavezni uvjet; prikazano uz napomenu"
    )
    reasons: list[str] = Field(description="Dva do tri kratka razloga za odabrani profil")
    caution: str | None = Field(default=None, description="Na što obratiti pažnju")
    facts: list[str] = Field(description="Brojke i izvori za „Detalje”")


class FindResponse(BaseModel):
    matching: int
    searched: int
    criteria: list[str]
    requirements: list[str] = []
    relaxed_note: str | None = None
    results: list[FindResult]
    note: str


class FindOptions(BaseModel):
    counties: list[str]
    settlements: int
    min_population: int
    llm: bool


# The finder ranks settlements with at least this many inhabitants: smaller ones rarely
# have any services and would crowd the top of the list (the map shows all of them).
MIN_POPULATION = 200


@lru_cache
def profiles() -> pd.DataFrame:
    """Profiles of all settlements (also used by the map of Croatia)."""
    d = get_settings().processed_dir
    path = d / "settlement_profiles.parquet"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_parquet(path)
    facilities = d / "settlement_facilities.parquet"
    if facilities.exists():
        df = df.merge(pd.read_parquet(facilities), on="code", how="left")
    traffic = d / "settlement_traffic.parquet"
    if traffic.exists():
        # Distance from major roads over every address of the settlement replaces the
        # value at its single centre point (ingest/settlement_traffic.py).
        t = pd.read_parquet(traffic).rename(columns={"score_noise": "score_noise_addr"})
        df = df.merge(t, on="code", how="left")
        df["score_noise"] = df["score_noise_addr"].fillna(df["score_noise"])
        df = df.drop(columns="score_noise_addr")
    landcover = d / "settlement_landcover.parquet"
    if landcover.exists():
        # Nature, trees and air as medians over the addresses of the settlement replace
        # the values at its centre (ingest/settlement_landcover.py).
        lc = pd.read_parquet(landcover)
        lc["code"] = lc["code"].astype(str)
        df["code"] = df["code"].astype(str)
        df = df.merge(lc, on="code", how="left", suffixes=("", "_addr"))
        for col in ("score_green", "score_air"):
            df[col] = df[f"{col}_addr"].fillna(df[col])
            df = df.drop(columns=f"{col}_addr")
        df["tree_share"] = df["tree_med"].fillna(df["tree_share"])
        df["air_band"] = df["air_band_med"].fillna(df["air_band"])
        df["pm25"] = df["pm25_med"].fillna(df["pm25"])
        df["no2"] = df["no2_med"].fillna(df["no2"])
    return df


def ranked() -> pd.DataFrame:
    """The settlements the finder ranks: at least MIN_POPULATION inhabitants."""
    df = profiles()
    if df.empty:
        return df
    return df[df["population"].fillna(0) >= MIN_POPULATION]


def options() -> FindOptions:
    df = ranked()
    settings = get_settings()
    return FindOptions(
        counties=sorted(df["county"].dropna().unique().tolist()) if not df.empty else [],
        settlements=len(df),
        min_population=MIN_POPULATION,
        llm=bool(settings.llm_base_url and settings.llm_model),
    )


def _criteria(req: FindRequest) -> list[str]:
    label = next(
        (p["label"] for p in load_profiles()["profiles"] if p["id"] == req.profile), req.profile
    )
    out = [f"profil: {label}", f"područje: {req.county or 'cijela Hrvatska'}"]
    out.append("uvjet profila: " + fr.profile_rules(req.profile)["summary"].rstrip("."))
    out.append(f"veličina: {SIZE_LABELS[req.size]}")
    if req.must:
        out.append("pješice do 15 minuta: " + ", ".join(NEED_LABELS[n] for n in req.must))
    if req.max_air != "any":
        out.append(f"zrak: {AIR_RATINGS[req.max_air].lower()} ili bolji")
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
            f"Zrak: {AIR_RATINGS.get(row['air_band'], row['air_band']).lower()} "
            f"(PM2,5 {fmt.num(float(row['pm25']), 1)} µg/m³, medijan adresa naselja)."
        )
    near, far = row.get("near_share"), row.get("far_share")
    if near is not None and far is not None and pd.notna(near) and pd.notna(far):
        facts.append(
            f"Prometnice: {fmt.num(100 * float(near))} % adresa naselja je do 300 m, a "
            f"{fmt.num(100 * float(far))} % dalje od 500 m od autoceste, brze, državne ili "
            "glavne gradske ceste."
        )
    med, p25, p75 = row.get("dist_med"), row.get("dist_p25"), row.get("dist_p75")
    if all(x is not None and pd.notna(x) for x in (med, p25, p75)):
        facts.append(
            f"Udaljenost od velike ceste, medijan adresa: {_metres(med)} "
            f"(kod polovice adresa između {_metres(p25)} i {_metres(p75)})."
        )
    if pd.notna(row["needs_15min"]):
        facts.append(
            f"Pješice do 15 minuta od središta naselja: {int(row['needs_15min'])} od 7 "
            "svakodnevnih potreba."
        )
    if pd.notna(row["max_departures"]):
        facts.append(
            f"Javni prijevoz uz središte naselja: do {departures(float(row['max_departures']))} "
            "na sat."
        )
    facts.extend(_nature_facts(row))
    return facts


def _metres(x: object) -> str:
    m = float(x)  # type: ignore[arg-type]
    return "više od 5 km" if m >= 5000 else fmt.metres(m)


def _pct_range(row: pd.Series, col: str) -> str | None:
    vals = [row.get(f"{col}_{q}") for q in ("med", "p25", "p75")]
    if not all(v is not None and pd.notna(v) for v in vals):
        return None
    med, p25, p75 = (float(v) for v in vals)  # type: ignore[arg-type]
    return f"{fmt.num(med)} % (kod polovice adresa između {fmt.num(p25)} i {fmt.num(p75)} %)"


def _nature_facts(row: pd.Series) -> list[str]:
    """Nature and tree shade as medians over the addresses of the settlement."""
    nature, tree = _pct_range(row, "nature"), _pct_range(row, "tree")
    urban = row.get("urban_share")
    out = []
    if nature:
        out.append(f"Priroda u krugu od 300 m oko adrese, medijan adresa naselja: {nature}.")
    if tree and urban is not None and pd.notna(urban) and float(urban) >= 0.5:
        out.append(
            f"Drveće u krugu od 300 m, medijan adresa: {tree}; većina adresa je u gusto "
            "izgrađenom dijelu, gdje se preporučuje najmanje 30 %."
        )
    if not out and pd.notna(row.get("tree_share")):
        out.append(
            f"Drveće pokriva {fmt.num(float(row['tree_share']))} % kopna u krugu od 300 m "
            "od središta naselja."
        )
    return out


def _requirement_label(req: str) -> str:
    walk = int(fr.rules()["walk_minutes"])
    if req.startswith("walk:"):
        return f"{fr.WALK_LABELS[req.split(':', 1)[1]][0]} do {walk} minuta hoda"
    km = fmt.num(float(fr.rules()["higher_ed"]["max_km"]))
    return (
        f"Studiji u naselju ili veće studijsko središte do {km} km, uz stajalište javnog prijevoza"
    )


def find(req: FindRequest) -> FindResponse:
    df = ranked()
    note = (
        "Rang je izračun nad unaprijed pripremljenim podacima za središte svakog naselja s "
        "najmanje 200 stanovnika. Za konkretnu adresu otvorite izvještaj."
    )
    rules = fr.profile_rules(req.profile)
    requirements = [_requirement_label(r) for r in rules["requires"]]
    if df.empty:
        return FindResponse(
            matching=0,
            searched=0,
            criteria=_criteria(req),
            requirements=requirements,
            results=[],
            note=note,
        )
    weights = {**profile_weights(req.profile), **(req.weights or {})}
    weights = {k: v for k, v in weights.items() if k in SCORED}
    extra = {c["id"]: float(c["weight"]) for c in rules["criteria"]}
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
    strict: list[tuple[float | None, pd.Series, list[fr.Check]]] = []
    near: list[tuple[float | None, pd.Series, list[fr.Check]]] = []
    for _, row in sel.iterrows():
        checks = [fr.check_requirement(r, row) for r in rules["requires"]]
        failed = sum(not c.ok for c in checks)
        if failed > 1:
            continue
        subs: dict[str, float | None] = {
            c: (None if pd.isna(row.get(f"score_{c}")) else float(row[f"score_{c}"]))
            for c in SCORED
        }
        for cid in extra:
            subs[cid] = fr.criterion_score(cid, row)
        rank = score.weighted(subs, {**weights, **extra})
        (strict if failed == 0 else near).append((rank, row, checks))

    def order(item: tuple[float | None, pd.Series, list[fr.Check]]) -> tuple[float, int]:
        rank, row, _ = item
        return (rank if rank is not None else -1.0, int(row["population"]))

    strict.sort(key=order, reverse=True)
    near.sort(key=order, reverse=True)
    picked = [(x, False) for x in strict[: req.limit]]
    relaxed_note = None
    min_strict = int(fr.rules()["min_strict_results"])
    if len(strict) < min_strict and near:
        fill = near[: req.limit - len(picked)]
        picked += [(x, True) for x in fill]
        relaxed_note = (
            f"Obavezne uvjete profila ispunjava samo {fmt.num(len(strict))} "
            f"{fmt.plural(len(strict), 'naselje', 'naselja', 'naselja')} na odabranom području, "
            "pa su ispod njih i naselja kojima nedostaje jedan uvjet; to piše uz svako od njih."
        )
    results = []
    for (s, row, checks), relaxed in picked:
        # Only a requirement that is not met; weaker criteria are named in the caution.
        gaps = [c.text for c in checks if not c.ok]
        results.append(
            FindResult(
                code=str(row["code"]),
                name=str(row["name"]),
                municipality=str(row["municipality"]),
                county=str(row["county"]),
                population=int(row["population"]),
                lat=float(row["lat"]),
                lon=float(row["lon"]),
                score=None if s is None else int(s),
                met=[c.text for c in checks if c.ok],
                missing=list(dict.fromkeys(gaps)),
                relaxed=relaxed,
                reasons=fr.highlights(req.profile, row),
                caution=fr.caution(req.profile, row),
                facts=fr.profile_facts(req.profile, row) + _facts(row),
            )
        )
    return FindResponse(
        matching=len(strict),
        searched=len(df),
        criteria=_criteria(req),
        requirements=requirements,
        relaxed_note=relaxed_note,
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
