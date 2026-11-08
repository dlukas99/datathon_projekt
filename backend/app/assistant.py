"""Assistant over the report API.

A question is split into clauses and every clause is matched with keyword rules
(text without diacritics, word stems, so "zrak", "zraka" and "zraku" or "skola"
and "škole" all match). One message can ask about several topics; each gets its
own block in the order asked. A short follow-up ("A škola?", "A pješice?") uses
the topics of the previous answer, which the page sends back (nothing is stored).

Every sentence with a number, name or date is built from templates over the
report, so nothing can be invented. The optional language model (any
OpenAI-compatible API) is asked only when the rules recognise nothing, and only
to name the topics; it never writes the answer.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import Literal

import httpx
from pydantic import BaseModel, Field

from app.config import get_settings
from app.geocode import normalize
from app.models import Category, Kind, Link, Place, Report, Status, Value
from app.sources import source_info

# Stems matched at the start of a word in text without diacritics.
CATEGORY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "flood": (
        "poplav",
        "rijek",
        "nasip",
        "izlij",
        "izlit",
        "potop",
        "velika voda",
        "velike vode",
        "povratn",
    ),
    "air": ("zrak", "prasin", "pm2", "pm 2", "pm10", "no2", "dusik", "onecis", "smog", "cestic"),
    "green": ("zelen", "drve", "drvec", "park(?!ir|ing)", "hlad", "vruc", "suma", "sume"),
    "noise": (
        "buk",
        "bucn",
        "promet",
        "pruga",
        "pruge",
        "autocest",
        "cest[aeiu]\\b",
        "tisin",
        "tih",
        "mirn",
    ),
    "solar": ("sunc", "solar", "panel", "fotonapon", "elektran"),
    "fire": ("pozar", "opozar", "vatr", "gorjel", "gorio"),
    "car_free": (
        "bez auta",
        "bez automobila",
        "zivjeti bez",
        "auto\\b",
        "automobil",
        "pjesice",
        "pjeske",
        "hodanj",
    ),
    "transit": (
        "autobus",
        "bus\\b",
        "busa\\b",
        "tramvaj",
        "vlak",
        "prijevoz",
        "stajalis",
        "stanic",
        "polaz",
        "zeljeznick",
        "javni",
    ),
    "kindergarten": ("vrtic", "jaslic"),
    "school": ("skol",),
    "doctor": (
        "lijecni",
        "ljecni",
        "doktor",
        "ordinacij",
        "obiteljsk",
        "opce prakse",
        "ambulant",
        "dom zdravlja",
    ),
    "pediatrician": ("pedijat",),
    "pharmacy": ("ljekarn", "apotek"),
    "grocery": ("trgovin", "ducan", "namirnic", "supermarket", "market", "konzum", "lidl"),
    "playground": ("igralis",),
    "recycling": ("reciklaz", "otpad", "zeleni otok", "kontejner"),
}
_CATEGORY_RE = {
    cat: re.compile(r"\b(?:" + "|".join(words) + ")") for cat, words in CATEGORY_KEYWORDS.items()
}

DAILY_KEYS = (
    "kindergarten",
    "school",
    "doctor",
    "pediatrician",
    "pharmacy",
    "grocery",
    "playground",
    "recycling",
)

# Nominative phrase and the matching form of "nearest" for each daily topic.
DAILY_NOUNS: dict[str, tuple[str, str]] = {
    "kindergarten": ("vrtić", "najbliži"),
    "school": ("osnovna škola", "najbliža"),
    "doctor": ("ordinacija obiteljske medicine", "najbliža"),
    "pediatrician": ("pedijatrijska ordinacija", "najbliža"),
    "pharmacy": ("ljekarna", "najbliža"),
    "grocery": ("trgovina namirnicama", "najbliža"),
    "playground": ("igralište", "najbliže"),
    "recycling": ("mjesto za reciklažu", "najbliže"),
}
DAILY_TITLES: dict[str, str] = {
    "kindergarten": "Vrtić",
    "school": "Osnovna škola",
    "doctor": "Obiteljski liječnik",
    "pediatrician": "Pedijatar",
    "pharmacy": "Ljekarna",
    "grocery": "Trgovina namirnicama",
    "playground": "Igralište",
    "recycling": "Reciklaža",
}
# Minutes of walking the report itself uses for "within reach" (METODOLOGIJA, Život bez auta).
WALK_LIMIT_MIN = 15

PURCHASE_PATTERNS = (
    "da li da kupim",
    "trebam li kupiti",
    "treba li kupiti",
    "isplati li se",
    "isplati se",
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
EXPLAIN_PATTERNS = (
    "sto znaci",
    "sto je to",
    "sto su",
    "objasni",
    "kako se racuna",
    "kako racunate",
    "zasto",
    "sto to znaci",
)
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
    "pregled",
)
PROS_CONS_RE = re.compile(
    r"\b(prednost|mane\b|mana\b|nedostat|nedostac|slabost|plusev|minus|dobre strane|lose strane)"
)
NEARBY_RE = re.compile(r"\b(najbliz|u blizini|u krugu|blizu|nadohvat)")
LIMITS_PATTERNS = (
    "sto ne znas",
    "sto ne znate",
    "sto nije provjeren",
    "nije provjeren",
    "sto ne mozes",
    "sto ne mozete",
    "koliko su pouzdan",
    "pouzdan",
    "sto nedostaje u podac",
    "ogranicenj",
)
POPULATION_WORDS = ("stanovni", "koliko ljudi", "velicina naselja", "veliko naselje")
YES_NO_STARTS = (
    "je li",
    "jel",
    "jeli",
    "ima li",
    "imaju li",
    "jesu li",
    "postoji li",
    "da li",
    "moze li",
    "nalazi li se",
    "bilo li je",
    "je li bilo",
)
FOLLOW_UP_STARTS = ("a ", "i ", "sto je s", "sto s ", "kako je s", "a sto", "kako stoji")
WALK_WORDS = ("pjesice", "pjeske", "hodanj", "hoda", "koliko daleko", "koliko minuta", "udaljen")
# Words that carry no topic of their own; anything else left in a clause is a topic we
# could not recognise.
FILLER = frozenset(
    re.findall(
        r"\w+",
        "molim hvala reci recite mi me nam zanima zanimalo jos li je su se bi bih bismo sto "
        "kako kakav kakva kakvo kakve kakvi koliko gdje ovdje ovo ova ovaj ove ovoj ovom tu tamo "
        "ok dobro pa onda da ne mozes mozete zelim htio htjela bih znati jel jeli postoji biti "
        "ima imaju li nesto nekog neku neki ikakv ikakva adresa adresi adresu lokacija lokaciji "
        "mjesto mjestu ulica ulici kuca kuci stan stanu ovu ove taj ta to toga tome za od do na "
        "u s sa iz uz pri po o kod blizini blizu puno malo dovoljno ljeti zimi danas sada isto "
        "kuce cijeli cijela opet takoder samo jos nam vam",
    )
)

EXAMPLES = (
    "Kakav je zrak i ima li ljekarna blizu?",
    "Što je u krugu 10 minuta?",
    "Koje su prednosti i mane ove lokacije?",
)


@dataclass(frozen=True)
class Gap:
    """A topic people ask about for which the report has no data."""

    title: str
    words: tuple[str, ...]  # recognise the topic
    weak: tuple[str, ...]  # recognise it only when the clause names no category
    sentence: str
    related: tuple[str, ...] = ()  # categories that help instead


GAPS: dict[str, Gap] = {
    "hospital": Gap(
        "Bolnica i hitna pomoć",
        ("bolnic", "hitna pomoc", "hitnu pomoc", "hitne pomoci", "klinik", "kbc "),
        (),
        "O bolnicama i hitnoj pomoći nemamo podatke. U izvještaju su obiteljski liječnici, "
        "pedijatri i ljekarne.",
    ),
    "secondary_school": Gap(
        "Srednja škola",
        ("srednj", "gimnazij", "fakultet", "sveucilis"),
        (),
        "O srednjim školama i fakultetima nemamo podatke; u izvještaju su osnovne škole.",
        ("school",),
    ),
    "crime": Gap(
        "Sigurnost",
        ("kriminal", "kradj", "provala", "provale", "nasilj"),
        ("sigurn",),
        "O sigurnosti i kriminalu nemamo podatke.",
    ),
    "earthquake": Gap("Potresi", ("potres", "seizm"), (), "O potresima nemamo podatke."),
    "internet": Gap(
        "Internet i signal",
        ("internet", "optik", "signal", "wifi", "mobiln"),
        (),
        "O internetu i mobilnom signalu nemamo podatke.",
    ),
    "parking": Gap(
        "Parkiranje", ("parking", "parkira", "garaz"), (), "O parkiranju nemamo podatke."
    ),
    "temperature": Gap(
        "Temperatura",
        ("temperatur", "stupnj", "toplinsk"),
        (),
        "Temperaturu ne mjerimo; pokazatelj hlada je udio drveća u okolici.",
        ("green",),
    ),
}

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
        "javna zelena površina do 300 m od kuće. Drveće ljeti daje hlad i ublažava vrućine; "
        "samu temperaturu ne mjerimo."
    ),
    "noise": (
        "Buku ne mjerimo: otvorene karte buke za cijelu Hrvatsku ne postoje. Prikazujemo "
        "udaljenost od autocesta, brzih, državnih i županijskih cesta te pruga. Do 300 m od velike "
        "prometnice buka i ispušni plinovi obično su najizraženiji, a dalje od 500 m utjecaj "
        "je slab (pregled istraživanja Health Effects Institutea, 2010.)."
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

# Logical next questions after a topic; the page leaves out those already asked.
FOLLOW_UPS: dict[str, tuple[str, ...]] = {
    "flood": ("Je li bilo požara u blizini?", "Što znači povratno razdoblje?", "Kakav je zrak?"),
    "air": ("A buka i promet?", "Ima li zelenila u blizini?", "Što znači PM2,5?"),
    "green": ("Kakav je zrak?", "Ima li igralište blizu?", "A buka i promet?"),
    "noise": ("Kakav je zrak?", "Ima li parka u blizini?", "Ima li autobus u blizini?"),
    "fire": ("Je li u poplavnom području?", "Ima li zelenila u blizini?"),
    "solar": ("Kako se računa sunce na krovu?", "Ima li zelenila u blizini?"),
    "car_free": ("Što je u krugu 10 minuta?", "Ima li autobus u blizini?", "A trgovina?"),
    "transit": ("Mogu li živjeti bez auta?", "Koliko je do škole?", "Što je najbliže?"),
    "kindergarten": ("A škola?", "A pedijatar?", "Ima li igralište blizu?"),
    "school": ("A vrtić?", "Ima li autobus u blizini?", "Ima li igralište blizu?"),
    "doctor": ("A pedijatar?", "A ljekarna?", "Ima li autobus u blizini?"),
    "pediatrician": ("A vrtić?", "A ljekarna?", "A obiteljski liječnik?"),
    "pharmacy": ("A obiteljski liječnik?", "A trgovina?", "Što je u krugu 10 minuta?"),
    "grocery": ("A ljekarna?", "Što je u krugu 10 minuta?", "Mogu li živjeti bez auta?"),
    "playground": ("A vrtić?", "Ima li zelenila u blizini?"),
    "recycling": ("A trgovina?", "Što je najbliže?"),
    "overview": ("Koje su prednosti i mane ove lokacije?", "Što nije provjereno?"),
    "pros_cons": ("Što nije provjereno?", "Što je u krugu 10 minuta?"),
    "nearby": ("Mogu li živjeti bez auta?", "Ima li autobus u blizini?"),
    "limits": ("Kakav je zrak?", "Je li u poplavnom području?"),
    "population": ("Kakvo je ovo mjesto ukratko?", "Što je najbliže?"),
}
DEFAULT_SUGGESTIONS = (
    "Kakav je zrak i ima li ljekarna blizu?",
    "Je li u poplavnom području?",
    "Koje su prednosti i mane ove lokacije?",
    "Što je u krugu 10 minuta?",
)

# Shown once by the page, under the conversation.
DISCLAIMER = "Informativni pregled iz otvorenih podataka, nije službena procjena ni savjet."


class AssistantLocation(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    label: str | None = Field(default=None, max_length=200)


class AssistantRequest(BaseModel):
    question: str = Field(min_length=2, max_length=300)
    locations: list[AssistantLocation] = Field(min_length=1, max_length=2)
    # Topics of the previous answer in this conversation, for "A škola?" (not stored).
    context: list[str] = Field(default_factory=list, max_length=20)


class Fact(BaseModel):
    text: str
    source: str
    retrieved_at: str | None
    kind: Kind


class Line(BaseModel):
    """One key number, read as "label: value"."""

    label: str
    value: str


class Chip(BaseModel):
    label: str
    tone: Literal["good", "missing", "unknown"]


class Block(BaseModel):
    """The answer to one topic of the question."""

    topic: str
    title: str
    address: str | None = None
    status: Status | None = None
    status_label: str | None = None
    text: str
    lines: list[Line] = []
    chips: list[Chip] = []
    links: list[Link] = []
    sources: list[Fact] = []
    method: list[str] = []


class AssistantReply(BaseModel):
    answer: str = Field(description="The whole answer as plain text")
    summary: str | None = None
    blocks: list[Block] = []
    topics: list[str] = Field(default=[], description="Send back as `context` for a follow-up")
    suggestions: list[str] = []
    facts: list[Fact] = []
    links: list[Link] = []
    mode: Literal["rules", "llm"]


PartKind = Literal[
    "category",
    "explain",
    "gap",
    "purchase",
    "scope",
    "overview",
    "pros_cons",
    "nearby",
    "limits",
    "population",
    "uncovered",
]


@dataclass(frozen=True)
class Part:
    kind: PartKind
    topic: str = ""
    clause: str = ""
    minutes: int | None = None
    yes_no: bool = False
    walking: bool = False


# --- Numbers in Croatian ---------------------------------------------------------------


def fmt_int(n: int) -> str:
    """28111 -> "28.111"."""
    return f"{n:,}".replace(",", ".")


def fmt_decimal(x: float, digits: int = 1) -> str:
    """9.94 -> "9,9"; whole numbers without decimals."""
    text = f"{x:.{digits}f}".replace(".", ",")
    return text.rstrip("0").rstrip(",") if "," in text else text


def fmt_minutes(minutes: float) -> str:
    """Whole minutes as the report shows them, at least 1: "7 min"."""
    return f"{max(1, round(minutes))} min"


def fmt_metres(metres: float) -> str:
    """370 m, 1,4 km: the same rounding as the page (10 m, then 0,1 km)."""
    if metres >= 1000:
        return f"{fmt_decimal(metres / 1000)} km"
    return f"{round(metres / 10) * 10} m"


# --- Understanding --------------------------------------------------------------------

_CLAUSE_SPLIT = re.compile(r"[?!.;:,]+|\s(?:i|a|te|ili|pa|kao i|te i)\s", re.IGNORECASE)


def _clauses(question: str) -> list[tuple[str, str]]:
    """(original, normalised) pieces of the question, in order."""
    out = []
    for piece in _CLAUSE_SPLIT.split(question):
        norm = normalize(piece)
        if norm:
            out.append((piece.strip(), norm))
    return out


_CAR_WORDS = re.compile(r"\b(bez auta|bez automobila|zivjeti bez|auto\b|automobil)")


def _categories_in(norm: str) -> list[str]:
    found = []
    for cat, pattern in _CATEGORY_RE.items():
        match = pattern.search(norm)
        if match:
            found.append((match.start(), cat))
    cats = [cat for _, cat in sorted(found)]
    # "Koliko je pješice do vrtića?" asks about the kindergarten, not life without a car.
    if "car_free" in cats and any(c in DAILY_KEYS for c in cats) and not _CAR_WORDS.search(norm):
        cats.remove("car_free")
    return cats


NEAR_WORDS = frozenset(
    [
        "najblize",
        "najblizi",
        "najbliza",
        "najblizeg",
        "najblizu",
        "najblizih",
        "krugu",
        "minuta",
        "minute",
        "min",
        "hoda",
        "pjesice",
        "nalazi",
        "nalaze",
    ]
)
# A clause asking where something is: an unknown place gets "no data", not "I don't understand".
_PLACE_QUESTION = re.compile(r"\b(najbliz|u blizini|blizu|u krugu|gdje je|gdje su|koliko je do)")


def _has_content(norm: str, ignore: frozenset[str] = frozenset()) -> bool:
    return any(
        len(w) >= 3 and w not in FILLER and w not in ignore and not w.isdigit()
        for w in norm.split()
    )


def _clause_parts(original: str, norm: str) -> list[Part]:
    q = f" {norm} "
    yes_no = norm.startswith(YES_NO_STARTS)
    parts: list[Part] = []
    if any(p in q for p in PURCHASE_PATTERNS):
        parts.append(Part("purchase"))
    cats = _categories_in(norm)
    for name, gap in GAPS.items():
        if any(w in q for w in gap.words) or (not cats and any(w in q for w in gap.weak)):
            parts.append(Part("gap", name))
            parts += [Part("category", c) for c in gap.related]
    if cats and any(p in q for p in EXPLAIN_PATTERNS):
        return parts + [Part("explain", c) for c in cats if c in EXPLANATIONS]
    if not cats and any(w in q for w in OUT_OF_SCOPE):
        parts.append(Part("scope"))
    if any(p in q for p in LIMITS_PATTERNS):
        parts.append(Part("limits"))
    if PROS_CONS_RE.search(norm):
        parts.append(Part("pros_cons"))
    elif not cats and any(p in q for p in OVERVIEW_PATTERNS):
        parts.append(Part("overview"))
    if not cats and NEARBY_RE.search(norm) and not parts and not _has_content(norm, NEAR_WORDS):
        minutes = re.search(r"(\d{1,2})\s*min", norm)
        parts.append(Part("nearby", minutes=int(minutes.group(1)) if minutes else None))
    if any(w in q for w in POPULATION_WORDS):
        parts.append(Part("population"))
    parts += [Part("category", c, yes_no=yes_no) for c in cats]
    if not parts and _has_content(norm):
        parts.append(Part("uncovered", clause=original))
    return parts


def understand_rules(question: str, context: Iterable[str] = ()) -> list[Part]:
    """Every topic of the question, in the order asked."""
    whole = normalize(question)
    known = [c for c in context if c in CATEGORY_KEYWORDS]
    follow_up = bool(known) and (
        f"{whole} ".startswith(FOLLOW_UP_STARTS) or len(whole.split()) <= 3
    )
    parts: list[Part] = []
    for original, norm in _clauses(question):
        parts += _clause_parts(original, norm)

    if follow_up:
        topics = [p.topic for p in parts if p.kind == "category"]
        walking = any(w in f" {whole} " for w in WALK_WORDS)
        explain = any(p in f" {whole} " for p in EXPLAIN_PATTERNS) or whole in ("zasto", "a zasto")
        # "A pješice?" after a daily place: walking to that place, not life without a car.
        if walking and set(topics) <= {"car_free"}:
            daily = [c for c in known if c in DAILY_KEYS]
            if daily:
                parts = [Part("category", c, walking=True) for c in daily]
        elif explain and not topics:
            parts = [Part("explain", c) for c in known if c in EXPLANATIONS] or [
                Part("category", c) for c in known
            ]

    seen: set[tuple[str, str]] = set()
    unique: list[Part] = []
    for part in parts:
        key = (part.kind, part.topic or part.clause)
        if key not in seen:
            seen.add(key)
            unique.append(part)
    # Alone, a clause we could not read is worth an answer only when it asks for a place
    # ("Gdje je najbliži pikado klub?"); otherwise the question is not about the address.
    if all(p.kind == "uncovered" for p in unique) and not any(
        _PLACE_QUESTION.search(normalize(p.clause)) for p in unique
    ):
        return []
    return unique


LLM_PROMPT = (
    "Ti si klasifikator pitanja za aplikaciju o okolišu adrese u Hrvatskoj. Vrati isključivo "
    'JSON oblika {"intent": "...", "categories": [...]}. intent je jedno od: report '
    "(pitanje o podacima za adresu), explain (što neki pojam znači), purchase_advice (traži "
    "savjet treba li kupiti), out_of_scope (cijene, pravna pitanja, sve izvan okoliša i "
    "dostupnosti). categories su nula ili više od: " + ", ".join(CATEGORY_KEYWORDS) + ". "
    "Ne odgovaraj na pitanje i ne piši ništa osim JSON-a."
)


def understand_llm(question: str) -> list[Part] | None:
    """Topics named by the language model, or None without a model or a usable answer."""
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
                "max_tokens": 120,
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
        cats = [c for c in data.get("categories", []) if c in CATEGORY_KEYWORDS]
    except (httpx.HTTPError, KeyError, IndexError, ValueError, TypeError, AttributeError):
        return None
    if intent == "purchase_advice":
        return [Part("purchase")]
    if intent == "out_of_scope":
        return [Part("scope")]
    if intent == "explain":
        return [Part("explain", c) for c in cats if c in EXPLANATIONS] or None
    if intent == "report":
        return [Part("category", c) for c in cats] or None
    return None


# --- Building the answer --------------------------------------------------------------


def _lower_first(text: str) -> str:
    return text[:1].lower() + text[1:] if text[:1].isupper() and not text[1:2].isupper() else text


def _category(report: Report, cat_id: str) -> Category | None:
    target = "daily" if cat_id in DAILY_KEYS else cat_id
    return next((c for c in report.categories if c.id == target), None)


def _value(cat: Category | None, key: str) -> Value | None:
    if cat is None:
        return None
    return next((v for v in cat.values if v.key == key), None)


def _nearest(places: list[Place], category: str) -> Place | None:
    timed = [p for p in places if p.category == category and p.walk_minutes is not None]
    return min(timed, key=lambda p: p.walk_minutes or 0.0, default=None)


def _fact(value: Value) -> Fact:
    return Fact(
        text=value.label,
        source=source_info(value.source).title,
        retrieved_at=value.retrieved_at,
        kind=value.kind,
    )


def _short_label(label: str) -> str:
    """ "PM2,5, godišnji prosjek 2024." -> "PM2,5"; other labels stay whole."""
    return label.split(", ")[0]


def _readable(display: str) -> str:
    """ "18,2 µg/m³ (umjerena razina)" -> "18,2 µg/m³ – umjerena razina"."""
    m = re.fullmatch(r"(.+?) \(([^()]+)\)", display)
    return f"{m.group(1)} – {m.group(2)}" if m else display


def _line(value: Value, label: str | None = None) -> Line:
    return Line(label=label or _short_label(value.label), value=_readable(value.display))


def _block(cat: Category, topic: str, text: str, address: str | None) -> Block:
    return Block(
        topic=topic,
        title=cat.title,
        address=address,
        status=cat.status,
        status_label=cat.status_label,
        text=text,
        sources=[_fact(v) for v in cat.values],
        method=cat.notes[:2],
    )


def _environment_block(cat: Category, part: Part, address: str | None) -> Block:
    headline = cat.headline
    lines: list[Line] = []
    if cat.id == "flood":
        point = [_value(cat, f"flood_rp{rp}_point") for rp in (10, 100, 500)]
        inside = any(v is not None and v.value is True for v in point)
        text = f"{'Da' if inside else 'Ne'} – {_lower_first(headline)}" if part.yes_no else headline
        text += " Model obuhvaća samo riječne poplave većih rijeka, ne bujice ni more."
        for rp in (10, 100, 500):
            at = _value(cat, f"flood_rp{rp}_point")
            near = _value(cat, f"flood_rp{rp}_100m")
            if at is not None and near is not None:
                lines.append(
                    Line(
                        label=f"Poplava „jednom u {rp} godina”",
                        value=(
                            "lokacija je u području"
                            if at.value is True
                            else "područje je unutar 100 m"
                            if near.value is True
                            else "ni lokacija ni krug od 100 m"
                        ),
                    )
                )
    elif cat.id == "air":
        text = f"{headline} To je procjena iz modela za godišnji prosjek, a ne mjerenje na adresi."
        lines = [_line(v) for v in cat.values[:3]]
    elif cat.id == "green":
        text = f"{headline} Temperaturu ne mjerimo, pa hlad procjenjujemo po udjelu drveća."
        labels = {
            "tree_share_300m": "Drveće u krugu 300 m",
            "green_share_300m": "Zelene površine u krugu 300 m",
            "nearest_park": "Najbliži park",
        }
        lines = [_line(v, labels[v.key]) for v in cat.values if v.key in labels]
    elif cat.id == "noise":
        text = f"{headline} Buku ne mjerimo: ovo je procjena prema udaljenosti od ceste."
        lines = [_line(v) for v in cat.values[:3]]
    elif cat.id == "fire":
        burnt = _value(cat, "burnt_areas_2km")
        text = headline
        if part.yes_no and burnt is not None and isinstance(burnt.value, int | float):
            text = f"{'Da' if burnt.value > 0 else 'Ne'} – {_lower_first(headline)}"
        lines = [_line(v) for v in cat.values[:3]]
    elif cat.id == "solar":
        text = f"{headline} Sjena susjednih zgrada i stvarni nagib krova nisu uračunati."
        lines = [_line(v) for v in cat.values[:3]]
    elif cat.id == "transit":
        stops = _value(cat, "stops_10min")
        text = headline
        if part.yes_no and stops is not None and isinstance(stops.value, int | float):
            text = f"{'Da' if stops.value > 0 else 'Ne'} – {_lower_first(headline)}"
        lines = [_line(v) for v in cat.values[:3]]
        stop = _nearest(cat.places, "stop")
        if stop is not None and stop.walk_minutes is not None:
            air = f", zračno {fmt_metres(stop.distance_m)}" if stop.distance_m else ""
            lines.append(
                Line(
                    label="Najbliže stajalište", value=f"{fmt_minutes(stop.walk_minutes)} hoda{air}"
                )
            )
    else:
        text = headline
        lines = [_line(v) for v in cat.values[:3]]
    block = _block(cat, cat.id, text, address)
    block.lines = lines[:4]
    block.links = list(cat.links)
    return block


def _car_free_block(cat: Category, address: str | None) -> Block:
    first = cat.headline.split(". ")[0].rstrip(".") + "."
    block = _block(cat, "car_free", first, address)
    count = _value(cat, "needs_within_15min")
    if count is not None:
        block.lines = [Line(label="Unutar 15 min hoda", value=count.display)]
    missing = _value(cat, "needs_missing")
    if missing is not None and missing.display != "ništa":
        block.chips += [
            Chip(label=f"nedostaje: {m}", tone="missing") for m in missing.display.split(", ")
        ]
    unknown = _value(cat, "needs_unknown")
    if unknown is not None:
        block.chips += [
            Chip(label=f"nije provjereno: {u}", tone="unknown") for u in unknown.display.split(", ")
        ]
    if not block.chips:
        block.text += " Ništa od toga ne nedostaje."
    return block


def _daily_block(report: Report, topic: str, part: Part, address: str | None) -> Block | None:
    cat = _category(report, topic)
    if cat is None:
        return None
    noun, nearest_word = DAILY_NOUNS[topic]
    value = _value(cat, f"nearest_{topic}")
    count = _value(cat, f"count15_{topic}")
    place = _nearest(cat.places, topic)
    minutes = place.walk_minutes if place is not None else None
    if minutes is None and value is not None and isinstance(value.value, int | float):
        minutes = float(value.value)

    lines: list[Line] = []
    if minutes is None:
        status: Status = "no_data"
        status_label = "Nije pronađeno"
        text = f"U podacima za okolicu ne nalazimo: {noun}."
    else:
        near = minutes <= WALK_LIMIT_MIN
        status = "good" if near else "info"
        status_label = "Do 15 min hoda" if near else "Više od 15 min hoda"
        what = f"{nearest_word.capitalize()} {noun} je {fmt_minutes(minutes)} hoda od adrese"
        if part.yes_no:
            answer = "Da" if near else "Ne unutar 15 minuta hoda"
            text = f"{answer} – {_lower_first(what)}"
        else:
            text = what
        if part.walking and place is not None and place.distance_m:
            text += f", zračnom linijom {fmt_metres(place.distance_m)}"
        text += "."
        name = place.name if place is not None else ""
        if name and name != "bez naziva":
            lines.append(Line(label="Najbliže", value=name))
        walk = f"{fmt_minutes(minutes)} hoda"
        if place is not None and place.distance_m:
            walk += f" (zračno {fmt_metres(place.distance_m)})"
        lines.append(Line(label="Pješice", value=walk))
        if count is not None:
            lines.append(Line(label="Unutar 15 min hoda", value=count.display))
    if any(p.source == "osm" for p in cat.places if p.category == topic) and topic in (
        "grocery",
        "playground",
        "recycling",
    ):
        text += " OpenStreetMap izvan gradova nije potpun, pa neko mjesto može nedostajati."
    used = [v for v in (value, count) if v is not None]
    return Block(
        topic=topic,
        title=DAILY_TITLES[topic],
        address=address,
        status=status,
        status_label=status_label,
        text=text,
        lines=lines,
        sources=[_fact(v) for v in used],
        method=[
            "Vrijeme hoda računa se po stvarnoj mreži ulica (Valhalla, OpenStreetMap) "
            "brzinom od 4,5 km/h; zračna udaljenost je ravna crta."
        ],
    )


def _category_block(report: Report, part: Part, address: str | None) -> Block | None:
    if part.topic in DAILY_KEYS:
        return _daily_block(report, part.topic, part, address)
    cat = _category(report, part.topic)
    if cat is None:
        return None
    if cat.id == "car_free":
        return _car_free_block(cat, address)
    return _environment_block(cat, part, address)


def _within(report: Report) -> list[tuple[str, str, float]]:
    """(topic, title, minutes) of the nearest place of every kind the report knows."""
    out: list[tuple[str, str, float]] = []
    daily = _category(report, "daily")
    if daily is not None:
        for topic in DAILY_KEYS:
            place = _nearest(daily.places, topic)
            value = _value(daily, f"nearest_{topic}")
            minutes = place.walk_minutes if place is not None else None
            if minutes is None and value is not None and isinstance(value.value, int | float):
                minutes = float(value.value)
            if minutes is not None:
                out.append((topic, DAILY_TITLES[topic], minutes))
    park = _value(_category(report, "green"), "nearest_park")
    if park is not None and isinstance(park.value, int | float):
        out.append(("green", "Park", float(park.value)))
    transit = _category(report, "transit")
    stop = _nearest(transit.places, "stop") if transit is not None else None
    if stop is not None and stop.walk_minutes is not None:
        out.append(("transit", "Stajalište", stop.walk_minutes))
    return sorted(out, key=lambda item: item[2])


def _nearby_block(report: Report, part: Part, address: str | None) -> Block:
    places = _within(report)
    block = Block(topic="nearby", title="Što je u blizini", address=address, text="")
    if not places:
        block.text = "U podacima za okolicu nema mjesta s izračunatim vremenom hoda."
        return block
    if part.minutes is not None:
        limit = part.minutes
        inside = [p for p in places if p[2] <= limit]
        block.text = (
            f"Unutar {limit} minuta hoda je {len(inside)} od {len(places)} vrsta mjesta koje "
            "pratimo."
            if inside
            else f"Unutar {limit} minuta hoda nema nijednog mjesta koje pratimo."
        )
        block.chips = [Chip(label=f"{t} · {fmt_minutes(m)}", tone="good") for _, t, m in inside]
        block.chips += [
            Chip(label=f"{t} · {fmt_minutes(m)}", tone="missing") for _, t, m in places if m > limit
        ][:4]
    else:
        first = places[:3]
        listed = ", ".join(f"{t.lower()} ({fmt_minutes(m)})" for _, t, m in first)
        block.text = f"Najbliže su {listed}."
        block.chips = [
            Chip(label=f"{t} · {fmt_minutes(m)}", tone="good" if m <= WALK_LIMIT_MIN else "missing")
            for _, t, m in places[:8]
        ]
    block.method = [
        "Minute hoda do najbližeg mjesta svake vrste, po stvarnoj mreži ulica brzinom od 4,5 km/h."
    ]
    return block


def _strengths(report: Report) -> tuple[list[tuple[str, str]], list[tuple[str, str]]]:
    """(title, status) of the categories rated good and of those rated weaker."""
    good: list[tuple[str, str]] = []
    weak: list[tuple[str, str]] = []
    for cat in report.categories:
        if cat.group == "daily":
            continue
        if cat.status == "good":
            good.append((cat.title, cat.status_label.lower()))
        elif cat.status in ("warning", "bad"):
            weak.append((cat.title, cat.status_label.lower()))
    for topic, title, minutes in _within(report):
        if topic in ("kindergarten", "school", "doctor", "pharmacy", "grocery") and (
            minutes > WALK_LIMIT_MIN
        ):
            weak.append((title, f"{fmt_minutes(minutes)} hoda"))
    return good, weak


def _chips(good: list[tuple[str, str]], weak: list[tuple[str, str]]) -> list[Chip]:
    return [Chip(label=f"{t} · {s}", tone="good") for t, s in good] + [
        Chip(label=f"{t} · {s}", tone="missing") for t, s in weak
    ]


def _pros_cons_block(report: Report, address: str | None) -> Block:
    good, weak = _strengths(report)
    said = []
    if good:
        said.append("Dobro ocijenjeno: " + _join([t.lower() for t, _ in good]) + ".")
    if weak:
        said.append("Slabije: " + _join([t.lower() for t, _ in weak]) + ".")
    if not said:
        said.append("Nijedna tema nema izrazito dobru ni lošu ocjenu.")
    said.append("Ovo je pregled kategorija iz izvještaja, a ne savjet o kupnji.")
    return Block(
        topic="pros_cons",
        title="Prednosti i slabosti",
        address=address,
        text=" ".join(said),
        chips=_chips(good, weak),
    )


def _overview_block(report: Report, address: str | None) -> Block:
    good, weak = _strengths(report)
    chips = _chips(good[:3], weak[:3])
    return Block(
        topic="overview",
        title="Ukratko",
        address=address,
        text=" ".join(report.summary),
        chips=chips,
    )


def _limits_block(report: Report, address: str | None) -> Block:
    chips: list[Chip] = []
    unknown = _value(_category(report, "car_free"), "needs_unknown")
    if unknown is not None:
        chips += [
            Chip(label=f"nije provjereno: {u}", tone="unknown") for u in unknown.display.split(", ")
        ]
    for cat in report.categories:
        if cat.status == "no_data":
            chips.append(Chip(label=f"{cat.title}: nema podataka", tone="unknown"))
        elif any(v.kind == "estimate" for v in cat.values):
            chips.append(Chip(label=f"{cat.title}: gruba procjena", tone="unknown"))
    if _category(report, "air") is not None:
        chips.append(Chip(label="Zrak: model na mreži od 1 km, ne mjerenje", tone="unknown"))
    if _category(report, "flood") is not None:
        chips.append(Chip(label="Poplave: samo riječne, ne bujice ni more", tone="unknown"))
    chips.append(
        Chip(
            label="bez podataka: " + ", ".join(g.title.lower() for g in GAPS.values()),
            tone="unknown",
        )
    )
    return Block(
        topic="limits",
        title="Što ne znamo",
        address=address,
        text="Ovo ne možemo procijeniti ili je samo procjena:",
        chips=chips,
    )


def _population_block(report: Report, address: str | None) -> Block:
    pop = report.location.population
    settlement = report.location.settlement or "naselje"
    block = Block(topic="population", title="Naselje", address=address, text="")
    if pop is None or not isinstance(pop.value, int | float):
        block.text = "Broj stanovnika naselja nije poznat."
        return block
    n = int(pop.value)
    block.text = f"U naselju {settlement} prema Popisu 2021. živi {fmt_int(n)} stanovnika."
    block.lines = [Line(label="Stanovnika", value=fmt_int(n))]
    block.sources = [_fact(pop)]
    return block


_QUESTION_START = re.compile(
    r"^(?:gdje (?:je|su)|ima li|imaju li|postoji li|je li|koliko je do|a)\s+(?:u blizini\s+)?",
    re.IGNORECASE,
)


def _asked_about(clause: str) -> str:
    """ "Gdje je najbliži pikado klub" -> "najbliži pikado klub"."""
    return _QUESTION_START.sub("", clause.strip()).rstrip("?!. ") or clause


def _simple_block(part: Part) -> Block:
    if part.kind == "purchase":
        return Block(
            topic="purchase",
            title="Savjet o kupnji",
            text=(
                "Ne dajem savjete o tome treba li kupiti nekretninu ni isplati li se. Mogu reći "
                "činjenice o okolišu i onome što je blizu pješice; za odluku se posavjetujte sa "
                "stručnjacima (procjenitelj, odvjetnik)."
            ),
        )
    if part.kind == "scope":
        return Block(
            topic="scope",
            title="Izvan opsega",
            text=(
                "Cijene, krediti, vlasništvo i gradnja nisu u ovim podacima. Za to su nadležni "
                "zemljišnoknjižni odjel općinskog suda, katastar, banka ili ovlašteni procjenitelj."
            ),
        )
    if part.kind == "gap":
        gap = GAPS[part.topic]
        return Block(
            topic=part.topic,
            title=gap.title,
            status="no_data",
            status_label="Nema podataka",
            text=gap.sentence,
        )
    if part.kind == "explain":
        title = {
            "flood": "Poplave",
            "air": "Kvaliteta zraka",
            "green": "Zelenilo i hlad",
            "noise": "Udaljenost od prometnica",
            "solar": "Sunce na krovu",
            "car_free": "Život bez auta",
            "fire": "Požari raslinja",
            "transit": "Javni prijevoz",
        }[part.topic]
        return Block(
            topic=part.topic, title=f"{title}: što to znači", text=EXPLANATIONS[part.topic]
        )
    # uncovered
    return Block(
        topic="uncovered",
        title="Nije u podacima",
        status="no_data",
        status_label="Nema podataka",
        text=f"Za „{_asked_about(part.clause)}” nemamo podatke, pa to ne mogu procijeniti.",
    )


REPORT_KINDS = {"category", "overview", "pros_cons", "nearby", "limits", "population"}


def _blocks_for(part: Part, reports: list[Report]) -> list[Block]:
    if part.kind not in REPORT_KINDS:
        return [_simple_block(part)]
    blocks: list[Block] = []
    for i, report in enumerate(reports):
        address = _address(report, i, len(reports))
        block: Block | None
        if part.kind == "category":
            block = _category_block(report, part, address)
        elif part.kind == "overview":
            block = _overview_block(report, address)
        elif part.kind == "pros_cons":
            block = _pros_cons_block(report, address)
        elif part.kind == "nearby":
            block = _nearby_block(report, part, address)
        elif part.kind == "limits":
            block = _limits_block(report, address)
        else:
            block = _population_block(report, address)
        if block is not None:
            blocks.append(block)
    return blocks


def _address(report: Report, index: int, total: int) -> str | None:
    if total == 1:
        return None
    label = report.location.label
    return f"Adresa {'A' if index == 0 else 'B'}" + (f" ({label})" if label else "")


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
            v = _value(_category(r, cat_id), key)
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
            v = _value(_category(r, cat_id), f"nearest_{cat_id}")
            times.append(v.value if v and v.unit == "min" and isinstance(v.value, float) else None)
        a, b = times
        if a is None or b is None or round(a) == round(b):
            return None
        return f"Pješice je bliže s adrese {'A' if a < b else 'B'}."
    return None


def _join(items: list[str]) -> str:
    """ "a, b i c"; "te" before the last item when a title already has "i" in it."""
    if len(items) == 1:
        return items[0]
    last = " te " if any(" i " in item for item in items) else " i "
    return ", ".join(items[:-1]) + last + items[-1]


def _summary(blocks: list[Block]) -> str | None:
    """One sentence on top when more than two topics were asked."""
    topical = [b for b in blocks if b.status is not None and b.address is None]
    if len(topical) <= 2:
        return None
    good = [b.title.lower() for b in topical if b.status == "good"]
    weak = [b.title.lower() for b in topical if b.status in ("warning", "bad")]
    unknown = [b.title.lower() for b in topical if b.status == "no_data"]
    said = []
    if good:
        said.append(f"dobro {'stoje' if len(good) > 1 else 'stoji'} {_join(good)}")
    if weak:
        said.append(f"slabije {_join(weak)}")
    if unknown:
        said.append(f"bez podataka {_join(unknown)}")
    if not said:
        return None
    return "Ukratko: " + "; ".join(said) + "."


def _suggestions(topics: list[str]) -> list[str]:
    out: list[str] = []
    for topic in topics:
        for q in FOLLOW_UPS.get(topic, ()):
            if q not in out:
                out.append(q)
    for q in DEFAULT_SUGGESTIONS:
        if len(out) >= 6:
            break
        if q not in out:
            out.append(q)
    return out[:6]


def _plain(summary: str | None, blocks: list[Block]) -> str:
    parts = [summary] if summary else []
    for b in blocks:
        head = f"{b.title}" + (f" ({b.address})" if b.address else "")
        parts.append(f"{head}: {b.text}")
    return " ".join(parts)


def answer(
    request: AssistantRequest,
    build: Callable[[float, float, str | None], Report],
) -> AssistantReply:
    mode: Literal["rules", "llm"] = "rules"
    parts = understand_rules(request.question, request.context)
    if not parts:
        from_model = understand_llm(request.question)
        if from_model:
            parts, mode = from_model, "llm"

    where = "ove adrese" if len(request.locations) > 1 else "ovu adresu"
    if not parts:
        block = Block(
            topic="unknown",
            title="Ne razumijem pitanje",
            text=(
                f"To pitanje ne mogu povezati s podacima za {where}. Odgovaram o okolišu "
                "(poplave, zrak, zelenilo, promet) i o tome što je blizu pješice. Pokušajte npr. "
                f"„{EXAMPLES[0]}” ili „{EXAMPLES[1]}”"
            ),
        )
        return AssistantReply(
            answer=block.text, blocks=[block], suggestions=list(EXAMPLES), mode=mode
        )

    reports: list[Report] = []
    if any(p.kind in REPORT_KINDS for p in parts):
        reports = [build(p.lat, p.lon, p.label) for p in request.locations]

    blocks: list[Block] = []
    comparisons: list[str] = []
    for part in parts:
        blocks += _blocks_for(part, reports)
        if part.kind == "category":
            sentence = _comparison(reports, part.topic)
            if sentence:
                comparisons.append(sentence)

    summary = " ".join(comparisons) or _summary(blocks)
    topics = [p.topic for p in parts if p.kind in ("category", "explain")]
    topics += [p.kind for p in parts if p.kind in FOLLOW_UPS and p.kind != "category"]
    facts: list[Fact] = []
    links: list[Link] = []
    for b in blocks:
        facts += [f for f in b.sources if f not in facts]
        links += [link for link in b.links if link not in links]
    return AssistantReply(
        answer=_plain(summary, blocks),
        summary=summary,
        blocks=blocks,
        topics=[t for t in dict.fromkeys(topics) if t in CATEGORY_KEYWORDS],
        suggestions=_suggestions(topics),
        facts=facts,
        links=links,
        mode=mode,
    )
