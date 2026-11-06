"""Address search over the processed address table (no external geocoder).

addresses.parquet columns: street, housenumber, place, postcode, settlement_code, lon, lat, source
settlements.parquet columns: name, municipality, county, code, lon, lat, source, center_source

A query is read the way people write addresses: street and house number (12, 12a, 12 A, 12/B,
25/2, bb), then the settlement, town or municipality, with or without a comma, a postcode or
"Hrvatska". When the house number is not in the register the street is offered, and when the
street is not found the settlement, each with a note saying so.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from functools import lru_cache

import pyarrow.parquet as pq
from pydantic import BaseModel

from app.config import get_settings

_GENERIC = {"ulica", "ul", "u"}
_TRANSLIT = str.maketrans({"đ": "d", "Đ": "d"})
# One house number token after folding: 12, 12a, 12-a, 12/b, 25/2, 12a/1.
_NUMBER = re.compile(r"(\d{1,4})(?:[-/]?([a-z]))?(?:/(\d{1,3}))?")
_POSTCODE = re.compile(r"(?<![\d/])[1-5]\d{4}(?![\d/])")
_COUNTRY = {"hrvatska", "croatia", "republika hrvatska"}
_UNIT_PREFIX = re.compile(r"^(?:grad|opcina) ")
_MAX_PLACE_WORDS = 5

# Endings of names in streets: "Bušićeva" and "Brune Bušića" share "busic".
_ENDINGS = ("eva", "ova", "ina", "og", "a", "e", "i")
_RENAMED = 8  # match score of a street found only through its stem, after every other

# How fully a suggestion answers the query, best first.
_EXACT, _OTHER_NUMBER, _STREET_INSTEAD, _SETTLEMENT_INSTEAD = range(4)


def _fold(text: str) -> str:
    text = text.translate(_TRANSLIT).lower()
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c))


def normalize(text: str) -> str:
    """Lowercase, strip diacritics and punctuation: 'Ulica Đ. Šimića' -> 'ulica d simica'.

    'đ' and the common spelling 'dj' both become 'd', so 'Đure', 'Djure' and 'Dure' match.
    """
    return re.sub(r"[^a-z0-9]+", " ", _fold(text)).replace("dj", "d").strip()


def number_key(housenumber: str) -> str:
    """'12 A', '12/b' and '12-a' -> '12a'; '25 / 2' -> '25/2'; '12A/1' -> '12a/1'."""
    text = re.sub(r"\s*([-/])\s*", r"\1", _fold(housenumber).strip())
    text = re.sub(r"(\d)\s+([a-z])$", r"\1\2", text)
    m = _NUMBER.fullmatch(text)
    if m is None:
        return re.sub(r"\s+", "", text)
    number, letter, sub = m.groups()
    return number + (letter or "") + (f"/{sub}" if sub else "")


def _stem(word: str) -> str:
    """Strip one name ending: 'busiceva', 'busica' -> 'busic'; 'teslina', 'tesle' -> 'tesl'."""
    for end in _ENDINGS:
        if word.endswith(end) and len(word) - len(end) >= 4:
            return word[: -len(end)]
    return word


def _join(*notes: str | None) -> str | None:
    return " ".join(n for n in notes if n) or None


def _unit(name: str) -> str:
    """Normalised settlement or municipality name without "Grad" or "Općina"."""
    return _UNIT_PREFIX.sub("", normalize(name))


class Suggestion(BaseModel):
    label: str
    lat: float
    lon: float
    kind: str  # "address", "street" or "settlement"
    source: str
    note: str | None = None  # what was not found, when a street or settlement is offered instead


@dataclass
class _Street:
    street: str
    place: str
    street_norm: str
    place_norm: str
    municipality_norm: str
    numbers: dict[str, int]  # number key -> row index
    postcodes: set[str] = field(default_factory=set)


@dataclass(frozen=True)
class Query:
    """One reading of what was typed."""

    street: str  # normalised words
    number: str = ""  # number key, "" when there is none
    place: str = ""  # normalised settlement, town or municipality
    postcode: str = ""
    no_number: bool = False  # "bb" (bez broja)


class Geocoder:
    def __init__(
        self,
        streets: list[_Street],
        lon: list[float],
        lat: list[float],
        sources: list[str],
        settlements: list[Suggestion],
    ) -> None:
        self.streets = streets
        self.lon = lon
        self.lat = lat
        self.sources = sources
        self.settlements = settlements
        self.settlement_norm = [normalize(s.label.split(",")[0]) for s in settlements]
        self.settlement_unit = [_unit(s.label.split(", ", 1)[-1]) for s in settlements]
        self.places = set(self.settlement_norm) | set(self.settlement_unit)
        self.by_token: dict[str, list[int]] = {}
        for i, st in enumerate(streets):
            for token in set(st.street_norm.split()):
                self.by_token.setdefault(token[:3], []).append(i)

    @classmethod
    def from_rows(
        cls,
        rows: dict[str, list[str] | list[float]],
        settlements: list[Suggestion] | None = None,
        municipalities: dict[str, str] | None = None,
    ) -> Geocoder:
        """Group address rows by street; `municipalities` maps settlement codes to names."""
        groups: dict[tuple[str, str], _Street] = {}
        streets_col = rows["street"]
        codes = rows.get("settlement_code")
        postcodes = rows.get("postcode")
        units = municipalities or {}
        for i in range(len(streets_col)):
            street = str(streets_col[i])
            place = str(rows["place"][i] or "")
            key = (normalize(street), normalize(place))
            st = groups.get(key)
            if st is None:
                code = str(codes[i]) if codes is not None else ""
                st = _Street(street, place, key[0], key[1], _unit(units.get(code, "")), {})
                groups[key] = st
            st.numbers.setdefault(number_key(str(rows["housenumber"][i])), i)
            if postcodes is not None and postcodes[i]:
                st.postcodes.add(str(postcodes[i]))
        return cls(
            streets=list(groups.values()),
            lon=[float(v) for v in rows["lon"]],
            lat=[float(v) for v in rows["lat"]],
            sources=[str(v) for v in rows["source"]],
            settlements=settlements or [],
        )

    # --- Reading the query ------------------------------------------------------------------

    def parse(self, query: str) -> list[Query]:
        """Readings of the query, the most likely first."""
        text = _fold(query)
        postcode = ""
        found = _POSTCODE.search(text)
        if found:
            postcode = found.group(0)
            text = f"{text[: found.start()]} {text[found.end() :]}"
        # "25 / 2", "12 - a", "12/ B" -> one number token; names like "Bale - Valle" stay apart.
        text = re.sub(r"(\d)\s*([-/])\s*([a-z0-9])", r"\1\2\3", text)
        parts = [_tokens(p) for p in text.split(",")]
        parts = [p for p in parts if p and " ".join(p) not in _COUNTRY]
        if not parts:
            return []
        head, rest = parts[0], [t for p in parts[1:] for t in p]
        while len(head) > 1 and head[-1] in _COUNTRY:
            head = head[:-1]
        no_number = "bb" in head[1:]
        head = [t for i, t in enumerate(head) if not (i and t == "bb")]
        place = _UNIT_PREFIX.sub("", " ".join(rest))

        readings: list[Query] = []
        split = self._split_number(head, comma_place=bool(place))
        if split is not None:
            street, number, after = split
            readings.append(Query(street, number, place or after, postcode, no_number))
        else:
            street = " ".join(head)
            if not place:
                for n in range(min(_MAX_PLACE_WORDS, len(head) - 1), 0, -1):
                    suffix = " ".join(head[-n:])
                    if suffix in self.places and any(w not in _GENERIC for w in head[:-n]):
                        readings.append(Query(" ".join(head[:-n]), "", suffix, postcode, no_number))
                        break
            readings.append(Query(street, "", place, postcode, no_number))
        return readings

    def _split_number(self, tokens: list[str], comma_place: bool) -> tuple[str, str, str] | None:
        """(street, number key, place written after the number) for the last house number.

        A number is never the first word ("1. ulica"). Words after the number count as a
        place only when they name one; otherwise the number belongs to the street name
        ("Ulica 1. svibnja").
        """
        for k in range(len(tokens) - 1, 0, -1):
            token = tokens[k]
            if not _NUMBER.fullmatch(token):
                continue
            used = 1
            nxt = tokens[k + 1] if k + 1 < len(tokens) else ""
            if token.isdigit() and len(nxt) == 1 and nxt.isalpha():  # "12 a"
                token, used = token + nxt, 2
            after = tokens[k + used :]
            place = " ".join(after)
            if not after:
                return " ".join(tokens[:k]), number_key(token), ""
            if not comma_place and _UNIT_PREFIX.sub("", place) in self.places:
                return " ".join(tokens[:k]), number_key(token), _UNIT_PREFIX.sub("", place)
        return None

    # --- Searching ----------------------------------------------------------------------------

    def _place_ok(self, st: _Street, place_q: str, postcode: str) -> bool:
        if place_q and (
            st.place_norm.startswith(place_q) or st.municipality_norm.startswith(place_q)
        ):
            return True
        if postcode and postcode in st.postcodes:
            return True
        return not place_q and not postcode

    def _match_streets(
        self, street_q: str, place_q: str, postcode: str = ""
    ) -> list[tuple[int, int]]:
        # Official street names often omit "ulica" and first names ("Bana Jelačića"),
        # so generic words are ignored and one of three or more words may be missing.
        tokens = [t for t in street_q.split() if t not in _GENERIC] or street_q.split()
        if not tokens:
            return []
        key = max(tokens, key=len)
        pool = self.by_token.get(key[:3], [])
        scored: list[tuple[int, int]] = []
        for i in pool:
            st = self.streets[i]
            if not self._place_ok(st, place_q, postcode):
                continue
            words = st.street_norm.split()
            if not any(w.startswith(key) for w in words):
                continue
            matched = sum(1 for t in tokens if any(w.startswith(t) for w in words))
            if st.street_norm == street_q:
                score = 0
            elif matched == len(tokens) and st.street_norm.startswith(street_q):
                score = 1
            elif matched == len(tokens):
                score = 2
            elif len(tokens) >= 3 and matched >= len(tokens) - 1:
                score = 3
            else:
                continue
            scored.append((score + self._elsewhere(st, place_q), i))
        scored.sort(key=lambda s: (s[0], -len(self.streets[s[1]].numbers)))
        return scored

    def _match_stems(self, street_q: str, place_q: str, postcode: str) -> list[tuple[int, int]]:
        """Streets whose official name is another form of the written one ("Brune Bušića"
        is "Bušićeva" in Split): the last written word and a street word share a stem."""
        tokens = [t for t in street_q.split() if t not in _GENERIC]
        if not tokens:
            return []
        key = _stem(tokens[-1])  # the surname comes last: "Nikole Tesle", "Brune Bušića"
        if len(key) < 4:
            return []
        found = [
            (_RENAMED + self._elsewhere(self.streets[i], place_q), i)
            for i in self.by_token.get(key[:3], [])
            if self._place_ok(self.streets[i], place_q, postcode)
            and any(_stem(w) == key for w in self.streets[i].street_norm.split())
        ]
        found.sort(key=lambda s: (s[0], -len(self.streets[s[1]].numbers)))
        return found

    @staticmethod
    def _elsewhere(st: _Street, place_q: str) -> int:
        """3 when the street is not in the written settlement but elsewhere in its town or
        municipality: the written settlement wins over a closer street name elsewhere."""
        return 0 if not place_q or st.place_norm.startswith(place_q) else 3

    def search(self, query: str, limit: int = 8) -> list[Suggestion]:
        ranked: list[tuple[int, int, int, Suggestion]] = []
        seen: set[tuple[str, float, float]] = set()
        for order, reading in enumerate(self.parse(query)):
            for rank, score, s in self._search_reading(reading, limit):
                if (s.label, s.lat, s.lon) not in seen:
                    seen.add((s.label, s.lat, s.lon))
                    ranked.append((rank, score, order, s))
        ranked.sort(key=lambda r: (r[0], r[1], r[2]))
        return [r[3] for r in ranked[:limit]]

    def _search_reading(self, q: Query, limit: int) -> list[tuple[int, int, Suggestion]]:
        """(how fully it answers, street match score, suggestion) for one reading."""
        out: list[tuple[int, int, Suggestion]] = []
        if not q.number and not q.place and not q.postcode:
            out += [(_EXACT, 0, s) for s in self._settlements_named(q.street, prefix=True)[:3]]
        # Other forms of the name ("Ivana Gundulića" for "Gundulićeva") are candidates too,
        # ranked after the written form; an exact house number decides between them.
        matches = self._match_streets(q.street, q.place, q.postcode)
        known = {i for _, i in matches}
        matches += [
            m for m in self._match_stems(q.street, q.place, q.postcode) if m[1] not in known
        ]
        matches.sort(key=lambda m: m[0])
        if not matches:
            if q.place:
                note = "Ulica nije pronađena u registru adresa; prikazano je središte naselja."
                named = self._settlements_named(q.place, prefix=True)
                same_name = [s for s in named if normalize(s.label.split(",")[0]) == q.place]
                for s in (same_name or named)[:2]:
                    out.append((_SETTLEMENT_INSTEAD, 0, s.model_copy(update={"note": note})))
            return out
        if not q.number:
            bb_note = (
                "Adrese bez kućnog broja (bb) nisu u registru; prikazana je sredina ulice."
                if q.no_number
                else None
            )
            out += [
                (_EXACT, sc, self._street(self.streets[i], _join(self._renamed(sc, i), bb_note)))
                for sc, i in matches[:limit]
            ]
            return out
        shown = q.number.upper()
        exact = [(sc, i) for sc, i in matches if q.number in self.streets[i].numbers]
        for sc, i in exact[:limit]:
            found = self._address(self.streets[i], q.number)
            out.append((_EXACT, sc, found.model_copy(update={"note": self._renamed(sc, i)})))
        if exact:
            return out
        base = re.match(r"\d+", q.number)
        if base and base.group(0) != q.number:
            note = f"Kućni broj {shown} nije u registru adresa; prikazan je broj {base.group(0)}."
            for sc, i in matches[:limit]:
                if base.group(0) in self.streets[i].numbers:
                    found = self._address(self.streets[i], base.group(0))
                    both = _join(self._renamed(sc, i), note)
                    out.append((_OTHER_NUMBER, sc, found.model_copy(update={"note": both})))
        best = matches[0][0]
        for sc, i in [m for m in matches if m[0] == best][:3]:
            st = self.streets[i]
            if st.street_norm == st.place_norm:
                # A village without street names: its centre, not the middle of all addresses.
                note = f"Kućni broj {shown} nije u registru adresa; prikazano je središte naselja."
                for s in self._settlements_named(st.place_norm, unit=st.municipality_norm)[:1]:
                    out.append((_SETTLEMENT_INSTEAD, sc, s.model_copy(update={"note": note})))
                continue
            note = f"Kućni broj {shown} nije u registru adresa; prikazana je sredina ulice."
            out.append((_STREET_INSTEAD, sc, self._street(st, _join(self._renamed(sc, i), note))))
        return out

    def _renamed(self, score: int, i: int) -> str | None:
        if score < _RENAMED:
            return None
        return f"Ulica je u registru adresa upisana kao „{self.streets[i].street}”."

    def _settlements_named(
        self, name: str, prefix: bool = False, unit: str = ""
    ) -> list[Suggestion]:
        """Settlements by name (or name prefix); `unit` prefers the given municipality.

        Only when no settlement has the name (a town or municipality written as the place),
        its settlements are offered.
        """
        indices = range(len(self.settlements))
        if prefix:
            found = [i for i in indices if self.settlement_norm[i].startswith(name)]
            found = found or [i for i in indices if self.settlement_unit[i] == name]
        else:
            found = [i for i in indices if self.settlement_norm[i] == name]
        # Stable sort: the exact name first, then the municipality; otherwise label length.
        found.sort(key=lambda i: (self.settlement_norm[i] != name, self.settlement_unit[i] != unit))
        return [self.settlements[i] for i in found]

    def _address(self, st: _Street, number: str) -> Suggestion:
        row = st.numbers[number]
        label = f"{st.street} {number.upper()}" + (f", {st.place}" if st.place else "")
        return self._suggestion(label, row, "address")

    def _street(self, st: _Street, note: str | None) -> Suggestion:
        rows = sorted(st.numbers.values())
        label = st.street + (f", {st.place}" if st.place else "")
        return self._suggestion(label, rows[len(rows) // 2], "street", note)

    def _suggestion(self, label: str, row: int, kind: str, note: str | None = None) -> Suggestion:
        return Suggestion(
            label=label,
            lat=round(self.lat[row], 6),
            lon=round(self.lon[row], 6),
            kind=kind,
            source=self.sources[row],
            note=note,
        )


def _tokens(part: str) -> list[str]:
    """Words of one comma-separated part; house number tokens keep their - and /."""
    out: list[str] = []
    for raw in part.split():
        if _NUMBER.fullmatch(raw):
            out.append(raw)
        else:
            out += normalize(raw).split()
    return out


@lru_cache
def get_geocoder() -> Geocoder:
    d = get_settings().processed_dir
    path = d / "addresses.parquet"
    columns = [
        "street",
        "housenumber",
        "place",
        "postcode",
        "settlement_code",
        "lon",
        "lat",
        "source",
    ]
    rows: dict[str, list[str] | list[float]] = {k: [] for k in columns}
    if path.exists():
        rows = pq.read_table(path, columns=columns).to_pydict()
    settlements: list[Suggestion] = []
    municipalities: dict[str, str] = {}
    spath = d / "settlements.parquet"
    if spath.exists():
        t = pq.read_table(spath).to_pydict()
        for i in range(len(t["name"])):
            municipalities[str(t["code"][i])] = str(t["municipality"][i])
            settlements.append(
                Suggestion(
                    label=f"{t['name'][i]}, {t['municipality'][i]}",
                    lat=round(float(t["lat"][i]), 6),
                    lon=round(float(t["lon"][i]), 6),
                    kind="settlement",
                    # Centre from the OSM place node when matched (ingest/centers.py).
                    source="osm"
                    if t.get("center_source", [""] * len(t["name"]))[i] == "osm_place"
                    else str(t["source"][i]),
                )
            )
        settlements.sort(key=lambda s: len(s.label))
    return Geocoder.from_rows(rows, settlements, municipalities)
