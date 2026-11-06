"""Address search check: 24 real addresses of primary schools, typed the way people type them.

The addresses come from the Ministry's register of primary schools
(data/raw/mzom/osnovne_skole.csv, public institutions only, CLAUDE.md rule 8). Each query
says what a correct first suggestion is; the script prints a Markdown table.

    cd backend && uv run python ../scripts/geocode_check.py
"""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.geocode import get_geocoder, normalize


@dataclass(frozen=True)
class Case:
    query: str
    area: str  # big city, town, village, island
    kind: str  # expected kind of the first suggestion: address, street or settlement
    places: tuple[str, ...]  # acceptable settlements in the label
    number: str = ""  # expected house number in the label, e.g. "23a"
    school: str = ""


CASES = [
    # Big cities
    Case(
        "Gundulićeva 23 A, Zagreb",
        "veliki grad",
        "address",
        ("Zagreb",),
        "23a",
        "OŠ Ivana Gundulića",
    ),
    Case("Jabukovac 30, Zagreb", "veliki grad", "address", ("Zagreb",), "30", "OŠ Jabukovac"),
    Case(
        "Joze Laurenčića bb, Zagreb", "veliki grad", "street", ("Zagreb",), "", "škola na adresi bb"
    ),
    Case("Ivana Rendića 6 Rijeka", "veliki grad", "address", ("Rijeka",), "6", "OŠ Brajda"),
    Case(
        "Brune Bušića 30, 21000 Split",
        "veliki grad",
        "address",
        ("Split",),
        "30",
        "COO Juraj Bonači",
    ),
    Case("Drinska 12/B, Osijek", "veliki grad", "address", ("Osijek",), "12b", "COO Ivan Štark"),
    Case("Ilica, Zagreb", "veliki grad", "street", ("Zagreb",)),
    # Towns
    Case(
        "Ulica pape Ivana Pavla II. 6, Požega",
        "manji grad",
        "address",
        ("Požega",),
        "6",
        "Katolička OŠ",
    ),
    Case("Slavonska 8, Pozega", "manji grad", "address", ("Požega",), "8", "OŠ Dobriše Cesarića"),
    Case(
        "Bartola Kašića 48 Vinkovci",
        "manji grad",
        "address",
        ("Vinkovci",),
        "48",
        "OŠ Bartola Kašića",
    ),
    Case(
        "Miroslava Kraljevića 15, 53000 Gospić",
        "manji grad",
        "address",
        ("Gospić",),
        "15",
        "OŠ dr. Jure Turića",
    ),
    Case(
        "Šetalište pazinske gimnazije 9, Pazin",
        "manji grad",
        "address",
        ("Pazin",),
        "9",
        "OŠ Vladimira Nazora",
    ),
    # Villages
    Case("Zrinska 8, Nijemci", "selo", "address", ("Nijemci",), "8", "OŠ Ivan Kozarac"),
    Case(
        "Sveti Martin pod Okićem 37b",
        "selo",
        "address",
        ("Sveti Martin pod Okićem",),
        "37b",
        "OŠ Mihaela Šiloboda",
    ),
    Case("Gora 61 a", "selo", "address", ("Gora",), "61a", "škola u Gori"),
    Case("Nijemci", "selo", "settlement", ("Nijemci",)),
    # Islands
    Case("Kroz Burak 81, Hvar", "otok", "address", ("Hvar",), "81", "OŠ Hvar"),
    Case("Ante Starčevića 1, Korcula", "otok", "address", ("Korčula",), "1", "OŠ Petra Kanavelića"),
    Case("Šetalište 20. travnja 56, Cres", "otok", "address", ("Cres",), "56", "OŠ Frane Petrića"),
    Case("Banjol 10, Rab", "otok", "address", ("Banjol", "Rab"), "10", "OŠ Ivana Rabljanina"),
    Case("Jelsa 161", "otok", "address", ("Jelsa",), "161", "OŠ Jelsa"),
    Case("1. ulica 25/2, Blato", "otok", "address", ("Blato",), "25/2", "OŠ Blato"),
    Case(
        "Omladinska 11, 51550 Mali Lošinj, Hrvatska",
        "otok",
        "address",
        ("Mali Lošinj",),
        "11",
        "OŠ Maria Martinolića",
    ),
    Case("Kroz Burak, Hvar", "otok", "street", ("Hvar",)),
]


def number_in(label: str) -> str:
    head = label.split(",")[0]
    words = head.split()
    tail = [w for w in words if any(ch.isdigit() for ch in w)]
    return normalize(tail[-1]).replace(" ", "/") if tail else ""


def verdict(case: Case, label: str, kind: str) -> str:
    place = normalize(label.split(",")[-1]) if "," in label else ""
    place_ok = any(normalize(p) == place for p in case.places)
    if kind == case.kind and place_ok:
        if case.kind != "address" or number_in(label) == case.number:
            return "točno"
        return "krivi broj"
    if not place_ok:
        return "krivo mjesto"
    return {"street": "samo ulica", "settlement": "samo naselje", "address": "adresa"}[kind]


def main() -> None:
    geocoder = get_geocoder()
    print("| # | Upit | Vrsta mjesta | Prvi prijedlog | Ocjena |")
    print("|---|---|---|---|---|")
    counts: dict[str, int] = {}
    for i, case in enumerate(CASES, 1):
        found = geocoder.search(case.query, limit=8)
        if found:
            first = found[0]
            shown = f"{first.label} ({first.kind})"
            note = getattr(first, "note", None)
            if note:
                shown += f": {note}"
            result = verdict(case, first.label, first.kind)
        else:
            shown, result = "ništa", "ništa"
        counts[result] = counts.get(result, 0) + 1
        print(f"| {i} | {case.query} | {case.area} | {shown} | {result} |")
    print()
    print("Ukupno: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))


if __name__ == "__main__":
    main()
