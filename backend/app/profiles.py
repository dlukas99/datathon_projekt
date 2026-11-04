"""Profiles and Skor za život weights, shared with the frontend (config/profiles.json)."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from app.config import REPO_ROOT

PROFILES_PATH = REPO_ROOT / "config" / "profiles.json"


@lru_cache
def load() -> dict[str, Any]:
    data: dict[str, Any] = json.loads(PROFILES_PATH.read_text(encoding="utf-8"))
    return data


def weights(profile_id: str) -> dict[str, float]:
    for p in load()["profiles"]:
        if p["id"] == profile_id:
            return {k: float(v) for k, v in p["weights"].items()}
    return weights("opci")
