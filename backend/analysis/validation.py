"""Compare the app's air values (EEA 2024 map) with the nearest official station.

For each city: the settlement centre plus three primary schools within 4 km,
picked to be far apart (public institutions only). Prints a Markdown table.

    uv run python -m analysis.validation
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from analysis.environment import read_air
from app.config import get_settings
from app.geo import to_htrs

CITIES = ("Zagreb", "Osijek", "Požega")
NAMES = {"pm25": "PM2,5", "no2": "NO2"}
TYPE_HR = {"traffic": "prometna", "background": "pozadinska", "industrial": "industrijska"}
SCHOOL_RADIUS_M = 4000.0


def _num(x: float, d: int = 1) -> str:
    return f"{x:.{d}f}".replace(".", ",")


def locations(city: str) -> list[tuple[str, float, float]]:
    d = get_settings().processed_dir
    s = pd.read_parquet(d / "settlements.parquet")
    centre = s[s["name"] == city].iloc[0]
    cx, cy = to_htrs(float(centre["lon"]), float(centre["lat"]))
    pois = pd.read_parquet(d / "pois.parquet")
    schools = pois[(pois["category"] == "school") & pois["source"].isin(["mzom_skole", "zg_skole"])]
    pts = [(f"središte ({city})", float(centre["lon"]), float(centre["lat"]), cx, cy)]
    cands = []
    for name, lon, lat in zip(schools["name"], schools["lon"], schools["lat"], strict=True):
        x, y = to_htrs(float(lon), float(lat))
        if math.hypot(x - cx, y - cy) <= SCHOOL_RADIUS_M:
            cands.append((str(name), float(lon), float(lat), x, y))
    # Farthest-point sampling: each next school is the one farthest from those chosen.
    while len(pts) < 4 and cands:
        best = max(cands, key=lambda c: min(math.hypot(c[3] - p[3], c[4] - p[4]) for p in pts))
        cands.remove(best)
        pts.append(best)
    return [(n, lon, lat) for n, lon, lat, _, _ in pts]


def nearest_station(stations: pd.DataFrame, lon: float, lat: float) -> tuple[pd.Series, float]:
    x, y = to_htrs(lon, lat)
    xy = np.array(
        [to_htrs(float(a), float(b)) for a, b in zip(stations["lon"], stations["lat"], strict=True)]
    )
    dist = np.hypot(xy[:, 0] - x, xy[:, 1] - y)
    i = int(dist.argmin())
    return stations.iloc[i], float(dist[i])


def table() -> str:
    st = pd.read_parquet(get_settings().processed_dir / "stations_2024.parquet")
    st = st[st["mean"].notna()]
    lines = [
        "| Grad | Lokacija | Tvar | Aplikacija (EEA karta) | Najbliža postaja (vrsta) "
        "| Udaljenost | Postaja, prosjek 2024. | Razlika | Zaključak |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for city in CITIES:
        for name, lon, lat in locations(city):
            for pol in ("pm25", "no2"):
                app = read_air(lon, lat, pol)
                station, dist = nearest_station(st[st["pollutant"] == pol], lon, lat)
                diff = None if app is None else app - float(station["mean"])
                kind = TYPE_HR.get(str(station["type"]), str(station["type"]))
                if diff is None:
                    verdict = "nema vrijednosti na karti"
                elif dist > 10000:
                    verdict = "postaja je daleko, usporedba je samo okvirna"
                elif abs(diff) <= 2:
                    verdict = "dobro slaganje"
                elif diff < 0 and kind == "prometna":
                    verdict = "karta niža: postaja je uz promet, karta prikazuje pozadinu"
                elif diff < 0:
                    verdict = "karta niža od mjerenja"
                else:
                    verdict = "karta viša od mjerenja"
                lines.append(
                    f"| {city} | {name} | {NAMES[pol]} | "
                    f"{'–' if app is None else _num(app)} | {station['station_name']} ({kind}) | "
                    f"{_num(dist / 1000)} km | {_num(float(station['mean']))} | "
                    f"{'–' if diff is None else _num(diff)} | {verdict} |"
                )
    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    print(table())
