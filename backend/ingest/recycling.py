"""Recycling yards and green islands: municipal datasets from data.gov.hr + OSM.

1. Search the portal's CKAN API for recycling datasets.
2. Download each CSV/JSON/XLSX resource and look for coordinate columns.
3. Keep valid points inside Croatia (swapped lat/lon is detected and fixed),
   one resource per dataset (the same data is often published in 3-4 formats).
4. Merge with OSM `amenity=recycling`, dropping OSM points within DEDUP_M.

Outputs: data/processed/recycling.parquet (category, name, lon, lat, source, detail)
and data/processed/recycling_ckan.json (per-dataset findings for
docs/KVALITETA_PODATAKA.md, and the dataset names used for the live sources page).
"""

from __future__ import annotations

import io
import json
import re
from typing import Any

import httpx
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from app.geo import CROATIA_BBOX
from ingest.common import download, get_json, processed_dir, raw_dir, record_source
from ingest.pois import _far_from

CKAN_SEARCH = "https://data.gov.hr/ckan/api/3/action/package_search"
QUERIES = ("reciklažno dvorište", "reciklažna dvorišta", "zeleni otok", "zeleni otoci")
TABULAR = {"csv", "json", "xlsx", "xls"}
LON_NAMES = ("longitude", "longitud", "lon", "lng", "x", "geo_duzina", "duzina")
LAT_NAMES = ("latitude", "lat", "y", "geo_sirina", "sirina")
NAME_NAMES = ("naziv", "name", "lokacija", "adresa", "ulica_i_broj")
DEDUP_M = 30.0


def _norm(col: str) -> str:
    return re.sub(r"[^a-z_]", "", col.strip().lower().replace(" ", "_"))


def _read_table(content: bytes, fmt: str) -> pd.DataFrame:
    if fmt == "csv":
        for enc in ("utf-8-sig", "cp1250"):
            for sep in (",", ";"):
                try:
                    df = pd.read_csv(io.BytesIO(content), sep=sep, dtype=str, encoding=enc)
                except (UnicodeDecodeError, pd.errors.ParserError):
                    continue
                if df.shape[1] > 1:
                    return df
        raise ValueError("CSV se ne može pročitati")
    if fmt == "json":
        data = json.loads(content.decode("utf-8-sig"))
        if isinstance(data, dict) and "features" in data:
            rows = []
            for f in data["features"]:
                geom = f.get("geometry") or {}
                coords = geom.get("coordinates") or [None, None]
                rows.append({**(f.get("properties") or {}), "x": coords[0], "y": coords[1]})
            return pd.DataFrame(rows).astype(str)
        if isinstance(data, dict):
            data = next((v for v in data.values() if isinstance(v, list)), [])
        return pd.DataFrame(data).astype(str)
    return pd.read_excel(io.BytesIO(content), dtype=str)


def _to_float(value: Any) -> float | None:
    try:
        return float(str(value).strip().replace(",", "."))
    except ValueError:
        return None


def extract_points(df: pd.DataFrame) -> tuple[list[dict[str, Any]], dict[str, int]]:
    cols = {_norm(c): c for c in df.columns}
    lon_col = next((cols[n] for n in LON_NAMES if n in cols), None)
    lat_col = next((cols[n] for n in LAT_NAMES if n in cols), None)
    name_col = next((cols[n] for n in NAME_NAMES if n in cols), None)
    stats = {"rows": len(df), "valid": 0, "swapped": 0, "invalid": 0, "missing": 0, "malformed": 0}
    if lon_col is None or lat_col is None:
        return [], stats
    w, s, e, n = CROATIA_BBOX
    points = []
    for _, row in df.iterrows():
        lon, lat = _to_float(row[lon_col]), _to_float(row[lat_col])
        if lon is None or lat is None:
            raw = f"{row[lon_col]}{row[lat_col]}".strip().lower().replace("nan", "")
            stats["malformed" if raw else "missing"] += 1
            continue
        if not (w <= lon <= e and s <= lat <= n) and (w <= lat <= e and s <= lon <= n):
            lon, lat = lat, lon
            stats["swapped"] += 1
        if not (w <= lon <= e and s <= lat <= n):
            stats["invalid"] += 1
            continue
        stats["valid"] += 1
        name = str(row[name_col]).strip() if name_col is not None else ""
        points.append({"lon": lon, "lat": lat, "name": "" if name == "nan" else name})
    return points, stats


def search_packages() -> list[dict[str, Any]]:
    seen: dict[str, dict[str, Any]] = {}
    for q in QUERIES:
        data = get_json(CKAN_SEARCH, params={"q": q, "rows": 50})
        for pkg in data["result"]["results"]:
            seen.setdefault(pkg["name"], pkg)
    return list(seen.values())


def run() -> None:
    packages = search_packages()
    findings: list[dict[str, Any]] = []
    frames: list[pd.DataFrame] = []
    used: list[str] = []
    cache = raw_dir("recycling")
    for pkg in packages:
        org = (pkg.get("organization") or {}).get("title", "")
        formats = sorted(
            {(r.get("format") or "").lower() or "bez oznake" for r in pkg["resources"]}
        )
        record: dict[str, Any] = {
            "name": pkg["name"],
            "title": pkg.get("title", ""),
            "organization": org,
            "license": pkg.get("license_title") or "nije navedena",
            "metadata_modified": pkg.get("metadata_modified"),
            "formats": formats,
            "resources": len(pkg["resources"]),
            "status": "bez koordinata",
            "issues": [],
        }
        for res in pkg["resources"]:
            fmt = (res.get("format") or "").lower()
            url = res.get("url") or ""
            if not url:
                record["issues"].append("resurs bez poveznice")
                continue
            if fmt not in TABULAR:
                continue
            path = cache / f"{pkg['name']}_{res['id']}.{fmt}"
            try:
                if not path.exists():
                    download(url, path, retries=2)
                df = _read_table(path.read_bytes(), fmt)
            except (httpx.HTTPError, ValueError, OSError) as exc:
                record["issues"].append(
                    f"{fmt.upper()} nije dostupan ili čitljiv ({type(exc).__name__})"
                )
                continue
            points, stats = extract_points(df)
            if stats["swapped"]:
                record["issues"].append(
                    f"zamijenjene geografska širina i dužina ({stats['swapped']})"
                )
            if stats["invalid"]:
                record["issues"].append(f"neispravne koordinate ({stats['invalid']})")
            if stats["malformed"]:
                record["issues"].append(
                    f"koordinate u neispravnom obliku broja ({stats['malformed']})"
                )
            if stats["missing"]:
                record["issues"].append(f"redovi bez koordinata ({stats['missing']})")
            if points:
                frame = pd.DataFrame(points)
                frame["source"] = f"ckan:{pkg['name']}"
                frames.append(frame)
                used.append(pkg["name"])
                record["status"] = "koordinate"
                record["points"] = len(points)
                break
        findings.append(record)

    d = processed_dir()
    osm = pd.read_parquet(d / "osm_pois.parquet")
    osm = osm[osm["category"] == "recycling"].rename(columns={"extra": "detail"})
    municipal = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    if not municipal.empty:
        municipal = municipal.drop_duplicates(["lon", "lat"])
        municipal["category"] = "recycling"
        municipal["detail"] = ""
        osm = _far_from(osm, municipal, DEDUP_M)
    osm = osm.assign(source="osm")
    cols = ["category", "name", "lon", "lat", "source", "detail"]
    out = pd.concat(
        [municipal[cols] if not municipal.empty else None, osm[cols]], ignore_index=True
    )
    pq.write_table(pa.Table.from_pandas(out, preserve_index=False), d / "recycling.parquet")
    (d / "recycling_ckan.json").write_text(
        json.dumps({"datasets": findings, "used": used}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    for name in used:
        pkg = next(p for p in packages if p["name"] == name)
        record_source(
            f"ckan:{name}",
            title=pkg.get("title", name),
            publisher=(pkg.get("organization") or {}).get("title", ""),
            url=f"https://data.gov.hr/ckan/dataset/{name}",
            license=pkg.get("license_title") or "nije navedena",
            retrieved_at=pkg.get("metadata_modified"),
        )
    with_coords = sum(1 for f in findings if f["status"] == "koordinate")
    print(
        f"reciklaža: {len(findings)} skupova, {with_coords} s koordinatama, "
        f"{len(municipal)} općinskih točaka, {len(osm)} iz OSM-a"
    )


if __name__ == "__main__":
    run()
