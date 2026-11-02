"""Address search over the processed address table (no external geocoder).

addresses.parquet columns: street, housenumber, place, lon, lat, source
settlements.parquet columns: name, municipality, county, lon, lat, source
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache

import pyarrow.parquet as pq
from pydantic import BaseModel

from app.config import get_settings

_NUMBER_RE = re.compile(r"^\d+[a-z]?$")
_GENERIC = {"ulica", "ul", "u"}
_TRANSLIT = str.maketrans({"đ": "d", "Đ": "d"})


def normalize(text: str) -> str:
    """Lowercase, strip diacritics and punctuation: 'Ulica Đ. Šimića' -> 'ulica d simica'.

    'đ' and the common spelling 'dj' both become 'd', so 'Đure', 'Djure' and 'Dure' match.
    """
    text = text.translate(_TRANSLIT).lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9]+", " ", text).replace("dj", "d")
    return text.strip()


def _number_key(housenumber: str) -> str:
    return normalize(housenumber).replace(" ", "")


class Suggestion(BaseModel):
    label: str
    lat: float
    lon: float
    kind: str  # "address", "street" or "settlement"
    source: str


@dataclass
class _Street:
    street: str
    place: str
    street_norm: str
    place_norm: str
    numbers: dict[str, int]  # normalized house number -> row index


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
        self.by_token: dict[str, list[int]] = {}
        for i, st in enumerate(streets):
            for token in set(st.street_norm.split()):
                self.by_token.setdefault(token[:3], []).append(i)

    @classmethod
    def from_rows(
        cls,
        rows: dict[str, list[str] | list[float]],
        settlements: list[Suggestion] | None = None,
    ) -> Geocoder:
        groups: dict[tuple[str, str], _Street] = {}
        streets_col = rows["street"]
        for i in range(len(streets_col)):
            street = str(streets_col[i])
            place = str(rows["place"][i] or "")
            key = (normalize(street), normalize(place))
            st = groups.get(key)
            if st is None:
                st = _Street(street, place, key[0], key[1], {})
                groups[key] = st
            st.numbers.setdefault(_number_key(str(rows["housenumber"][i])), i)
        return cls(
            streets=list(groups.values()),
            lon=[float(v) for v in rows["lon"]],
            lat=[float(v) for v in rows["lat"]],
            sources=[str(v) for v in rows["source"]],
            settlements=settlements or [],
        )

    def _match_streets(self, street_q: str, place_q: str) -> list[tuple[int, int]]:
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
            if place_q and not st.place_norm.startswith(place_q):
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
            scored.append((score, i))
        scored.sort(key=lambda s: (s[0], -len(self.streets[s[1]].numbers)))
        return scored

    def search(self, query: str, limit: int = 8) -> list[Suggestion]:
        parts = [p.strip() for p in query.split(",")]
        head = normalize(parts[0])
        place_q = normalize(" ".join(parts[1:])) if len(parts) > 1 else ""
        tokens = head.split()
        number = ""
        if tokens and _NUMBER_RE.match(tokens[-1]):
            number = tokens.pop()
        elif len(tokens) >= 2 and tokens[-2].isdigit() and len(tokens[-1]) == 1:
            number = tokens[-2] + tokens[-1]
            tokens = tokens[:-2]
        street_q = " ".join(tokens)
        results: list[Suggestion] = []

        if not number and not place_q:
            for name_norm, s in zip(self.settlement_norm, self.settlements, strict=True):
                if name_norm.startswith(head):
                    results.append(s)
                    if len(results) >= 3:
                        break

        for _, i in self._match_streets(street_q, place_q):
            st = self.streets[i]
            if number:
                row = st.numbers.get(number)
                if row is None:
                    continue
                label = f"{st.street} {self._display_number(st, number)}"
                kind = "address"
            else:
                rows = sorted(st.numbers.values())
                row = rows[len(rows) // 2]
                label = st.street
                kind = "street"
            if st.place:
                label += f", {st.place}"
            results.append(
                Suggestion(
                    label=label,
                    lat=round(self.lat[row], 6),
                    lon=round(self.lon[row], 6),
                    kind=kind,
                    source=self.sources[row],
                )
            )
            if len(results) >= limit:
                break
        return results

    @staticmethod
    def _display_number(st: _Street, number: str) -> str:
        return number.upper() if number[-1:].isalpha() else number


@lru_cache
def get_geocoder() -> Geocoder:
    d = get_settings().processed_dir
    path = d / "addresses.parquet"
    rows: dict[str, list[str] | list[float]] = {
        k: [] for k in ("street", "housenumber", "place", "lon", "lat", "source")
    }
    if path.exists():
        rows = pq.read_table(path, columns=list(rows)).to_pydict()
    settlements: list[Suggestion] = []
    spath = d / "settlements.parquet"
    if spath.exists():
        t = pq.read_table(spath).to_pydict()
        for i in range(len(t["name"])):
            settlements.append(
                Suggestion(
                    label=f"{t['name'][i]}, {t['municipality'][i]}",
                    lat=round(float(t["lat"][i]), 6),
                    lon=round(float(t["lon"][i]), 6),
                    kind="settlement",
                    source=str(t["source"][i]),
                )
            )
        settlements.sort(key=lambda s: len(s.label))
    return Geocoder.from_rows(rows, settlements)
