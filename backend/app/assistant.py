"""Assistant over the report API.

The language model (optional, any OpenAI-compatible API) is used only to
recognise the intent and the categories of a question. Every sentence with a
number, name or date is built from templates over tool results (the report), so
the model can never invent a value. Without a key, keyword rules do the same job.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Literal

import httpx
from pydantic import BaseModel, Field

from app.config import get_settings
from app.geocode import normalize
from app.models import Category, Kind, Link, Report
from app.sources import source_info

Intent = Literal["report", "explain", "purchase_advice", "out_of_scope"]

CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "flood": ("poplav", "rijek", "nasip", "izlije", "potop"),
    "air": ("zrak", "prasin", "pm2", "pm 2", "no2", "dusik", "onecis", "smog"),
    "green": ("zelen", "drve", "park", "hlad", "vruc", "toplin", "vrucin"),
    "noise": ("buk", "bucn", "promet", "pruga", "autocest"),
    "solar": ("sunc", "solar", "panel", "fotonapon", "elektran"),
    "car_free": ("bez auta", "pjesice", "pjeske", "hodanj", "automobil", "auto "),
    "transit": ("autobus", "tramvaj", "vlak", "prijevoz", "stajalis", "polaz", "zeljeznic"),
    "kindergarten": ("vrtic", "jaslic"),
    "school": ("skol",),
    "doctor": ("lijecni", "doktor", "ordinacij", "obiteljsk"),
    "pediatrician": ("pedijat",),
    "pharmacy": ("ljekarn", "apotek"),
    "grocery": ("trgovin", "ducan", "namirnic", "supermarket", "market"),
    "playground": ("igralist",),
}
DAILY_KEYS = {
    "kindergarten",
    "school",
    "doctor",
    "pediatrician",
    "pharmacy",
    "grocery",
    "playground",
}

PURCHASE_PATTERNS = (
    "da li da kupim",
    "trebam li kupiti",
    "isplati li se",
    "vrijedi li kupiti",
    "kupiti ili ne",
    "da kupim",
    "preporucujes li",
    "preporucate li",
    "je li dobra kupnja",
    "dobra investicija",
)
OUT_OF_SCOPE = (
    "cijen",
    "kosta",
    "eura",
    "vrijednost nekretnin",
    "kredit",
    "porez",
    "kamat",
    "vlasnistv",
    "zemljisn",
    "katast",
    "gradevinsk",
    "legaliz",
    "potres",
    "kriminal",
    "susjed",
)
EXPLAIN_PATTERNS = ("sto znaci", "sto je", "objasni", "kako se racuna", "sto su", "zasto")

EXPLANATIONS: dict[str, str] = {
    "flood": (
        "Povratno razdoblje od 100 godina znači da se poplava te veličine u prosjeku "
        "očekuje jednom u 100 godina, odnosno s vjerojatnošću od 1 % svake godine. Može se "
        "dogoditi i dvije godine zaredom. Prikazujemo modelirane karte JRC-a za 10, 100 i 500 "
        "godina; službene karte izrađuju Hrvatske vode."
    ),
    "air": (
        "PM2,5 su lebdeće čestice promjera do 2,5 mikrometra, a NO2 je dušikov dioksid, "
        "uglavnom iz prometa i izgaranja. Godišnji prosjek uspoređujemo sa smjernicom Svjetske "
        "zdravstvene organizacije iz 2021. i s graničnom vrijednošću EU-a koja vrijedi od 2030."
    ),
    "green": (
        "Udio drveća i zelenih površina u krugu od 300 m računamo iz satelitske karte ESA "
        "WorldCover. Uspoređujemo ga s pravilom 3-30-300: najmanje 30 % krošnji u susjedstvu i "
        "javna zelena površina do 300 m od kuće. Drveće ljeti ublažava vrućine."
    ),
    "noise": (
        "Za buku nemamo otvorene mjerne karte za cijelu Hrvatsku, pa prikazujemo procjenu: "
        "udaljenost od autocesta, glavnih i važnijih cesta te pruga. Što je prometnica bliže, "
        "to je buka vjerojatnije veća."
    ),
    "solar": (
        "Procjena dolazi iz alata PVGIS Europske komisije: koliko bi kilovatsati godišnje "
        "proizvela elektrana snage 1 kW uz optimalni nagib. Sjena susjednih zgrada i stvarni "
        "nagib krova nisu uračunati."
    ),
    "car_free": (
        "Provjeravamo sedam svakodnevnih potreba unutar 15 minuta hoda po stvarnoj mreži "
        "ulica, brzinom od 4,5 km/h: trgovinu namirnicama, ljekarnu, obiteljskog liječnika, "
        "vrtić, osnovnu školu, park i stajalište s barem jednim polaskom na sat radnim danom."
    ),
    "transit": (
        "Broj polazaka na sat prosjek je od 6 do 20 sati za jedan radni dan iz voznih redova "
        "ZET-a, HŽPP-a i Autotroleja. Drugdje prikazujemo stajališta iz OpenStreetMapa bez "
        "voznog reda."
    ),
}

DISCLAIMER = "Ovo je informativni pregled iz otvorenih podataka, a ne službena procjena ni savjet."


class AssistantLocation(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    label: str | None = Field(default=None, max_length=200)


class AssistantRequest(BaseModel):
    question: str = Field(min_length=2, max_length=300)
    locations: list[AssistantLocation] = Field(min_length=1, max_length=2)


class Fact(BaseModel):
    text: str
    source: str
    retrieved_at: str | None
    kind: Kind


class AssistantReply(BaseModel):
    answer: str
    facts: list[Fact] = []
    links: list[Link] = []
    mode: Literal["rules", "llm"]


@dataclass
class Understanding:
    intent: Intent
    categories: list[str] = field(default_factory=list)


def understand_rules(question: str) -> Understanding:
    q = " " + normalize(question) + " "
    if any(p in q for p in PURCHASE_PATTERNS):
        return Understanding("purchase_advice")
    cats = [c for c, words in CATEGORY_KEYWORDS.items() if any(w in q for w in words)]
    if not cats and any(w in q for w in OUT_OF_SCOPE):
        return Understanding("out_of_scope")
    if cats and any(p in q for p in EXPLAIN_PATTERNS):
        return Understanding("explain", cats)
    return Understanding("report", cats)


LLM_PROMPT = (
    "Ti si klasifikator pitanja za aplikaciju o okolišu adrese u Hrvatskoj. Vrati isključivo "
    'JSON oblika {"intent": "...", "categories": [...]}. intent je jedno od: report '
    "(pitanje o podacima za adresu), explain (što neki pojam znači), purchase_advice (traži "
    "savjet treba li kupiti), out_of_scope (cijene, pravna pitanja, sve izvan okoliša i "
    "dostupnosti). categories su nula ili više od: " + ", ".join(CATEGORY_KEYWORDS) + ". "
    "Ne odgovaraj na pitanje i ne piši ništa osim JSON-a."
)


def understand_llm(question: str) -> Understanding | None:
    settings = get_settings()
    if not (settings.llm_base_url and settings.llm_model):
        return None
    headers = {"Content-Type": "application/json"}
    if settings.llm_api_key:
        headers["Authorization"] = f"Bearer {settings.llm_api_key}"
    try:
        response = httpx.post(
            f"{settings.llm_base_url.rstrip('/')}/chat/completions",
            headers=headers,
            json={
                "model": settings.llm_model,
                "temperature": 0,
                "messages": [
                    {"role": "system", "content": LLM_PROMPT},
                    {"role": "user", "content": question},
                ],
            },
            timeout=20.0,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        match = re.search(r"\{.*\}", content, re.DOTALL)
        data = json.loads(match.group(0) if match else content)
        intent = data.get("intent")
        if intent not in ("report", "explain", "purchase_advice", "out_of_scope"):
            return None
        cats = [c for c in data.get("categories", []) if c in CATEGORY_KEYWORDS]
        return Understanding(intent, cats)
    except (httpx.HTTPError, KeyError, IndexError, ValueError, TypeError, AttributeError):
        return None


def _category(report: Report, cat_id: str) -> Category | None:
    target = "daily" if cat_id in DAILY_KEYS else cat_id
    return next((c for c in report.categories if c.id == target), None)


def _name(report: Report, index: int, total: int) -> str:
    if total == 1:
        return "Za ovu adresu"
    letter = "A" if index == 0 else "B"
    label = report.location.label
    return f"Adresa {letter}" + (f" ({label})" if label else "")


def _facts_for(
    report: Report, cat_id: str, prefix: str
) -> tuple[list[str], list[Fact], list[Link]]:
    cat = _category(report, cat_id)
    if cat is None:
        return [], [], []
    sentences: list[str] = []
    facts: list[Fact] = []
    if cat_id in DAILY_KEYS:
        value = next((v for v in cat.values if v.key == f"nearest_{cat_id}"), None)
        if value is not None:
            sentences.append(f"{prefix}: {value.label.lower()}, najbliže {value.display}.")
            facts.append(
                Fact(
                    text=f"{value.label}: {value.display}",
                    source=source_info(value.source).title,
                    retrieved_at=value.retrieved_at,
                    kind=value.kind,
                )
            )
        return sentences, facts, []
    sentences.append(f"{prefix} ({cat.title.lower()}, {cat.status_label.lower()}): {cat.headline}")
    for value in cat.values:
        facts.append(
            Fact(
                text=f"{value.label}: {value.display}",
                source=source_info(value.source).title,
                retrieved_at=value.retrieved_at,
                kind=value.kind,
            )
        )
    return sentences, facts, list(cat.links)


def _comparison(reports: list[Report], cat_id: str) -> str | None:
    """A neutral sentence saying where a numeric value is lower or higher."""
    keys = {
        "air": ("pm25_annual", "nižu", "godišnju koncentraciju PM2,5"),
        "green": ("tree_share_300m", "veći", "udio drveća u krugu od 300 m"),
        "solar": ("pv_kwh_per_kwp", "veću", "procijenjenu proizvodnju sunčane elektrane"),
    }
    if len(reports) != 2:
        return None
    if cat_id in keys:
        key, word, what = keys[cat_id]
        vals = []
        for r in reports:
            cat = _category(r, cat_id)
            v = next((x for x in cat.values if x.key == key), None) if cat else None
            vals.append(v.value if v and isinstance(v.value, int | float) else None)
        a, b = vals
        if a is None or b is None or a == b:
            return None
        lower_is_better = cat_id == "air"
        a_wins = (a < b) if lower_is_better else (a > b)
        return f"{word.capitalize()} {what} ima adresa {'A' if a_wins else 'B'}."
    if cat_id in DAILY_KEYS:
        times = []
        for r in reports:
            cat = _category(r, cat_id)
            v = next((x for x in cat.values if x.key == f"nearest_{cat_id}"), None) if cat else None
            times.append(v.value if v and v.unit == "min" and isinstance(v.value, float) else None)
        a, b = times
        if a is None or b is None or round(a) == round(b):
            return None
        return f"Pješice je bliže s adrese {'A' if a < b else 'B'}."
    return None


def answer(
    request: AssistantRequest,
    build: Callable[[float, float, str | None], Report],
) -> AssistantReply:
    understood = understand_llm(request.question)
    mode: Literal["rules", "llm"] = "llm"
    if understood is None:
        understood = understand_rules(request.question)
        mode = "rules"

    if understood.intent == "purchase_advice":
        return AssistantReply(
            answer=(
                "Ne dajem savjete o tome treba li kupiti nekretninu. Mogu vam reći činjenice: "
                "pitajte me npr. o poplavama, zraku, zelenilu, buci ili tome što je dostupno "
                "pješice. Za odluku se posavjetujte i sa stručnjacima (procjenitelj, odvjetnik) "
                "i provjerite službene izvore."
            ),
            mode=mode,
        )
    if understood.intent == "out_of_scope":
        return AssistantReply(
            answer=(
                "To pitanje je izvan onoga što ovaj alat pokriva (okoliš i dostupnost pješice). "
                "Za vlasništvo, cijene, kredite i građevinska pitanja obratite se nadležnim "
                "institucijama i stručnjacima: zemljišnoknjižnom odjelu općinskog suda, "
                "katastru, banci ili ovlaštenom procjenitelju."
            ),
            mode=mode,
        )
    if understood.intent == "explain":
        parts = [EXPLANATIONS[c] for c in understood.categories if c in EXPLANATIONS]
        if parts:
            return AssistantReply(answer=" ".join(parts), mode=mode)

    reports = [build(p.lat, p.lon, p.label) for p in request.locations]
    cats = understood.categories
    if not cats:
        sentences = []
        for i, r in enumerate(reports):
            sentences.append(f"{_name(r, i, len(reports))}: " + " ".join(r.summary))
        return AssistantReply(
            answer=" ".join(sentences)
            + " Pitajte me konkretnije, npr. o poplavama, zraku ili najbližem vrtiću.",
            mode=mode,
        )

    sentences = []
    facts: list[Fact] = []
    links: list[Link] = []
    for cat_id in cats:
        for i, r in enumerate(reports):
            s, f, links_for = _facts_for(r, cat_id, _name(r, i, len(reports)))
            sentences.extend(s)
            facts.extend(f)
            for link in links_for:
                if link not in links:
                    links.append(link)
        comparison = _comparison(reports, cat_id)
        if comparison:
            sentences.append(comparison)
    sentences.append(DISCLAIMER)
    return AssistantReply(answer=" ".join(sentences), facts=facts, links=links, mode=mode)
