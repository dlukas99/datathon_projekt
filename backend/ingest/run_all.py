"""`make data`: download and process every source, reusing files already in data/raw/."""

from __future__ import annotations

import sys
import time
from collections.abc import Callable

from ingest import dgu, osm, pois, rasters, registries, transit

STEPS: list[tuple[str, Callable[[], None]]] = [
    ("OpenStreetMap", osm.run),
    ("DGU adrese i upravne jedinice", dgu.run),
    ("Rasteri (JRC, EEA, ESA WorldCover)", rasters.run),
    ("Vozni redovi", transit.run),
    ("Registri (MZOM, HZZO, Grad Zagreb)", registries.run),
    ("Spajanje točaka", pois.run),
]


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    failed = []
    for title, step in STEPS:
        start = time.monotonic()
        print(f"== {title}", flush=True)
        try:
            step()
        except Exception as exc:  # report and continue with the remaining sources
            print(f"   GREŠKA: {exc!r}", flush=True)
            failed.append(title)
        print(f"   {time.monotonic() - start:.0f} s", flush=True)
    if failed:
        print("Nisu uspjeli: " + ", ".join(failed))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
