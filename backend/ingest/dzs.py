"""DZS Census 2021: population per settlement, joined to DGU settlements by name.

The DZS table has no settlement codes, only names of the county, town or
municipality and settlement. Bilingual names ("Name – Ime") are cut at the dash.

Output: data/processed/settlement_population.parquet (settlement_code, population)
"""

from __future__ import annotations

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from app.geocode import normalize
from ingest.common import download, file_date, processed_dir, raw_dir, record_source

URL = "https://podaci.dzs.hr/media/rqybclnx/popis_2021-stanovnistvo_po_naseljima.xlsx"
PAGE = (
    "https://data.gov.hr/ckan/dataset/"
    "statistika-u-nizu-popis-stanovnistva-kucanstava-i-stanova-2021"
)


def _key(municipality: str, settlement: str) -> tuple[str, str]:
    return normalize(municipality), normalize(settlement.split(" – ")[0])


def run() -> None:
    path = download(URL, raw_dir("dzs") / "popis_2021_stanovnistvo_po_naseljima.xlsx")
    df = pd.read_excel(path, sheet_name="1.", header=7, dtype=str)
    df = df.iloc[:, :9]
    df.columns = [
        "county",
        "jls_type",
        "county_en",
        "jls_en",
        "jls",
        "settlement",
        "sex",
        "_",
        "total",
    ]
    rows = df[df["settlement"].notna() & (df["sex"] == "sv.")].copy()
    # Grad Zagreb is a county and a town at once; its town column is empty.
    rows["jls"] = rows["jls"].fillna(rows["county"])
    population = {
        _key(str(r.jls), str(r.settlement)): int(str(r.total).replace("-", "0"))
        for r in rows.itertuples()
    }
    settlements = pd.read_parquet(processed_dir() / "settlements.parquet")
    codes, values = [], []
    for s in settlements.itertuples():
        value = population.get(_key(str(s.municipality), str(s.name)))
        if value is not None:
            codes.append(s.code)
            values.append(value)
    pq.write_table(
        pa.table({"settlement_code": codes, "population": values}),
        processed_dir() / "settlement_population.parquet",
    )
    record_source(
        "dzs_popis",
        title="Popis stanovništva, kućanstava i stanova 2021., stanovništvo po naseljima",
        publisher="Državni zavod za statistiku",
        url=PAGE,
        license="Otvorena dozvola RH",
        retrieved_at=file_date(path),
        data_date="Popis 2021.",
    )
    print(f"dzs: {len(codes)} od {len(settlements)} naselja spojeno, {len(rows)} u tablici DZS-a")


if __name__ == "__main__":
    run()
