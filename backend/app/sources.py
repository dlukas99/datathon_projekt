"""Registry of data sources: static descriptions merged with the ingest manifest."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from app.config import get_settings
from app.models import SourceInfo

# Sources queried live (not part of `make data`), described here once.
LIVE_SOURCES: dict[str, dict[str, Any]] = {
    "pvgis": {
        "title": "PVGIS 5.3, procjena proizvodnje fotonaponskog sustava",
        "publisher": "Europska komisija, Zajednički istraživački centar (JRC)",
        "url": "https://re.jrc.ec.europa.eu/pvg_tools/en/",
        "license": "Uvjeti korištenja PVGIS-a (slobodna upotreba uz navođenje izvora)",
    },
    "valhalla": {
        "title": "Mreža hoda: Valhalla nad OpenStreetMapom",
        "publisher": "suradnici OpenStreetMapa; usmjerivač Valhalla (MIT)",
        "url": "https://github.com/valhalla/valhalla",
        "license": "ODbL 1.0 (podaci), MIT (softver)",
    },
}


@lru_cache
def manifest() -> dict[str, dict[str, Any]]:
    path = get_settings().processed_dir / "manifest.json"
    if not path.exists():
        return {}
    data: dict[str, dict[str, Any]] = json.loads(path.read_text(encoding="utf-8"))
    return data


def source_info(source_id: str) -> SourceInfo:
    meta = {**LIVE_SOURCES.get(source_id, {}), **manifest().get(source_id, {})}
    return SourceInfo(
        id=source_id,
        title=meta.get("title", source_id),
        publisher=meta.get("publisher", ""),
        url=meta.get("url", ""),
        license=meta.get("license", ""),
        retrieved_at=meta.get("retrieved_at"),
        data_date=meta.get("data_date"),
    )


def retrieved_at(source_id: str) -> str | None:
    return source_info(source_id).retrieved_at
