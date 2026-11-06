"""Golden reports for the demo addresses (scripts/demo_addresses.json).

A snapshot keeps the stable parts of a report: location, statuses and values of
the environmental categories, walking results. PVGIS is excluded because it is a
live external service. Regenerate after `make data` with:

    uv run python -m tests.golden --update
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from app.models import Report

ROOT = Path(__file__).resolve().parents[2]
DEMO = ROOT / "scripts" / "demo_addresses.json"
GOLDEN_DIR = Path(__file__).parent / "fixtures" / "golden"
SKIP_CATEGORIES = {"solar"}


def demo_addresses() -> list[dict[str, Any]]:
    data: dict[str, Any] = json.loads(DEMO.read_text(encoding="utf-8"))
    return list(data["addresses"])


def snapshot(report: Report) -> dict[str, Any]:
    loc = report.location
    cats: dict[str, Any] = {}
    for cat in report.categories:
        if cat.id in SKIP_CATEGORIES:
            continue
        cats[cat.id] = {
            "status": cat.status,
            "values": {v.key: v.value for v in cat.values},
        }
    return {
        "location": {
            "settlement": loc.settlement,
            "municipality": loc.municipality,
            "county": loc.county,
        },
        "categories": cats,
    }


def main() -> int:
    from fastapi.testclient import TestClient

    from app.main import app

    if "--update" not in sys.argv:
        print("Usage: python -m tests.golden --update")
        return 2
    GOLDEN_DIR.mkdir(parents=True, exist_ok=True)
    with TestClient(app) as client:
        for demo in demo_addresses():
            response = client.get("/api/report", params={"lat": demo["lat"], "lon": demo["lon"]})
            response.raise_for_status()
            snap = snapshot(Report.model_validate(response.json()))
            path = GOLDEN_DIR / f"{demo['id']}.json"
            text = json.dumps(snap, ensure_ascii=False, indent=2) + "\n"
            path.write_text(text, encoding="utf-8", newline="\n")  # LF, as in the repository
            print(f"{path.name}: zapisano")
    return 0


if __name__ == "__main__":
    sys.exit(main())
