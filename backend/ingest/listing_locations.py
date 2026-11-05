"""Index Oglasi location ids for the "Pogledaj oglase" links (config/listing_locations.json).

Index Oglasi limits a search to a place only through a UUID inside the
`searchQuery` parameter; the slug in the path alone is ignored (the title says
"Split", the results cover the whole country). The UUID cannot be derived, so
this maintainer step asks Index's own route resolver once per slug,

    GET https://www.index.hr/oglasi/api/routes?pathname=/nekretnine/prodaja-stanova/{slug}/pretraga

and stores `slug -> {"type": "city" | "county", "id": UUID}` in the repository.
The frontend only reads that file; the app never calls Index at runtime.

Slugs come from the DGU administrative units (data/processed/admin_units.parquet):
every town or municipality and every county. Names shared by towns or
municipalities in more than one county (e.g. Otok) go to
`ambiguous_municipalities` and are never looked up, because one slug cannot tell
them apart; the listing links use the county for them.

Polite by design: one request per second, slugs already resolved or known to be
missing are skipped, progress is saved as it goes, and the run stops at the
first unexpected answer instead of retrying. It does not imitate a browser
session: if Index answers only inside one, the run stops and says so.

Run in backend/:  uv run python -m ingest.listing_locations [--offline]
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from collections import defaultdict
from collections.abc import Iterable
from datetime import date
from pathlib import Path
from typing import Any
from urllib.parse import unquote

import httpx
import pyarrow.parquet as pq

from app.config import REPO_ROOT
from ingest.common import get_json, processed_dir

OUTPUT = REPO_ROOT / "config" / "listing_locations.json"
ROUTES_URL = "https://www.index.hr/oglasi/api/routes"
ISTRIA = "Istarska županija"
SAVE_EVERY = 25
NOTE = (
    "Generira `uv run python -m ingest.listing_locations` (u mapi backend). "
    "index_oglasi: slug lokacije -> UUID iz https://www.index.hr/oglasi/api/routes "
    "(Index bez UUID-a zanemaruje mjesto u putanji); aplikacija Index ne zove. "
    "index_oglasi_not_found: slugovi za koje Index nema stranicu. "
    "ambiguous_municipalities: imena gradova i općina koja u DGU upravnim jedinicama "
    "postoje u više županija; poveznice za njih koriste županiju."
)

_FOLD = str.maketrans({"č": "c", "ć": "c", "š": "s", "ž": "z", "đ": "d"})


def slugify(name: str) -> str:
    """Croatian place name to a URL slug: "Đakovo" -> "dakovo", "Mali Lošinj" -> "mali-losinj".

    Same rules as `slugify` in frontend/src/lib/listings.ts.
    """
    folded = unicodedata.normalize("NFKD", name.lower().translate(_FOLD))
    plain = "".join(c for c in folded if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", plain).strip("-")


def municipality_name(name: str, county: str) -> str:
    """Name listing sites use for a town or municipality.

    Istrian units have official bilingual names ("Pula - Pola"); the sites use the
    Croatian part. Elsewhere " - " is part of the name ("Murter - Kornati").
    """
    if county == ISTRIA and " - " in name:
        return name.split(" - ", 1)[0]
    return name


def county_slug(name: str) -> str:
    """Short county slug: "Splitsko-dalmatinska županija" -> "splitsko-dalmatinska"."""
    return slugify(name.removesuffix(" županija"))


def plan(rows: Iterable[dict[str, Any]]) -> tuple[list[str], list[str]]:
    """Slugs to resolve (towns, municipalities, counties) and the ambiguous names.

    `rows` are DGU administrative units with `level`, `name` and `parent_name`
    (the county, for a town or municipality).
    """
    by_slug: dict[str, set[tuple[str, str]]] = defaultdict(set)
    counties: set[str] = set()
    for row in rows:
        if row["level"] == "municipality":
            name, county = str(row["name"]), str(row["parent_name"])
            by_slug[slugify(municipality_name(name, county))].add((name, county))
        elif row["level"] == "county":
            counties.add(county_slug(str(row["name"])))
    ambiguous = sorted({name for units in by_slug.values() if len(units) > 1 for name, _ in units})
    slugs = {slug for slug, units in by_slug.items() if len(units) == 1} | counties
    return sorted(slugs), ambiguous


def parse_route(payload: Any) -> dict[str, str] | None:
    """`{"type", "id"}` from a routes answer, or None when Index has no such page."""
    if not isinstance(payload, list) or not payload or not isinstance(payload[0], dict):
        raise ValueError(f"neočekivan odgovor: {str(payload)[:200]}")
    route = payload[0]
    if not route:
        return None
    query = json.loads(unquote(str(route["searchQuery"])))
    for key, kind in (("includeCityIds", "city"), ("includeCountyIds", "county")):
        ids = query.get(key)
        if ids:
            return {"type": kind, "id": str(ids[0])}
    return None


def resolve(slug: str) -> dict[str, str] | None:
    url = f"{ROUTES_URL}?pathname=/nekretnine/prodaja-stanova/{slug}/pretraga"
    return parse_route(get_json(url, min_interval=1.0))


def load(path: Path = OUTPUT) -> dict[str, Any]:
    if path.exists():
        data: dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
        return data
    return {}


def save(data: dict[str, Any], path: Path = OUTPUT) -> None:
    ordered = {
        "_note": NOTE,
        "updated": data.get("updated"),
        "ambiguous_municipalities": sorted(data.get("ambiguous_municipalities", [])),
        "index_oglasi": dict(sorted(data.get("index_oglasi", {}).items())),
        "index_oglasi_not_found": sorted(set(data.get("index_oglasi_not_found", []))),
    }
    path.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(*, offline: bool = False) -> int:
    rows = pq.read_table(
        processed_dir() / "admin_units.parquet", columns=["level", "name", "parent_name"]
    ).to_pylist()
    slugs, ambiguous = plan(rows)
    data = load()
    data["ambiguous_municipalities"] = ambiguous
    found: dict[str, dict[str, str]] = data.setdefault("index_oglasi", {})
    missing: list[str] = data.setdefault("index_oglasi_not_found", [])
    pending = [s for s in slugs if s not in found and s not in missing]
    print(f"index oglasi: {len(slugs)} slugova, {len(found)} poznato, {len(pending)} za provjeru")
    print(f"dvoznačna imena (koristi se županija): {', '.join(ambiguous) or 'nema'}")
    stopped: str | None = None
    if not offline:
        for i, slug in enumerate(pending, 1):
            try:
                location = resolve(slug)
            except (httpx.HTTPError, ValueError, KeyError) as exc:
                stopped = f"{slug}: {exc}"
                break
            if location is None:
                missing.append(slug)
            else:
                found[slug] = location
            data["updated"] = date.today().isoformat()
            if i % SAVE_EVERY == 0:
                save(data)
    save(data)
    left = [s for s in slugs if s not in found and s not in missing]
    if missing:
        print(f"Index nema stranicu za {len(missing)}: {', '.join(sorted(missing))}")
    if stopped:
        print(
            f"Zaustavljeno na {stopped}. Index trenutačno ne odgovara na izravne zahtjeve "
            "(npr. HTTP 400 izvan sesije svoje stranice); skripta namjerno ne oponaša "
            "preglednik. Poveznice za mjesta bez UUID-a koriste županiju ili traže ručni "
            f"odabir mjesta. Nedostaje još {len(left)} slugova."
        )
        return 1
    if left:
        print(f"Nedostaje još {len(left)} slugova (pokrenite bez --offline).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument(
        "--offline", action="store_true", help="bez mreže: samo dvoznačna imena i popis"
    )
    args = parser.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    return run(offline=args.offline)


if __name__ == "__main__":
    sys.exit(main())
