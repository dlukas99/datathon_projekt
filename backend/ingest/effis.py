"""EFFIS burnt areas (Copernicus European Forest Fire Information System), Croatia.

The bulk download needs an account (HTTP 403), but the public WFS works without
one. Output: data/processed/effis_burnt.parquet with
fire_date, area_ha, commune, geometry (WKB, EPSG:4326).
"""

from __future__ import annotations

import json

import pyarrow as pa
import pyarrow.parquet as pq
import shapely
from shapely.geometry import shape

from ingest.common import download, file_date, processed_dir, raw_dir, record_source

WFS = "https://maps.effis.emergency.copernicus.eu/effis"
FILTER = (
    '<fes:Filter xmlns:fes="http://www.opengis.net/fes/2.0"><fes:PropertyIsEqualTo>'
    "<fes:ValueReference>COUNTRY</fes:ValueReference><fes:Literal>HR</fes:Literal>"
    "</fes:PropertyIsEqualTo></fes:Filter>"
)


def url() -> str:
    import urllib.parse

    params = {
        "service": "WFS",
        "version": "2.0.0",
        "request": "GetFeature",
        "typeNames": "ms:modis.ba.poly",
        "outputFormat": "application/json; subtype=geojson",
        "FILTER": FILTER,
    }
    return f"{WFS}?{urllib.parse.urlencode(params)}"


def run() -> None:
    path = download(url(), raw_dir("effis") / "hr.geojson")
    data = json.loads(path.read_text(encoding="utf-8"))
    cols: dict[str, list[object]] = {k: [] for k in ("fire_date", "area_ha", "commune", "geometry")}
    for f in data["features"]:
        p = f["properties"]
        geom = shape(f["geometry"])
        if geom.is_empty:
            continue
        cols["fire_date"].append(str(p.get("FIREDATE", ""))[:10])
        cols["area_ha"].append(float(p.get("AREA_HA") or 0))
        cols["commune"].append(str(p.get("COMMUNE") or ""))
        cols["geometry"].append(shapely.to_wkb(geom))
    pq.write_table(pa.table(cols), processed_dir() / "effis_burnt.parquet")
    dates = sorted(d for d in cols["fire_date"] if isinstance(d, str) and d)
    record_source(
        "effis",
        title="EFFIS, opožarene površine (MODIS), Hrvatska",
        publisher="Europska komisija, Copernicus EFFIS (JRC)",
        url="https://forest-fire.emergency.copernicus.eu/applications/data-and-services",
        license="CC BY 4.0",
        retrieved_at=file_date(path),
        data_date=f"{dates[0][:4]}.–{dates[-1][:4]}." if dates else None,
    )
    print(f"effis: {len(cols['fire_date'])} opožarenih površina")


if __name__ == "__main__":
    run()
