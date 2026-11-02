"""Official registries without coordinates, geocoded against DGU addresses.

  kindergartens  MZOM Registar dječjih vrtića (data.gov.hr), Grad Zagreb geoportal
  schools        MZOM Osnovne škole (data.gov.hr), Grad Zagreb geoportal
  doctors        HZZO contracted family medicine and paediatric teams
  pharmacies     HZZO contracted pharmacies

Output: data/processed/registry_pois.parquet
  category, name, lon, lat, source, detail, precision ("address" | "street")
plus data/processed/geocoding_report.json with match rates (docs/KVALITETA_PODATAKA.md).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from app.geocode import normalize
from ingest.common import download, file_date, processed_dir, raw_dir, record_source

VRTICI_CSV = (
    "https://data.gov.hr/ckan/dataset/0b951eaa-d9e7-4c68-adcf-5090f452abf4/resource/"
    "7e7c26cd-6ad4-4cdd-b0cb-42b0ad2a933c/download/data.csv"
)
SKOLE_CSV = (
    "https://data.gov.hr/ckan/dataset/2841fb78-c828-4ab2-8cdc-f22abeed3a8c/resource/"
    "3c72e1c1-4c41-48f0-8663-c7ce4a997e88/download/data.csv"
)
ZG_VRTICI_CSV = (
    "https://opendata.arcgis.com/api/v3/datasets/49bb07d4efc34bd5bacc1d330dc28a07_0/"
    "downloads/data?format=csv&spatialRefId=4326&where=1%3D1"
)
ZG_SKOLE_GEOJSON = (
    "https://opendata.arcgis.com/api/v3/datasets/08ff18612cea48a1b1bdb921a83974bc_0/"
    "downloads/data?format=geojson&spatialRefId=4326&where=1%3D1"
)
HZZO_OPCA = "https://hzzo.hr/sites/default/files/web_opca_092026_0.xlsx"
HZZO_PED = "https://hzzo.hr/sites/default/files/web_ped_092026_0.xlsx"
HZZO_LJEKARNE = (
    "https://hzzo.hr/sites/default/files/inline-files/Popis%20ugovorenih%20ljekarni%20u%20RH_1.xls"
)
HZZO_PAGE = (
    "https://hzzo.hr/zdravstvena-zastita/zdravstvena-zastita-pokrivena-obveznim-"
    "zdravstvenim-osiguranjem/ugovoreni"
)

STOP_TOKENS = {"ulica", "ul", "trg", "cesta", "put", "obala", "naselje", "i", "bb"}
NUMBER_RE = re.compile(r"(\d+)\s*([a-zA-Z]?)\b")


def number_key(text: str) -> str:
    m = NUMBER_RE.search(text)
    return f"{m.group(1)}{m.group(2).lower()}" if m else ""


def split_address(address: str) -> tuple[str, str]:
    """'J.J.Strossmayera 82' -> ('J.J.Strossmayera', '82'); number may be missing."""
    address = address.strip().rstrip(",")
    m = re.search(r"\s(\d+\s*[a-zA-Z]?)(\s*[-/,].*)?$", " " + address)
    if not m:
        return address, ""
    street = (" " + address)[: m.start()].strip(" ,")
    return street, number_key(m.group(1))


def street_tokens(text: str) -> list[str]:
    return [t for t in normalize(text).split() if len(t) >= 3 and t not in STOP_TOKENS]


def street_score(query: str, candidate: str) -> float:
    q = street_tokens(query)
    if not q:
        return 0.0
    cand = street_tokens(candidate)
    hits = sum(1 for t in q if any(c.startswith(t) or t.startswith(c) for c in cand))
    if not any(t == max(q, key=len) for t in q if any(c.startswith(t) for c in cand)):
        return 0.0  # the longest word (usually the surname) must match
    return hits / len(q)


@dataclass
class AddressIndex:
    by_post: dict[tuple[str, str], list[int]] = field(default_factory=dict)
    by_place: dict[tuple[str, str], list[int]] = field(default_factory=dict)
    streets_post: dict[str, list[int]] = field(default_factory=dict)
    streets_place: dict[str, list[int]] = field(default_factory=dict)
    street: list[str] = field(default_factory=list)
    lon: list[float] = field(default_factory=list)
    lat: list[float] = field(default_factory=list)

    @classmethod
    def load(cls) -> AddressIndex:
        t = pq.read_table(processed_dir() / "addresses.parquet").to_pydict()
        idx = cls(street=t["street"], lon=t["lon"], lat=t["lat"])
        for i in range(len(t["street"])):
            num = number_key(t["housenumber"][i])
            post = t["postcode"][i]
            place = normalize(t["place"][i])
            idx.by_post.setdefault((post, num), []).append(i)
            idx.by_place.setdefault((place, num), []).append(i)
            idx.streets_post.setdefault(post, []).append(i)
            idx.streets_place.setdefault(place, []).append(i)
        return idx

    def match(
        self, address: str, postcode: str = "", place: str = ""
    ) -> tuple[float, float, str] | None:
        street, num = split_address(address)
        place_n = normalize(place)
        pools: list[list[int]] = []
        if num:
            if postcode:
                pools.append(self.by_post.get((postcode, num), []))
            if place_n:
                pools.append(self.by_place.get((place_n, num), []))
        for pool in pools:
            best = self._best(street, pool)
            if best is not None:
                return self.lon[best], self.lat[best], "address"
        # Street-level fallback: a middle address of the matching street.
        for pool in (self.streets_post.get(postcode, []), self.streets_place.get(place_n, [])):
            if not pool or not street:
                continue
            scored: dict[str, list[int]] = {}
            for i in pool:
                scored.setdefault(self.street[i], []).append(i)
            ranked = sorted(((street_score(street, s), s) for s in scored), key=lambda x: -x[0])
            if ranked and ranked[0][0] >= 0.99:
                rows = scored[ranked[0][1]]
                mid = rows[len(rows) // 2]
                return self.lon[mid], self.lat[mid], "street"
        return None

    def _best(self, street: str, pool: list[int]) -> int | None:
        if not pool:
            return None
        if not street_tokens(street):
            return pool[0] if len({self.street[i] for i in pool}) == 1 else None
        best_i, best_s = None, 0.0
        for i in pool:
            s = street_score(street, self.street[i])
            if s > best_s:
                best_i, best_s = i, s
        return best_i if best_s >= 0.5 else None


@dataclass
class Collector:
    rows: dict[str, list[object]] = field(
        default_factory=lambda: {
            k: [] for k in ("category", "name", "lon", "lat", "source", "detail", "precision")
        }
    )
    report: dict[str, dict[str, int]] = field(default_factory=dict)

    def add(
        self,
        category: str,
        name: str,
        lon: float,
        lat: float,
        source: str,
        detail: str,
        precision: str,
    ) -> None:
        for key, value in (
            ("category", category),
            ("name", name),
            ("lon", lon),
            ("lat", lat),
            ("source", source),
            ("detail", detail),
            ("precision", precision),
        ):
            self.rows[key].append(value)

    def count(self, source: str, outcome: str) -> None:
        stats = self.report.setdefault(source, {"address": 0, "street": 0, "unmatched": 0})
        stats[outcome] = stats.get(outcome, 0) + 1


def geocode_rows(
    col: Collector,
    idx: AddressIndex,
    source: str,
    category: str,
    records: list[dict[str, str]],
) -> None:
    for r in records:
        hit = idx.match(r["address"], r.get("postcode", ""), r.get("place", ""))
        if hit is None:
            col.count(source, "unmatched")
            continue
        lon, lat, precision = hit
        col.count(source, precision)
        col.add(category, r["name"], lon, lat, source, r["address_label"], precision)


def _records(df: pd.DataFrame) -> list[dict[str, str]]:
    return [{str(k): _clean(v) for k, v in row.items()} for row in df.to_dict("records")]


def _clean(value: object) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return ""
    text = str(value).strip()
    return text[:-2] if text.endswith(".0") and text[:-2].isdigit() else text


def kindergartens(col: Collector, idx: AddressIndex) -> None:
    path = download(VRTICI_CSV, raw_dir("mzom") / "djecji_vrtici.csv")
    df = pd.read_csv(path, dtype=str, encoding="utf-8-sig").fillna("")
    records = [
        {
            "name": " ".join(r["Naziv"].split()),
            "address": r["Adresa"],
            "postcode": r["PostanskiBroj"],
            "place": r["Mjesto"],
            "address_label": f"{r['Adresa']}, {r['Mjesto']}",
        }
        for r in _records(df)
        if normalize(r["Mjesto"]) != "zagreb"  # Zagreb comes from the city geoportal
    ]
    geocode_rows(col, idx, "mzom_vrtici", "kindergarten", records)
    record_source(
        "mzom_vrtici",
        title="Registar dječjih vrtića",
        publisher="Ministarstvo znanosti, obrazovanja i mladih",
        url="https://data.gov.hr/ckan/dataset/djecji-vrtici",
        license="Otvorena dozvola RH",
        retrieved_at=file_date(path),
    )
    zg = download(ZG_VRTICI_CSV, raw_dir("zagreb") / "vrtici.csv")
    zdf = pd.read_csv(zg, dtype=str, encoding="utf-8-sig").fillna("")
    for r in _records(zdf):
        col.add(
            "kindergarten",
            f"Dječji vrtić {r['naziv'].title()}",
            float(r["X"]),
            float(r["Y"]),
            "zg_vrtici",
            f"{r['adresa']}, Zagreb",
            "address",
        )
    record_source(
        "zg_vrtici",
        title="Geoportal: dječji vrtići Grada Zagreba",
        publisher="Grad Zagreb",
        url="https://data.gov.hr/ckan/dataset/geoportal-djecji-vrtici",
        license="CC BY 4.0",
        retrieved_at=file_date(zg),
    )


def schools(col: Collector, idx: AddressIndex) -> None:
    path = download(SKOLE_CSV, raw_dir("mzom") / "osnovne_skole.csv")
    df = pd.read_csv(path, dtype=str, encoding="utf-8-sig").fillna("")
    records = [
        {
            "name": " ".join(r["Naziv"].split()).title().replace("Osnovna Škola", "Osnovna škola"),
            "address": r["Adresa"],
            "postcode": r["PoštanskiBroj"],
            "place": r["Mjesto"],
            "address_label": f"{r['Adresa'].title()}, {r['Mjesto']}",
        }
        for r in _records(df)
        if normalize(r["Mjesto"]) != "zagreb"
    ]
    geocode_rows(col, idx, "mzom_skole", "school", records)
    record_source(
        "mzom_skole",
        title="Osnovne škole",
        publisher="Ministarstvo znanosti, obrazovanja i mladih",
        url="https://data.gov.hr/ckan/dataset/osnovne-skole",
        license="Otvorena dozvola RH",
        retrieved_at=file_date(path),
    )
    zg = download(ZG_SKOLE_GEOJSON, raw_dir("zagreb") / "osnovne_skole.geojson")
    data = json.loads(zg.read_text(encoding="utf-8"))
    for f in data["features"]:
        p = f["properties"]
        lon, lat = f["geometry"]["coordinates"][:2]
        col.add(
            "school",
            str(p.get("naziv", "")).strip(),
            float(lon),
            float(lat),
            "zg_skole",
            f"{p.get('adresa', '')}, Zagreb",
            "address",
        )
    record_source(
        "zg_skole",
        title="Geoportal: osnovne škole Grada Zagreba",
        publisher="Grad Zagreb",
        url="https://data.gov.hr/ckan/dataset/geoportal-osnovne-skole",
        license="Otvorena dozvola RH",
        retrieved_at=file_date(zg),
    )


def _hzzo_teams(path: Path) -> list[dict[str, str]]:
    df = pd.read_excel(path, header=None, skiprows=2, dtype=str)
    seen: set[tuple[str, str, str]] = set()
    records = []
    for row in df.itertuples(index=False):
        place, street, number = _clean(row[10]), _clean(row[11]), _clean(row[12])
        if not place:
            continue
        key = (place, street, number)
        if key in seen:  # several teams can share one practice address
            continue
        seen.add(key)
        address = f"{street} {number}".strip() if street else f"{place} {number}".strip()
        records.append(
            {
                "name": "",
                "address": address,
                "place": place,
                "address_label": f"{address.title()}, {place.title()}",
            }
        )
    return records


def doctors(col: Collector, idx: AddressIndex) -> None:
    for url, category, label, fname in (
        (HZZO_OPCA, "doctor", "Ordinacija obiteljske medicine", "hzzo_opca.xlsx"),
        (HZZO_PED, "pediatrician", "Pedijatrijska ordinacija", "hzzo_pedijatrija.xlsx"),
    ):
        path = download(url, raw_dir("hzzo") / fname)
        records = _hzzo_teams(path)
        for r in records:
            r["name"] = label
        geocode_rows(col, idx, f"hzzo_{category}", category, records)
        record_source(
            f"hzzo_{category}",
            title=(
                "Ugovoreni timovi opće/obiteljske medicine"
                if category == "doctor"
                else "Ugovoreni timovi zdravstvene zaštite predškolske djece (pedijatrija)"
            ),
            publisher="Hrvatski zavod za zdravstveno osiguranje (HZZO)",
            url=HZZO_PAGE,
            license="nije navedena; javno objavljen popis tijela javne vlasti",
            retrieved_at=file_date(path),
            data_date="rujan 2026.",
        )


def pharmacies(col: Collector, idx: AddressIndex) -> None:
    path = download(HZZO_LJEKARNE, raw_dir("hzzo") / "ljekarne.xls")
    df = pd.read_excel(path, header=1, dtype=str).fillna("")
    cols = {c.strip(): c for c in df.columns}
    seen: set[tuple[str, str, str]] = set()
    records = []
    for row in _records(df):
        street = row[str(cols["Ulica"])]
        number = row[str(cols["Kućni broj"])]
        postcode = row[str(cols["HPT broj"])]
        place = row[str(cols["HPT naziv"])]
        key = (postcode, normalize(street), number)
        if not street or key in seen:
            continue
        seen.add(key)
        address = f"{street} {number}".strip()
        records.append(
            {
                "name": "Ljekarna",
                "address": address,
                "postcode": postcode,
                "place": place,
                "address_label": f"{address}, {place.title()}",
            }
        )
    geocode_rows(col, idx, "hzzo_ljekarne", "pharmacy", records)
    record_source(
        "hzzo_ljekarne",
        title="Popis ugovorenih ljekarni",
        publisher="Hrvatski zavod za zdravstveno osiguranje (HZZO)",
        url=HZZO_PAGE,
        license="nije navedena; javno objavljen popis tijela javne vlasti",
        retrieved_at=file_date(path),
        data_date="rujan 2023. (zadnja izmjena datoteke)",
    )


def run() -> None:
    idx = AddressIndex.load()
    col = Collector()
    kindergartens(col, idx)
    schools(col, idx)
    doctors(col, idx)
    pharmacies(col, idx)
    out = processed_dir()
    pq.write_table(pa.table(col.rows), out / "registry_pois.parquet")
    (out / "geocoding_report.json").write_text(
        json.dumps(col.report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    for source, stats in col.report.items():
        total = sum(stats.values())
        print(f"{source}: {stats} (uspješno {100 * (total - stats['unmatched']) / total:.1f} %)")


if __name__ == "__main__":
    run()
