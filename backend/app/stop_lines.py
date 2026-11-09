"""Which lines stop at stops without an open timetable (from OSM route relations).

The table comes from ingest/transit_lines.py. It names lines, never frequencies: where the
operator publishes no open timetable we can say "tram 1 and 2 stop here", not how often.
"""

from __future__ import annotations

import re
from functools import lru_cache

import numpy as np
import pandas as pd

from app.config import get_settings
from app.models import Place

# A route's stop node and the stop in the report are the same stop within this distance
# (a platform and the stop position on the road are often 10-20 m apart).
MATCH_M = 30.0
MAX_REFS = 10  # per mode and operator; the rest is "i još N"
MODE_WORDS = {"tram": "tramvaj", "trolleybus": "trolejbus", "bus": "autobus"}


@lru_cache
def _table() -> pd.DataFrame | None:
    path = get_settings().processed_dir / "osm_stop_lines.parquet"
    if not path.exists():
        return None
    return pd.read_parquet(path)


def _natural(ref: str) -> tuple[int, str]:
    m = re.match(r"\d+", ref)
    return (int(m.group(0)) if m else 10**6, ref)


def _operator_key(name: str) -> str:
    return re.sub(r"[^a-z0-9čćđšž]", "", re.sub(r"d\.?\s?o\.?\s?o\.?", "", name.lower()))


def _join(items: list[str]) -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " i " + items[-1]


def describe(rows: pd.DataFrame) -> str | None:
    """'tramvaj 1 i 2, autobus 4 i 7 (GPP Osijek); autobus 21 (Promet Split)'."""
    if rows.empty:
        return None
    # A relation without an operator that repeats a line of a named operator is the same line.
    key = rows["mode"] + "|" + rows["ref"]
    unnamed = rows["operator"] == ""
    rows = rows[~(unnamed & key.isin(set(key[~unnamed])))]
    # One operator under several spellings ("Pulapromet d.o.o.", "pulapromet", "Pula promet").
    op_key = rows["operator"].map(_operator_key)
    parts: list[str] = []
    for key_ in op_key.value_counts().index:  # the operator with most stops first
        group = rows[op_key == key_]
        operator = str(group["operator"].value_counts().index[0])  # its most used spelling
        modes: list[str] = []
        for mode in ("tram", "trolleybus", "bus"):
            refs = sorted(set(group.loc[group["mode"] == mode, "ref"]), key=_natural)
            if not refs:
                continue
            shown = refs[:MAX_REFS]
            text = f"{MODE_WORDS[mode]} {_join(shown)}"
            if len(refs) > MAX_REFS:
                text = f"{MODE_WORDS[mode]} {', '.join(shown)} i još {len(refs) - MAX_REFS}"
            modes.append(text)
        if modes:
            parts.append(", ".join(modes) + (f" ({operator})" if operator else ""))
    return "; ".join(parts) or None


def lines_at(stops: list[Place]) -> str | None:
    """Lines of the route relations that stop at any of these stops, or None."""
    table = _table()
    if table is None or table.empty or not stops:
        return None
    lat = table["lat"].to_numpy()
    lon = table["lon"].to_numpy()
    hit = np.zeros(len(table), dtype=bool)
    for stop in stops:
        dy = (lat - stop.lat) * 111_320.0
        dx = (lon - stop.lon) * 111_320.0 * np.cos(np.radians(stop.lat))
        hit |= np.hypot(dx, dy) <= MATCH_M
    return describe(table[hit])
