"""Public transport timetables: departures per hour at each stop on a weekday.

Feeds:
  ZET (Zagreb) GTFS, Otvorena dozvola
  HŽPP (railways) GTFS, published on data.gov.hr for building applications
  Autotrolej (Rijeka) weekday timetable JSON, CC BY 4.0

Output: data/processed/transit_stops.parquet with
  name, lon, lat, source, mode, departures_per_hour, service_date
Departures per hour = departures between 06:00 and 20:00 on one weekday / 14.
"""

from __future__ import annotations

import io
import json
import zipfile
from datetime import date, timedelta
from pathlib import Path

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

from ingest.common import download, file_date, processed_dir, raw_dir, record_source

DAY_START_S = 6 * 3600
DAY_END_S = 20 * 3600
HOURS = (DAY_END_S - DAY_START_S) / 3600

GTFS_FEEDS = {
    "gtfs_zet": {
        "url": "https://zet.hr/gtfs-scheduled/latest",
        "title": "ZET, vozni red u obliku GTFS",
        "publisher": "Zagrebački električni tramvaj d.o.o.",
        "page": "https://www.zet.hr/odredbe/datoteke-u-gtfs-formatu/669",
        "license": "Otvorena dozvola Republike Hrvatske",
    },
    "gtfs_hzpp": {
        "url": "https://www.hzpp.hr/GTFS_files.zip",
        "title": "HŽ Putnički prijevoz, vozni red u obliku GTFS",
        "publisher": "HŽ Putnički prijevoz d.o.o.",
        "page": "https://data.gov.hr/ckan/dataset/hzpp-vozni-red",
        "license": "nije navedena; skup je objavljen na data.gov.hr radi izrade aplikacija",
    },
}

AUTOTROLEJ_URL = "http://e-usluge2.rijeka.hr/OpenData/ATvoznired-tjedan.json"


def _seconds(hms: pd.Series) -> pd.Series:
    parts = hms.str.strip().str.split(":", expand=True)
    return parts[0].astype(int) * 3600 + parts[1].astype(int) * 60 + parts[2].astype(int)


def _read(zf: zipfile.ZipFile, name: str, **kwargs: object) -> pd.DataFrame:
    with zf.open(name) as fh:
        return pd.read_csv(io.TextIOWrapper(fh, encoding="utf-8-sig"), dtype=str, **kwargs)  # type: ignore[call-overload,no-any-return]


def _service_date(zf: zipfile.ZipFile, today: date) -> tuple[date, set[str]]:
    """First Wednesday from today with active services; returns (date, service_ids)."""
    names = set(zf.namelist())
    cal = _read(zf, "calendar.txt") if "calendar.txt" in names else pd.DataFrame()
    cd = _read(zf, "calendar_dates.txt") if "calendar_dates.txt" in names else pd.DataFrame()
    day = today + timedelta(days=(2 - today.weekday()) % 7)
    for _ in range(60):
        ymd = day.strftime("%Y%m%d")
        active: set[str] = set()
        if not cal.empty:
            mask = (cal["wednesday"] == "1") & (cal["start_date"] <= ymd) & (cal["end_date"] >= ymd)
            active = set(cal.loc[mask, "service_id"])
        if not cd.empty:
            rows = cd[cd["date"] == ymd]
            active |= set(rows.loc[rows["exception_type"] == "1", "service_id"])
            active -= set(rows.loc[rows["exception_type"] == "2", "service_id"])
        if active:
            return day, active
        day += timedelta(days=7)
    raise RuntimeError("no active weekday service in the next 60 weeks")


def gtfs_departures(path: Path, source: str, today: date) -> pd.DataFrame:
    with zipfile.ZipFile(path) as zf:
        day, services = _service_date(zf, today)
        trips = _read(zf, "trips.txt", usecols=["trip_id", "service_id", "route_id"])
        routes = _read(zf, "routes.txt", usecols=["route_id", "route_type"])
        stops = _read(zf, "stops.txt")
        st = _read(
            zf,
            "stop_times.txt",
            usecols=["trip_id", "stop_id", "departure_time", "stop_sequence"],
        )
    trips = trips[trips["service_id"].isin(services)].merge(routes, on="route_id", how="left")
    st = st[st["trip_id"].isin(trips["trip_id"])].copy()
    st["seq"] = st["stop_sequence"].astype(int)
    last = st.groupby("trip_id")["seq"].transform("max")
    st = st[st["seq"] < last]  # arrival at the last stop is not a departure
    st = st[st["departure_time"].notna() & (st["departure_time"].str.len() > 0)]
    st["t"] = _seconds(st["departure_time"])
    st = st[(st["t"] >= DAY_START_S) & (st["t"] < DAY_END_S)]
    st = st.merge(trips[["trip_id", "route_type"]], on="trip_id", how="left")
    counts = st.groupby("stop_id").agg(n=("trip_id", "size"), route_type=("route_type", "first"))
    if "location_type" in stops:
        stops = stops[stops["location_type"].fillna("0").isin(["0", ""])]
    stops = stops.merge(counts, left_on="stop_id", right_index=True, how="left")
    stops["lat"] = stops["stop_lat"].astype(float)
    stops["lon"] = stops["stop_lon"].astype(float)
    stops = stops[(stops["lat"].abs() > 1) & (stops["lon"].abs() > 1)]
    mode_map = {"0": "tram", "2": "train", "3": "bus"}
    return pd.DataFrame(
        {
            "name": stops["stop_name"].fillna(""),
            "lon": stops["lon"],
            "lat": stops["lat"],
            "source": source,
            "mode": stops["route_type"]
            .map(mode_map)
            .fillna("bus" if source != "gtfs_hzpp" else "train"),
            "departures_per_hour": (stops["n"].fillna(0).astype(float) / HOURS).round(2),
            "service_date": day.isoformat(),
        }
    )


def autotrolej_departures(path: Path, retrieved: str) -> pd.DataFrame:
    rows = json.loads(path.read_text(encoding="utf-8-sig"))
    df = pd.DataFrame(rows)
    df["t"] = _seconds(df["Polazak"].str.slice(0, 8))
    last = df.groupby("PolazakId")["RedniBrojStanice"].transform("max")
    dep = df[(df["RedniBrojStanice"] < last) & (df["t"] >= DAY_START_S) & (df["t"] < DAY_END_S)]
    counts = dep.groupby("StanicaId").size()
    stops = df.groupby("StanicaId").agg(
        name=("Naziv", "first"), lon=("GpsX", "first"), lat=("GpsY", "first")
    )
    stops["n"] = counts.reindex(stops.index).fillna(0)
    return pd.DataFrame(
        {
            "name": stops["name"],
            "lon": stops["lon"].astype(float),
            "lat": stops["lat"].astype(float),
            "source": "autotrolej",
            "mode": "bus",
            "departures_per_hour": (stops["n"] / HOURS).round(2),
            "service_date": f"radni dan (preuzeto {retrieved[:10]})",
        }
    )


def run(today: date | None = None) -> None:
    today = today or date.today()
    frames = []
    for source, feed in GTFS_FEEDS.items():
        path = download(feed["url"], raw_dir("gtfs") / f"{source}.zip")
        df = gtfs_departures(path, source, today)
        frames.append(df)
        record_source(
            source,
            title=feed["title"],
            publisher=feed["publisher"],
            url=feed["page"],
            license=feed["license"],
            retrieved_at=file_date(path),
            data_date=f"radni dan {df['service_date'].iloc[0]}",
        )
        print(f"{source}: {len(df)} stajališta, dan {df['service_date'].iloc[0]}")
    at_path = download(AUTOTROLEJ_URL, raw_dir("autotrolej") / "ATvoznired-tjedan.json")
    at = autotrolej_departures(at_path, file_date(at_path))
    frames.append(at)
    record_source(
        "autotrolej",
        title="Vozni redovi autobusa Autotroleja (radni dan)",
        publisher="Grad Rijeka",
        url="https://data.gov.hr/ckan/dataset/at-vozni-redovi",
        license="CC BY 4.0",
        retrieved_at=file_date(at_path),
        data_date="radni dan",
    )
    print(f"autotrolej: {len(at)} stajališta")
    out = pd.concat(frames, ignore_index=True)
    pq.write_table(
        pa.Table.from_pandas(out, preserve_index=False), processed_dir() / "transit_stops.parquet"
    )


if __name__ == "__main__":
    run()
