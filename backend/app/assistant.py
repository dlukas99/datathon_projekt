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
from app.models import Category, Kind, Link, Report, Value
from app.sources import source_info

Intent = Literal[
    "report", "explain", "purchase_advice", "out_of_scope", "overview", "no_data", "unknown"
]

CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "flood": ("poplav", "rijek", "nasip", "izlije", "potop"),
    "air": ("zrak", "prasin", "pm2", "pm 2", "no2", "dusik", "onecis", "smog"),
    "green": ("zelen", "drve", "park", "hlad", "vruc", "toplin", "vrucin"),
    "noise": (
        "buk",
        "bucn",
        "promet",
        "pruga",
        "autocest",
        "cesta",
        "ceste",
        "cesti",
        "tisin",
        " tih",
        " mirn",
    ),
    "solar": ("sunc", "solar", "panel", "fotonapon", "elektran"),
    "fire": ("pozar", "opozar", "vatr", "gorjel"),
    "car_free": ("bez auta", "pjesice", "pjeske", "hodanj", "automobil", "auto "),
    "transit": ("autobus", "tramvaj", "vlak", "prijevoz", "stajalis", "polaz", "zeljeznic"),
    "kindergarten": ("vrtic", "jaslic"),
    "school": ("skol",),
    "doctor": ("lijecni", "doktor", "ordinacij", "obiteljsk", "ambulant", "dom zdravlja"),
    "pediatrician": ("pedijat",),
    "pharmacy": ("ljekarn", "apotek"),
    "grocery": ("trgovin", "ducan", "namirnic", "supermarket", "market"),
    "playground": ("igralist",),
    "recycling": ("reciklaz", "otpad", "zeleni otok", "kontejner"),
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
    "susjed",
)
EXPLAIN_PATTERNS = ("sto znaci", "sto je", "objasni", "kako se racuna", "sto su", "zasto")
# General questions about the place: answered with the report's summary.
OVERVIEW_PATTERNS = (
    "opcenito",
    "ukratko",
    "sazet",
    "sazmi",
    "kakvo je ovo mjesto",
    "kakvo je mjesto",
    "kako je zivjeti",
    "dobro mjesto",
    "dobra lokacija",
    "kakva je lokacija",
    "okolin",
    "okolis",
    "prednost",
    "nedostat",
    "nedostac",
    "pregled",
)
POPULATION_WORDS = ("stanovni", "koliko ljudi", "velicina naselja", "veliko naselje")


@dataclass(frozen=True)
class Gap:
    """A topic people ask about for which the report has no data."""

    words: tuple[str, ...]  # recognise the topic
    weak: tuple[str, ...]  # recognise it only when no category matched ("sigurno od poplava")
    sentence: str
    related: tuple[str, ...] = ()  # categories that help instead


GAPS: dict[str, Gap] = {
    "hospital": Gap(
        ("bolnic", "hitna pomoc", "hitnu pomoc", "hitne pomoci", "klinik", "kbc "),
        (),
        "O bolnicama i hitnoj pomoći nemamo podatke. U izvještaju su obiteljski liječnici, "
        "pedijatri i ljekarne.",
    ),
    "secondary_school": Gap(
        ("srednj", "gimnazij", "fakultet", "sveucilis"),
        (),
        "O srednjim školama i fakultetima nemamo podatke; u izvještaju su osnovne škole.",
        ("school",),
    ),
    "crime": Gap(
        ("kriminal", "kradj", "provala", "provale", "nasilj"),
        ("sigurn",),
        "O sigurnosti i kriminalu nemamo podatke.",
    ),
    "earthquake": Gap(("potres", "seizm"), (), "O potresima nemamo podatke."),
    "internet": Gap(
        ("internet", "optik", "signal", "wifi", "mobiln"),
        (),
        "O internetu i mobilnom signalu nemamo podatke.",
    ),
    "parking": Gap(("parking", "parkira", "garaz"), (), "O parkiranju nemamo podatke."),
    "temperature": Gap(
        ("temperatur", "stupnj", "toplinsk"),
        (),
        "Temperaturu ne mjerimo; pokazatelj hlada je udio drveća u okolici.",
        ("green",),
    ),
}

TOPICS = (
    "poplave, zrak, zelenilo i hlad, promet i ceste u blizini, požari raslinja, sunce na krovu, "
    "život bez auta, javni prijevoz, vrtić, osnovna škola, obiteljski liječnik, pedijatar, "
    "ljekarna, trgovina, igralište, reciklaža i broj stanovnika naselja"
)

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
        "Iz satelitske karte ESA WorldCover računamo koliko površine u krugu od 300 m čini "
        "priroda (drveće, grmlje, travnjaci, polja i močvare), a koliko drveće i zgrade. Ako "
        "je izgrađeno više od pola kopna, to je gradsko područje i vrijedi pravilo 3-30-300: "
        "najmanje 30 % površine pod drvećem i park do 300 m od kuće. Drveće ljeti daje hlad i "
        "ublažava vrućine; samu temperaturu ne mjerimo."
    ),
    "noise": (
        "Buku ne mjerimo: otvorene karte buke za cijelu Hrvatsku ne postoje. Prikazujemo "
        "udaljenost od autocesta, brzih, državnih i glavnih gradskih cesta te pruga. "
        "Do 300 m od velike prometnice buka i ispušni plinovi obično su najizraženiji, "
        "a dalje od 500 m utjecaj je slab (pregled istraživanja Health Effects Institutea, 2010.)."
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
    "fire": (
        "Opožarene površine dolaze iz europskog sustava EFFIS, koji ih kartira iz satelitskih "
        "snimaka od 2016. Prikazujemo požare u krugu od 2 km. Prošli požari pokazuju "
        "izloženost, ali ne predviđaju buduće."
    ),
    "transit": (
        "Broj polazaka na sat prosjek je od 6 do 20 sati za jedan radni dan iz voznih redova "
        "ZET-a, HŽPP-a i Autotroleja. Drugdje prikazujemo stajališta iz OpenStreetMapa bez "
        "voznog reda."
    ),
}

# Shown once under the conversation in the interface, not after every answer.
DISCLAIMER = "Ovo je informativni pregled iz otvorenih podataka, a ne službena procjena ni savjet."

# "Najbliža ljekarna je 5 minuta pješice": the nearest place of each daily need.
NEAREST: dict[str, str] = {
    "kindergarten": "Najbliži vrtić",
    "school": "Najbliža osnovna škola",
    "doctor": "Najbliži obiteljski liječnik",
    "pediatrician": "Najbliži pedijatar",
    "pharmacy": "Najbliža ljekarna",
    "grocery": "Najbliža trgovina namirnicama",
    "playground": "Najbliže igralište",
}


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


class SourceRef(BaseModel):
    title: str
    retrieved_at: str | None


class AssistantReply(BaseModel):
    answer: str = Field(description="Jedna do dvije rečenice koje izravno odgovaraju na pitanje")
    sources: list[SourceRef] = Field(default=[], description="Izvori odgovora, za redak „Izvor”")
    facts: list[Fact] = Field(default=[], description="Sve vrijednosti, za „Prikaži detalje”")
    links: list[Link] = []
    mode: Literal["rules", "llm"]


@dataclass
class Understanding:
    intent: Intent
    categories: list[str] = field(default_factory=list)
    gaps: list[str] = field(default_factory=list)
    population: bool = False


def understand_rules(question: str) -> Understanding:
    q = " " + normalize(question) + " "
    if any(p in q for p in PURCHASE_PATTERNS):
        return Understanding("purchase_advice")
    cats = [c for c, words in CATEGORY_KEYWORDS.items() if any(w in q for w in words)]
    population = any(w in q for w in POPULATION_WORDS)
    gaps = [
        name
        for name, gap in GAPS.items()
        if any(w in q for w in gap.words) or (not cats and any(w in q for w in gap.weak))
    ]
    if gaps:
        return Understanding("no_data", cats, gaps, population)
    if not cats and not population and any(w in q for w in OUT_OF_SCOPE):
        return Understanding("out_of_scope")
    if cats and any(p in q for p in EXPLAIN_PATTERNS):
        return Understanding("explain", cats)
    if cats or population:
        return Understanding("report", cats, population=population)
    if any(p in q for p in OVERVIEW_PATTERNS):
        return Understanding("overview")
    return Understanding("unknown")


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
    """Empty for one address (the answer speaks about it directly), else "Adresa A (…): "."""
    if total == 1:
        return ""
    letter = "A" if index == 0 else "B"
    label = report.location.label
    return f"Adresa {letter}" + (f" ({label})" if label else "") + ": "


def _value(cat: Category, key: str) -> Value | None:
    return next((v for v in cat.values if v.key == key), None)


def _nearest_sentence(cat_id: str, value: Value) -> str:
    """'Najbliža ljekarna je 5 minuta pješice (Ljekarna Centar).' from the report value."""
    head = NEAREST[cat_id]
    shown, _, rest = value.display.partition(" (")
    name = f" ({rest.rstrip(')')})" if rest else ""
    if value.unit == "min" and isinstance(value.value, int | float):
        if value.value > 60:
            return f"{head} je više od sat hoda daleko{name}."
        return f"{head} je {shown.replace(' hoda', '')} pješice{name}."
    return f"{head}: {value.display}."


def _car_free_sentence(cat: Category) -> str:
    have = _value(cat, "needs_within_15min")
    if have is None or not isinstance(have.value, int | float):
        return cat.headline
    n = int(have.value)
    if n >= 7:
        text = "Da: sve svakodnevne potrebe su do 15 minuta pješice"
    elif n >= 5:
        text = f"Uglavnom da: {n} od 7 svakodnevnih potreba je do 15 minuta pješice"
    elif n >= 3:
        text = f"Djelomično: {n} od 7 svakodnevnih potreba je do 15 minuta pješice"
    else:
        text = f"Teško: samo {n} od 7 svakodnevnih potreba je do 15 minuta pješice"
    missing = _value(cat, "needs_missing")
    if missing is not None and missing.display not in ("", "ništa"):
        text += f"; nedostaje: {missing.display}"
    unknown = _value(cat, "needs_unknown")
    if unknown is not None and unknown.display:
        text += "; javni prijevoz nismo mogli provjeriti, jer vozni red nije otvoren"
    return text + "."


def short_answer(cat_id: str, cat: Category) -> str:
    """One or two plain sentences that answer the question, from the report only."""
    if cat_id in DAILY_KEYS:
        value = _value(cat, f"nearest_{cat_id}")
        if value is None:
            return f"{NEAREST[cat_id]} nije pronađen u podacima za ovo područje."
        return _nearest_sentence(cat_id, value)
    if cat.status == "no_data":
        return cat.headline
    if cat_id == "flood" and cat.status == "good":
        return "Ne. Nije u području riječnih poplava, čak ni za vrlo rijetke velike poplave."
    if cat_id == "car_free":
        return _car_free_sentence(cat)
    return cat.headline


def _sources(values: list[Value]) -> list[SourceRef]:
    out: list[SourceRef] = []
    for v in values:
        ref = SourceRef(title=source_info(v.source).title, retrieved_at=v.retrieved_at)
        if all(r.title != ref.title for r in out):
            out.append(ref)
    return out


def _facts_for(
    report: Report, cat_id: str, prefix: str
) -> tuple[list[str], list[Fact], list[Link], list[SourceRef]]:
    cat = _category(report, cat_id)
    if cat is None:
        return [], [], [], []
    if cat_id in DAILY_KEYS:
        used = [v for v in cat.values if v.key in (f"nearest_{cat_id}", f"count15_{cat_id}")]
    else:
        used = list(cat.values)
    facts = [
        Fact(
            text=f"{v.label}: {v.display}",
            source=source_info(v.source).title,
            retrieved_at=v.retrieved_at,
            kind=v.kind,
        )
        for v in used
    ]
    links = [] if cat_id in DAILY_KEYS else list(cat.links)
    return [prefix + short_answer(cat_id, cat)], facts, links, _sources(used)


def _population(report: Report, prefix: str) -> tuple[str, list[Fact]]:
    """Inhabitants of the settlement (census 2021), from the report's location."""
    pop = report.location.population
    if pop is None:
        return f"{prefix}Broj stanovnika naselja nije poznat.", []
    settlement = report.location.settlement or "naselje"
    fact = Fact(
        text=f"{pop.label}: {pop.display}",
        source=source_info(pop.source).title,
        retrieved_at=pop.retrieved_at,
        kind=pop.kind,
    )
    return f"{prefix}Naselje {settlement} ima {pop.display}.", [fact]


def _comparison(reports: list[Report], cat_id: str) -> str | None:
    """A neutral sentence saying where a numeric value is lower or higher."""
    keys = {
        "air": ("pm25_annual", "nižu", "godišnju koncentraciju PM2,5"),
        "green": ("nature_share_300m", "veći", "udio prirode u krugu od 300 m"),
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

    where = "ove adrese" if len(request.locations) > 1 else "ovu adresu"
    if understood.intent == "unknown":
        return AssistantReply(
            answer=(
                f"To ne znam: odgovaram samo o okolišu i onome što je pješice za {where}, "
                "npr. „Kakav je zrak?” ili „Koliko je daleko vrtić?”"
            ),
            mode=mode,
        )

    sentences: list[str] = []
    cats = list(understood.categories)
    if understood.intent == "no_data":
        sentences.extend(GAPS[g].sentence for g in understood.gaps)
        cats += [c for g in understood.gaps for c in GAPS[g].related if c not in cats]
        if not cats and not understood.population:
            sentences.append(f"Za {where} mogu odgovoriti o ovim temama: {TOPICS}.")
            return AssistantReply(answer=" ".join(sentences), mode=mode)

    reports = [build(p.lat, p.lon, p.label) for p in request.locations]
    facts: list[Fact] = []
    links: list[Link] = []
    sources: list[SourceRef] = []
    if understood.population:
        for i, r in enumerate(reports):
            said, known = _population(r, _name(r, i, len(reports)))
            sentences.append(said)
            facts.extend(known)
            sources.extend(
                SourceRef(title=f.source, retrieved_at=f.retrieved_at)
                for f in known
                if all(f.source != y.title for y in sources)
            )
    if not cats and not sentences:
        # A general question (or the model found no category): the report's summary.
        for i, r in enumerate(reports):
            sentences.append(_name(r, i, len(reports)) + " ".join(r.summary))
        return AssistantReply(
            answer=" ".join(sentences)
            + " Pitajte me i konkretnije, npr. o poplavama, zraku ili najbližem vrtiću.",
            mode=mode,
        )

    for cat_id in cats:
        for i, r in enumerate(reports):
            s, f, links_for, refs = _facts_for(r, cat_id, _name(r, i, len(reports)))
            sentences.extend(s)
            facts.extend(f)
            sources.extend(x for x in refs if all(x.title != y.title for y in sources))
            for link in links_for:
                if link not in links:
                    links.append(link)
        comparison = _comparison(reports, cat_id)
        if comparison:
            sentences.append(comparison)
    return AssistantReply(
        answer=" ".join(sentences), sources=sources, facts=facts, links=links, mode=mode
    )
