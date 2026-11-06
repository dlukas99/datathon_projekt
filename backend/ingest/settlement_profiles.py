"""Profiles of settlements for "Predloži mjesto za život".

For every settlement with at least MIN_POPULATION inhabitants the same analysis
as the address report runs at the settlement centre (ingest/centers.py):
floods, air, greenery, traffic, fires, walking access, public transport and
daily needs. Solar is left out (PVGIS is a live API and varies little across
Croatia). Needs the walking router (Valhalla) to be running.

Output: data/processed/settlement_profiles.parquet, one row per settlement with
facts and the 0–100 sub-score of each category (analysis/score.py).
"""

from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import httpx
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from analysis import score
from analysis.daily import car_free_category, daily_category, transit_category
from analysis.environment import (
    air_category,
    air_level,
    fire_category,
    flood_category,
    green_category,
    noise_category,
)
from analysis.walking import compute_reach
from app.config import get_settings
from app.layers import get_layers
from app.models import Category
from ingest.common import processed_dir, record_source

MIN_POPULATION = 200
DAILY_NEEDS = ("kindergarten", "school", "doctor", "pediatrician", "pharmacy", "grocery")


def _value(cat: Category, key: str) -> Any:
    return next((v.value for v in cat.values if v.key == key), None)


def profile(row: dict[str, Any]) -> dict[str, Any]:
    lat, lon = float(row["lat"]), float(row["lon"])
    layers = get_layers()
    reach = compute_reach(lat, lon, layers)
    cats = {
        "flood": flood_category(lon, lat),
        "air": air_category(lon, lat),
        "green": green_category(lon, lat, reach.nearest("park")),
        "noise": noise_category(lon, lat, layers),
        "fire": fire_category(lon, lat, layers),
        "car_free": car_free_category(reach),
        "transit": transit_category(reach, True),
        "daily": daily_category(reach),
    }
    out: dict[str, Any] = {
        "code": row["code"],
        "name": row["name"],
        "municipality": row["municipality"],
        "county": row["county"],
        "population": int(row["population"]),
        "lon": lon,
        "lat": lat,
        "router_ok": reach.router_ok,
        "flood_status": cats["flood"].status,
        "air_band": air_level(cats["air"]) or cats["air"].status_label.lower(),
        "pm25": _value(cats["air"], "pm25_annual"),
        "no2": _value(cats["air"], "no2_annual"),
        "tree_share": _value(cats["green"], "tree_share_300m"),
        "traffic_band": cats["noise"].status_label,
        "burnt_areas": _value(cats["fire"], "burnt_areas_2km"),
        "needs_15min": _value(cats["car_free"], "needs_within_15min"),
        "max_departures": _value(cats["transit"], "max_departures_per_hour"),
        "has_stops": bool(_value(cats["transit"], "stops_10min")),
    }
    for need in DAILY_NEEDS:
        out[f"has_{need}"] = bool(reach.within(need, 15.0))
    out["has_park"] = bool(reach.within("park", 15.0))
    for cid, cat in cats.items():
        out[f"score_{cid}"] = score.subscore(cat)
    return out


def run(workers: int = 4) -> None:
    try:
        httpx.get(f"{get_settings().valhalla_url}/status", timeout=5).raise_for_status()
    except httpx.HTTPError as exc:
        raise RuntimeError(
            "Valhalla ne radi: pokrenite je (docker compose -f deploy/docker-compose.dev.yml "
            "up -d) pa ponovite `uv run python -m ingest.settlement_profiles`."
        ) from exc
    d = processed_dir()
    settlements = pd.read_parquet(d / "settlements.parquet")
    population = pd.read_parquet(d / "settlement_population.parquet")
    merged = settlements.merge(population, left_on="code", right_on="settlement_code")
    rows: list[dict[str, Any]] = [
        {str(k): v for k, v in r.items()}
        for r in merged[merged["population"] >= MIN_POPULATION].to_dict("records")
    ]
    start = time.monotonic()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        results = list(pool.map(profile, rows))
    table = pd.DataFrame(results)
    pq.write_table(
        pa.Table.from_pandas(table, preserve_index=False), d / "settlement_profiles.parquet"
    )
    failed = int((~table["router_ok"]).sum())
    record_source(
        "settlement_profiles",
        title=f"Profili naselja (≥ {MIN_POPULATION} stanovnika), izračun aplikacije",
        publisher="izvedeno iz izvora navedenih na stranici Izvori",
        url="",
        license="CC BY 4.0 (izvedeni podaci); ulazni izvori zadržavaju svoje licence",
        retrieved_at=pd.Timestamp.now(tz="UTC").isoformat(timespec="seconds"),
        notes=json.dumps({"settlements": len(table), "router_failed": failed}),
    )
    print(
        f"profili naselja: {len(table)} naselja za {time.monotonic() - start:.0f} s, "
        f"bez mreže hoda: {failed}"
    )


if __name__ == "__main__":
    run()
