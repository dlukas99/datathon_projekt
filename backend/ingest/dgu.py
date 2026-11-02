"""DGU (State Geodetic Administration): INSPIRE addresses and administrative units.

Addresses.gml is a single 2.6 GB line, so it is streamed out of the ZIP in blocks
and each <wfs:member> is read with regular expressions (the structure is fixed by
the INSPIRE AD schema). Administrative units are read with GDAL (pyogrio).

Outputs in data/processed/:
  addresses.parquet    street, housenumber, place, postcode, settlement_code, lon, lat, source
  admin_units.parquet  level (county|municipality|settlement), code, name, parent_code,
                       parent_name, geometry (WKB, EPSG:3765, simplified to 5 m)
  settlements.parquet  name, municipality, county, code, lon, lat, source
"""

from __future__ import annotations

import re
import zipfile
from collections.abc import Iterator
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import shapely
from pyproj import Transformer

from ingest.common import download, file_date, processed_dir, raw_dir, record_source

AD_URL = "https://geoportal.dgu.hr/services/atom/INSPIRE_Addresses_(AD).zip"
AU_URL = "https://geoportal.dgu.hr/services/atom/INSPIRE_Administrative_Units_(AU).zip"

MEMBER_END = b"</wfs:member>"
RE_ID = re.compile(rb'gml:id="([^"]+)"')
RE_TEXT = re.compile(rb"<gn:text>([^<]*)</gn:text>")
RE_ALT = re.compile(rb"<ad:alternativeIdentifier>([^<]*)</ad:alternativeIdentifier>")
RE_POS = re.compile(rb"<gml:pos>([-0-9.]+) ([-0-9.]+)</gml:pos>")
RE_DESIGNATOR = re.compile(rb"<ad:LocatorDesignator><ad:designator>([^<]*)</ad:designator>")
RE_COMPONENT = re.compile(rb'<ad:component xlink:href="#([A-Za-z]+)\.([0-9]+)"')
RE_POSTCODE = re.compile(rb"<ad:postCode>([^<]*)</ad:postCode>")
RE_LEVEL = re.compile(rb'<ad:level xlink:href="[^"]*/([0-9a-zA-Z]+)"')

LEVELS = {
    "Županija": "county",
    "Jedinica lokalne samouprave": "municipality",
    "Naselje": "settlement",
}


def iter_members(zf: zipfile.ZipFile, name: str, block: int = 1 << 24) -> Iterator[bytes]:
    with zf.open(name) as fh:
        rest = b""
        while True:
            chunk = fh.read(block)
            if not chunk:
                break
            data = rest + chunk
            parts = data.split(MEMBER_END)
            rest = parts.pop()
            yield from parts


def _text(match: re.Match[bytes] | None) -> str:
    return match.group(1).decode("utf-8").strip() if match else ""


def parse_names(zf: zipfile.ZipFile, name: str) -> dict[str, tuple[str, str]]:
    """gml:id -> (alternativeIdentifier, name) for ThoroughfareName and AdminUnitName."""
    out: dict[str, tuple[str, str]] = {}
    for member in iter_members(zf, name):
        m = RE_ID.search(member)
        if m:
            out[m.group(1).decode()] = (_text(RE_ALT.search(member)), _text(RE_TEXT.search(member)))
    return out


def parse_postcodes(zf: zipfile.ZipFile) -> dict[str, str]:
    out: dict[str, str] = {}
    for member in iter_members(zf, "PostalDescriptor.gml"):
        m = RE_ID.search(member)
        if m:
            out[m.group(1).decode()] = _text(RE_POSTCODE.search(member))
    return out


def addresses(zip_path: Path) -> dict[str, list[object]]:
    to_wgs = Transformer.from_crs("EPSG:3035", "EPSG:4326", always_xy=True)
    with zipfile.ZipFile(zip_path) as zf:
        streets = parse_names(zf, "ThoroughfareName.gml")
        units = parse_names(zf, "AdminUnitName.gml")
        posts = parse_postcodes(zf)
        cols: dict[str, list[object]] = {
            k: [] for k in ("street", "housenumber", "place", "postcode", "settlement_code")
        }
        xs: list[float] = []
        ys: list[float] = []
        for member in iter_members(zf, "Address.gml"):
            pos = RE_POS.search(member)
            number = _text(RE_DESIGNATOR.search(member))
            if pos is None or not number:
                continue
            street = place = code = postcode = ""
            for kind, ident in RE_COMPONENT.findall(member):
                key = f"{kind.decode()}.{ident.decode()}"
                if kind == b"ThoroughfareName":
                    street = streets.get(key, ("", ""))[1]
                elif kind == b"AdminUnitName" and key in units:
                    alt, nm = units[key]
                    if len(alt) == 6:  # settlement code; the country has none
                        code, place = alt, nm
                elif kind == b"PostalDescriptor":
                    postcode = posts.get(key, "")
            cols["street"].append(street or place)
            cols["housenumber"].append(number)
            cols["place"].append(place)
            cols["postcode"].append(postcode)
            cols["settlement_code"].append(code)
            # INSPIRE EPSG:3035 axis order in GML is northing, easting.
            ys.append(float(pos.group(1)))
            xs.append(float(pos.group(2)))
    lon, lat = to_wgs.transform(np.asarray(xs), np.asarray(ys))
    cols["lon"] = list(np.round(lon, 6))
    cols["lat"] = list(np.round(lat, 6))
    cols["source"] = ["dgu_ad"] * len(xs)
    return cols


def admin_units(zip_path: Path) -> tuple[dict[str, list[object]], dict[str, list[object]]]:
    import geopandas as gpd
    import pyogrio

    extract_dir = raw_dir("dgu", "au")
    gml = extract_dir / "AdministrativeUnit.gml"
    if not gml.exists():
        with zipfile.ZipFile(zip_path) as zf:
            zf.extract("AdministrativeUnit.gml", extract_dir)
    df = pyogrio.read_dataframe(
        gml,
        columns=["nationalCode", "LocalisedCharacterString", "text"],
        where="LocalisedCharacterString IN ('Županija', 'Jedinica lokalne samouprave', 'Naselje')",
    )
    df = df.set_crs("EPSG:3035", allow_override=True).to_crs("EPSG:3765")
    df["level"] = df["LocalisedCharacterString"].map(LEVELS)
    df = df[df["level"].notna()].reset_index(drop=True)
    df["geometry"] = shapely.simplify(df.geometry.values, 5.0, preserve_topology=True)

    # The GML parent links are not exposed by GDAL; derive the hierarchy spatially.
    def parents(child: str, parent: str) -> dict[str, tuple[str, str]]:
        kids = df[df["level"] == child]
        pts = gpd.GeoDataFrame(
            {"code": kids["nationalCode"]},
            geometry=kids.geometry.representative_point(),
            crs=df.crs,
        )
        up = df[df["level"] == parent][["nationalCode", "text", "geometry"]]
        joined = gpd.sjoin(pts, up, predicate="within", how="left")
        joined = joined.drop_duplicates("code").fillna({"nationalCode": "", "text": ""})
        return {r.code: (str(r.nationalCode), str(r.text)) for r in joined.itertuples()}

    jls_of = parents("settlement", "municipality")
    county_of = parents("municipality", "county")
    parent_code, parent_name = [], []
    for row in df.itertuples():
        link = (
            jls_of.get(row.nationalCode)
            if row.level == "settlement"
            else county_of.get(row.nationalCode)
            if row.level == "municipality"
            else None
        ) or ("", "")
        parent_code.append(link[0])
        parent_name.append(link[1])
    units: dict[str, list[Any]] = {
        "level": list(df["level"]),
        "code": list(df["nationalCode"]),
        "name": list(df["text"]),
        "parent_code": parent_code,
        "parent_name": parent_name,
        "geometry": list(shapely.to_wkb(df.geometry.values)),
    }
    settle = df[df["level"] == "settlement"]
    pts = gpd.GeoSeries(settle.geometry.representative_point(), crs="EPSG:3765").to_crs("EPSG:4326")
    jls = [jls_of.get(c, ("", "")) for c in settle["nationalCode"]]
    settlements: dict[str, list[Any]] = {
        "name": list(settle["text"]),
        "municipality": [j[1] for j in jls],
        "county": [county_of.get(j[0], ("", ""))[1] for j in jls],
        "code": list(settle["nationalCode"]),
        "lon": list(np.round(pts.x.values, 6)),
        "lat": list(np.round(pts.y.values, 6)),
        "source": ["dgu_au"] * len(settle),
    }
    return units, settlements


def run() -> None:
    out = processed_dir()
    au_zip = download(AU_URL, raw_dir("dgu") / "INSPIRE_Administrative_Units_AU.zip")
    units, settlements = admin_units(au_zip)
    pq.write_table(pa.table(units), out / "admin_units.parquet")
    pq.write_table(pa.table(settlements), out / "settlements.parquet")
    record_source(
        "dgu_au",
        title="Upravne jedinice INSPIRE (županije, gradovi i općine, naselja)",
        publisher="Državna geodetska uprava",
        url="https://data.gov.hr/ckan/dataset/upravne-jedinice-inspire",
        license="Otvorena dozvola RH",
        retrieved_at=file_date(au_zip),
    )
    print(f"dgu_au: {len(units['code'])} jedinica, {len(settlements['name'])} naselja")

    ad_zip = download(AD_URL, raw_dir("dgu") / "INSPIRE_Addresses_AD.zip")
    cols = addresses(ad_zip)
    pq.write_table(pa.table(cols), out / "addresses.parquet")
    record_source(
        "dgu_ad",
        title="Adrese INSPIRE (Registar prostornih jedinica)",
        publisher="Državna geodetska uprava",
        url="https://data.gov.hr/ckan/dataset/adrese-inspire",
        license="Otvorena dozvola RH",
        retrieved_at=file_date(ad_zip),
    )
    print(f"dgu_ad: {len(cols['street'])} adresa")


if __name__ == "__main__":
    run()
