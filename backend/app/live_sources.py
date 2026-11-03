"""Live metadata from the national open data portal (CKAN API of data.gov.hr).

One `package_search` request returns the last modification date of every
dataset we use. Results are cached for an hour; the last good answer is kept on
disk so the page still shows dates when the portal does not respond.
"""

from __future__ import annotations

import json
import threading
import time
from datetime import UTC, datetime

import httpx
from pydantic import BaseModel

from app.config import get_settings

CKAN_SEARCH = "https://data.gov.hr/ckan/api/3/action/package_search"
DATASET_URL = "https://data.gov.hr/ckan/dataset/{name}"
CACHE_SECONDS = 3600

# Our source id -> CKAN dataset name on data.gov.hr
CKAN_DATASETS: dict[str, str] = {
    "dgu_ad": "adrese-inspire",
    "dgu_au": "upravne-jedinice-inspire",
    "dzs_popis": "statistika-u-nizu-popis-stanovnistva-kucanstava-i-stanova-2021",
    "mzom_vrtici": "djecji-vrtici",
    "mzom_skole": "osnovne-skole",
    "zg_vrtici": "geoportal-djecji-vrtici",
    "zg_skole": "geoportal-osnovne-skole",
    "autotrolej": "at-vozni-redovi",
    "gtfs_hzpp": "vozni-red-h-putni-kog-prijevoza-u-gtfs-obliku",
}


class LiveDataset(BaseModel):
    id: str
    ckan_name: str
    title: str
    organization: str
    metadata_modified: str | None
    url: str


class LiveSources(BaseModel):
    checked_at: str
    available: bool
    datasets: list[LiveDataset]


_lock = threading.Lock()
_cache: tuple[float, LiveSources] | None = None


def extra_datasets() -> dict[str, str]:
    """Municipal recycling datasets found by `make data` (see ingest/recycling.py)."""
    path = get_settings().processed_dir / "recycling_ckan.json"
    if not path.exists():
        return {}
    names: list[str] = json.loads(path.read_text(encoding="utf-8")).get("used", [])
    return {f"ckan:{n}": n for n in names}


def _fetch(datasets: dict[str, str]) -> list[LiveDataset]:
    names = " OR ".join(datasets.values())
    response = httpx.get(
        CKAN_SEARCH,
        params={"fq": f"name:({names})", "rows": len(datasets) + 5},
        headers={"User-Agent": get_settings().user_agent},
        timeout=10.0,
    )
    response.raise_for_status()
    results = {r["name"]: r for r in response.json()["result"]["results"]}
    out = []
    for source_id, name in datasets.items():
        r = results.get(name)
        if r is None:
            continue
        modified = r.get("metadata_modified")
        out.append(
            LiveDataset(
                id=source_id,
                ckan_name=name,
                title=r.get("title") or name,
                organization=(r.get("organization") or {}).get("title", ""),
                metadata_modified=f"{modified}Z" if modified and "+" not in modified else modified,
                url=DATASET_URL.format(name=name),
            )
        )
    return out


def live_sources() -> LiveSources:
    global _cache
    with _lock:
        now = time.monotonic()
        if _cache and now - _cache[0] < CACHE_SECONDS:
            return _cache[1]
        path = get_settings().processed_dir / "live_sources.json"
        try:
            datasets = _fetch({**CKAN_DATASETS, **extra_datasets()})
            result = LiveSources(
                checked_at=datetime.now(UTC).isoformat(timespec="seconds"),
                available=True,
                datasets=datasets,
            )
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(result.model_dump_json(indent=2), encoding="utf-8")
        except (httpx.HTTPError, KeyError, ValueError):
            if path.exists():
                last = LiveSources.model_validate_json(path.read_text(encoding="utf-8"))
                result = last.model_copy(update={"available": False})
            else:
                result = LiveSources(
                    checked_at=datetime.now(UTC).isoformat(timespec="seconds"),
                    available=False,
                    datasets=[],
                )
        _cache = (now, result)
        return result
