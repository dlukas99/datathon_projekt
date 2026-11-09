"""Facilities for the profile rules of "Predloži mjesto": higher education, hospitals,
student dormitories.

Sources:
  MZOM "Ustanove iz sustava visokog obrazovanja" (data.gov.hr, Otvorena dozvola):
      133 institutions with the place they are in (Mjesto).
  MZOM "Studijski programi visokih učilišta" (data.gov.hr, Otvorena dozvola):
      1,727 study programmes with the place they are taught in (IzvodjacMjesto).
  OpenStreetMap (Geofabrik extract, ODbL): general and clinical hospitals
      (amenity=hospital), student dormitories and canteens (by name).

Places from the registries are matched to DGU settlements by name (no geocoding of
addresses: the rules only need the settlement). Output:
  data/processed/higher_ed_places.parquet  settlement code, name, institutions,
      first-and-second-cycle programmes, example institutions
  data/processed/osm_facilities.parquet    category (hospital | dormitory | canteen), name,
      lon, lat
  data/processed/settlement_facilities.parquet  per settlement: higher education within
      40 km (JSON list, straight-line km between settlement centres) and the nearest
      hospital, student dormitory and canteen (straight-line km from the centre)
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import osmium
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from shapely import wkb

from app.geocode import normalize
from ingest.common import download, file_date, processed_dir, raw_dir, record_source

INSTITUTIONS_URL = (
    "https://data.gov.hr/ckan/dataset/2eea1a6e-49da-4742-a79a-77a019cf60e9/resource/"
    "ustanove-iz-sustava-visokog-obrazovanja/download/data.json"
)
PROGRAMMES_URL = (
    "https://data.gov.hr/ckan/dataset/66cc26c0-5d04-446b-9c46-7127041ec63a/resource/"
    "studijski-programi-visokih-ucilista/download/data.json"
)
INSTITUTIONS_PAGE = "https://data.gov.hr/ckan/dataset/ustanove-iz-sustava-visokog-obrazovanja"
PROGRAMMES_PAGE = "https://data.gov.hr/ckan/dataset/studijski-programi-visokih-ucilista"
PBF_NAME = "croatia-latest.osm.pbf"
# Last modification of both data files (resources) on data.gov.hr, from CKAN package_show
# (checked 2026-11-08). The datasets themselves were last edited on the portal on 2026-04-15.
DATA_DATE = "2025-04-15"

# Programmes a student enrols in after secondary school or continues with (first and
# second cycle, short and professional studies). Postgraduate studies are left out.
STUDENT_PROGRAMMES = re.compile(r"preddiplomski|diplomski|integrirani|kratki", re.IGNORECASE)
POSTGRADUATE = re.compile(r"poslijediplomski", re.IGNORECASE)


def clean(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def place_key(text: str) -> str:
    return normalize(clean(text).replace("-", " "))


def settlement_index(settlements: pd.DataFrame) -> dict[str, dict[str, Any]]:
    """Settlement name -> the most populous settlement of that name."""
    best: dict[str, dict[str, Any]] = {}
    for r in settlements.to_dict("records"):
        key = place_key(str(r["name"]))
        pop = 0 if pd.isna(r.get("population")) else int(r["population"])
        if key not in best or pop > best[key]["pop"]:
            best[key] = {"code": str(r["code"]), "name": str(r["name"]), "pop": pop}
    return best


def higher_ed_places(
    institutions: list[dict[str, Any]],
    programmes: list[dict[str, Any]],
    settlements: pd.DataFrame,
) -> tuple[pd.DataFrame, list[str]]:
    """One row per settlement with higher education; also the place names not matched."""
    index = settlement_index(settlements)
    inst: dict[str, list[str]] = defaultdict(list)
    for item in institutions:
        name = clean(item.get("NazivUstanove"))
        if "u osnivanju" in name.lower():
            continue  # not yet founded
        inst[place_key(item.get("Mjesto", ""))].append(name)
    progs: dict[str, int] = defaultdict(int)
    # Holders (Nositelj) by number of programmes in the place: the example shown is the
    # one that offers most of the studies there.
    holders: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
    for item in programmes:
        kind = clean(item.get("VrstaSP"))
        if STUDENT_PROGRAMMES.search(kind) and not POSTGRADUATE.search(kind):
            key = place_key(item.get("IzvodjacMjesto", ""))
            progs[key] += 1
            holders[key][clean(item.get("Nositelj"))] += 1
    rows = []
    unmatched = []
    for key in sorted(set(inst) | set(progs)):
        hit = index.get(key)
        if hit is None:
            unmatched.append(key)
            continue
        ranked = sorted(holders.get(key, {}).items(), key=lambda kv: (-kv[1], kv[0]))
        examples = [name for name, _ in ranked if name] or sorted(inst.get(key, []))
        rows.append(
            {
                "code": hit["code"],
                "name": hit["name"],
                "institutions": len(inst.get(key, [])),
                "programmes": progs.get(key, 0),
                "examples": examples[:2],
            }
        )
    return pd.DataFrame(rows), unmatched


# General and clinical hospitals (OSM amenity=hospital). Spa, psychiatric, prison and
# rehabilitation hospitals and hospitals across the border are left out.
HOSPITAL_NAME = re.compile(r"opća|opca|kliničk|klinick|\bkbc\b|\bkb\b|bolnic", re.IGNORECASE)
HOSPITAL_EXCLUDE = re.compile(
    r"specijaln|psihijat|lječil|toplic|deponij|dom zdravlja|ambulant|rehabilit|veterin"
    r"|zatvorsk|\bjzu\b|opšta",
    re.IGNORECASE,
)
DORM_NAME = re.compile(r"^\W*studentski\s+dom\b", re.IGNORECASE)
# Student canteens only: a plain "Menza" is often a company or hospital canteen.
CANTEEN_NAME = re.compile(r"studentsk\w*\s+(restoran|menza)|menza\s+studentsk", re.IGNORECASE)
# Higher education further than this from a settlement is never listed for it.
HIGHER_ED_SEARCH_KM = 40.0


def osm_category(tags: Any) -> str | None:
    name = tags.get("name", "")
    if tags.get("amenity") == "hospital":
        ok = HOSPITAL_NAME.search(name) and not HOSPITAL_EXCLUDE.search(name)
        return "hospital" if ok else None
    if DORM_NAME.search(name):
        return "dormitory"
    if CANTEEN_NAME.search(name):
        return "canteen"
    return None


def osm_facilities(pbf: Path) -> pd.DataFrame:
    wkb_factory = osmium.geom.WKBFactory()
    rows: dict[str, list[Any]] = {k: [] for k in ("category", "name", "lon", "lat")}
    processor = (
        osmium.FileProcessor(str(pbf))
        .with_locations()
        .with_areas(osmium.filter.KeyFilter("amenity", "building"))
        .with_filter(osmium.filter.KeyFilter("amenity", "building"))
    )
    obj: Any
    for obj in processor:
        cat = osm_category(obj.tags)
        if cat is None:
            continue
        if obj.is_node():
            if not obj.location.valid():
                continue
            lon, lat = obj.location.lon, obj.location.lat
        elif obj.is_area():
            try:
                shape = wkb.loads(bytes.fromhex(wkb_factory.create_multipolygon(obj)))
            except (osmium.InvalidLocationError, RuntimeError):
                continue
            point = shape.representative_point()
            lon, lat = point.x, point.y
        else:
            continue
        rows["category"].append(cat)
        rows["name"].append(obj.tags.get("name", ""))
        rows["lon"].append(lon)
        rows["lat"].append(lat)
    df = pd.DataFrame(rows)
    # A site and its buildings often carry the same name: one point per name and ~200 m.
    cell = (
        (df["lon"] * 500).round().astype(int).astype(str)
        + "/"
        + ((df["lat"] * 500).round().astype(int).astype(str))
    )
    return df.assign(cell=cell).drop_duplicates(["category", "name", "cell"]).drop(columns="cell")


def km_between(lon1: Any, lat1: Any, lon2: Any, lat2: Any) -> Any:
    """Great-circle distance in km (works on scalars and numpy arrays)."""
    lon1, lat1, lon2, lat2 = (
        np.radians(np.asarray(v, dtype=float)) for v in (lon1, lat1, lon2, lat2)
    )
    a = (
        np.sin((lat2 - lat1) / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    )
    return 6371.0 * 2 * np.arcsin(np.sqrt(a))


def settlement_facilities(
    settlements: pd.DataFrame, places: pd.DataFrame, facilities: pd.DataFrame
) -> pd.DataFrame:
    """Per settlement: higher education within reach and the nearest OSM facilities."""
    centres = settlements.set_index("code")[["lon", "lat"]]
    targets = places.join(centres, on="code")
    target_rows: list[dict[str, Any]] = [
        {str(k): v for k, v in t.items()} for t in targets.to_dict("records")
    ]
    out: dict[str, list[Any]] = defaultdict(list)
    for r in settlements.itertuples(index=False):
        out["code"].append(r.code)
        km = km_between(r.lon, r.lat, targets["lon"].to_numpy(), targets["lat"].to_numpy())
        near: list[dict[str, Any]] = []
        for t, d in zip(target_rows, km, strict=True):
            own = t["code"] == r.code
            if own or d <= HIGHER_ED_SEARCH_KM:
                near.append(
                    {
                        "code": t["code"],
                        "name": t["name"],
                        "km": 0.0 if own else round(float(d), 1),
                        "programmes": int(t["programmes"]),
                        "institutions": int(t["institutions"]),
                        "example": t["examples"][0] if len(t["examples"]) else "",
                    }
                )
        near.sort(key=lambda x: float(x["km"]))
        out["higher_ed"].append(json.dumps(near, ensure_ascii=False))
        for cat in ("hospital", "dormitory", "canteen"):
            sub = facilities[facilities["category"] == cat]
            if sub.empty:
                out[f"{cat}_km"].append(None)
                out[f"{cat}_name"].append(None)
                continue
            dist = km_between(r.lon, r.lat, sub["lon"].to_numpy(), sub["lat"].to_numpy())
            i = int(np.argmin(dist))
            out[f"{cat}_km"].append(round(float(dist[i]), 1))
            out[f"{cat}_name"].append(str(sub["name"].iloc[i]))
    return pd.DataFrame(out)


def run() -> None:
    raw = raw_dir("mzom")
    inst_path = download(INSTITUTIONS_URL, raw / "visoka_ucilista.json")
    prog_path = download(PROGRAMMES_URL, raw / "studijski_programi.json")
    out = processed_dir()
    settlements = pd.read_parquet(out / "settlements.parquet").merge(
        pd.read_parquet(out / "settlement_population.parquet"),
        left_on="code",
        right_on="settlement_code",
        how="left",
    )
    institutions = json.loads(inst_path.read_text(encoding="utf-8"))
    programmes = json.loads(prog_path.read_text(encoding="utf-8"))
    places, unmatched = higher_ed_places(institutions, programmes, settlements)
    pq.write_table(
        pa.Table.from_pandas(places, preserve_index=False), out / "higher_ed_places.parquet"
    )
    notes = {"places": len(places), "unmatched_places": unmatched}
    record_source(
        "mzom_visoka_ucilista",
        title="Ustanove iz sustava visokog obrazovanja",
        publisher="Ministarstvo znanosti, obrazovanja i mladih",
        url=INSTITUTIONS_PAGE,
        license="Otvorena dozvola (OD)",
        retrieved_at=file_date(inst_path),
        data_date=DATA_DATE,
        notes=json.dumps(notes, ensure_ascii=False),
    )
    record_source(
        "mzom_studijski_programi",
        title="Studijski programi visokih učilišta",
        publisher="Ministarstvo znanosti, obrazovanja i mladih",
        url=PROGRAMMES_PAGE,
        license="Otvorena dozvola (OD)",
        retrieved_at=file_date(prog_path),
        data_date=DATA_DATE,
        notes=json.dumps({"programmes": len(programmes)}),
    )
    pbf = raw_dir("osm") / PBF_NAME
    facilities = osm_facilities(pbf)
    pq.write_table(
        pa.Table.from_pandas(facilities, preserve_index=False), out / "osm_facilities.parquet"
    )
    per_settlement = settlement_facilities(settlements, places, facilities)
    pq.write_table(
        pa.Table.from_pandas(per_settlement, preserve_index=False),
        out / "settlement_facilities.parquet",
    )
    record_source(
        "osm_facilities",
        title="OpenStreetMap: bolnice, studentski domovi i menze",
        publisher="suradnici OpenStreetMapa",
        url="https://www.openstreetmap.org/",
        license="ODbL 1.0",
        retrieved_at=file_date(pbf),
        notes=json.dumps(facilities["category"].value_counts().to_dict()),
    )
    counts = facilities["category"].value_counts().to_dict()
    print(f"visoka učilišta: {len(places)} naselja, bez para: {unmatched}; OSM: {counts}")


if __name__ == "__main__":
    run()
