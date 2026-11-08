"""Official air quality stations in Croatia: 2024 annual means of PM2.5 and NO2.

Measurements: EEA Air Quality Download Service (verified E1a data, reported by
the Croatian ministry, namespace aqd.azo.hr), one parquet file per sampling point.
Station coordinates and type: EEA sampling point metadata (DataExtract.csv).

Output: data/processed/stations_2024.parquet with
sampling_point, station_code, station_name, pollutant, lon, lat, area, type,
mean, coverage (share of the year with valid data), n.
"""

from __future__ import annotations

import io
import json
import zipfile

import httpx
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from ingest.common import download, file_date, http_client, processed_dir, raw_dir, record_source

API = "https://eeadmz1-downloads-api-appservice.azurewebsites.net/ParquetFile/urls"
METADATA = (
    "https://discomap.eea.europa.eu/App/AQViewer/download?"
    "fqn=Airquality_Dissem.b2g.measurements&f=csv"
)
YEAR = 2024
POLLUTANTS = {6001: "pm25", 8: "no2"}
NAMES = {"pm25": "PM2.5", "no2": "NO2"}
HOURS_2024 = 366 * 24
DAYS_2024 = 366


def parquet_urls() -> list[str]:
    urls: list[str] = []
    for agg in ("day", "hour"):
        body = {
            "countries": ["HR"],
            "cities": [],
            "pollutants": list(NAMES.values()),
            "dataset": 2,
            "source": "API",
            "dateTimeStart": f"{YEAR}-01-01T00:00:00Z",
            "dateTimeEnd": f"{YEAR}-12-31T23:59:59Z",
            "aggregationType": agg,
        }
        with http_client(timeout=120) as client:
            response = client.post(API, json=body)
            response.raise_for_status()
        urls += [u.strip() for u in response.text.splitlines() if u.strip().endswith(".parquet")]
    return sorted(set(urls))


def metadata() -> pd.DataFrame:
    path = download(METADATA, raw_dir("eea_stations") / "samplingpoints.zip")
    with zipfile.ZipFile(path) as zf:
        df = pd.read_csv(io.BytesIO(zf.read("DataExtract.csv")), dtype=str, low_memory=False)
    df = df[df["Country"] == "Croatia"]
    df = df.sort_values("Year").drop_duplicates("Sampling Point Id", keep="last")
    return df


def annual_means(urls: list[str]) -> pd.DataFrame:
    rows = []
    for url in urls:
        path = download(url, raw_dir("eea_stations") / url.rsplit("/", 1)[-1])
        df = pd.read_parquet(path)
        df = df[(df["Start"] >= f"{YEAR}-01-01") & (df["Start"] < f"{YEAR + 1}-01-01")]
        df = df[df["Pollutant"].isin(POLLUTANTS)]
        if df.empty:
            continue
        valid = df[(df["Validity"] > 0) & df["Value"].notna()]
        agg = str(df["AggType"].iloc[0])
        expected = HOURS_2024 if agg == "hour" else DAYS_2024
        rows.append(
            {
                "sampling_point": str(df["Samplingpoint"].iloc[0]).split("/", 1)[-1],
                "pollutant": POLLUTANTS[int(df["Pollutant"].iloc[0])],
                "mean": float(valid["Value"].astype(float).mean()) if len(valid) else None,
                "coverage": round(len(valid) / expected, 3),
                "n": len(valid),
                "agg": agg,
            }
        )
    return pd.DataFrame(rows)


def run() -> None:
    meta = metadata()
    means = annual_means(parquet_urls())
    joined = means.merge(meta, left_on="sampling_point", right_on="Sampling Point Id", how="left")
    out = pd.DataFrame(
        {
            "sampling_point": joined["sampling_point"],
            "station_code": joined["Air Quality Station EoI Code"],
            "station_name": joined["Air Quality Station Name"],
            "pollutant": joined["pollutant"],
            "lon": joined["Longitude"].astype(float),
            "lat": joined["Latitude"].astype(float),
            "area": joined["Air Quality Station Area"],
            "type": joined["Air Quality Station Type"],
            "mean": joined["mean"],
            "coverage": joined["coverage"],
            "n": joined["n"],
        }
    )
    # Several sampling points can measure the same pollutant at a station: keep the best covered.
    out = out.sort_values("coverage", ascending=False).drop_duplicates(
        ["station_code", "pollutant"]
    )
    pq.write_table(
        pa.Table.from_pandas(out, preserve_index=False), processed_dir() / "stations_2024.parquet"
    )
    record_source(
        "eea_stations",
        title=f"Službene mjerne postaje kvalitete zraka u Hrvatskoj, mjerenja {YEAR}. (E1a)",
        publisher=(
            "Ministarstvo zaštite okoliša i zelene tranzicije, "
            "preko EEA Air Quality Download Service"
        ),
        url="https://eeadmz1-downloads-webapp.azurewebsites.net/",
        license="CC BY 4.0 (pravna obavijest EEA-e, https://www.eea.europa.eu/en/legal-notice)",
        retrieved_at=file_date(raw_dir("eea_stations") / "samplingpoints.zip"),
        data_date=str(YEAR),
        notes=json.dumps({"stations": int(out["station_code"].nunique())}),
    )
    summary = out.groupby("pollutant").size().to_dict()
    print(f"postaje {YEAR}: {summary}")


if __name__ == "__main__":
    try:
        run()
    except httpx.HTTPError as exc:
        raise SystemExit(f"EEA servis nije dostupan: {exc}") from exc
