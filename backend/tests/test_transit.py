"""Timetables: every GTFS feed (ZET, HŽPP, Šibenik) is counted by the same rules."""

import zipfile
from datetime import date
from pathlib import Path

from ingest.transit import GTFS_FEEDS, gtfs_departures

FILES = {
    "agency.txt": "agency_id,agency_name,agency_url,agency_timezone\n1,Test,https://x,Europe/Zagreb\n",
    "calendar.txt": (
        "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n"
        "WD,1,1,1,1,1,0,0,20260907,20270607\n"
        "SU,0,0,0,0,0,0,1,20260907,20270607\n"
    ),
    "routes.txt": "route_id,route_short_name,route_type\nR1,1,3\n",
    "stops.txt": "stop_id,stop_name,stop_lat,stop_lon\nA,Prvo,43.73,15.89\nB,Zadnje,43.74,15.90\n",
    "trips.txt": "route_id,service_id,trip_id\n"
    + "".join(f"R1,WD,T{i}\n" for i in range(6))
    + "R1,SU,S1\n",
    "stop_times.txt": "trip_id,arrival_time,departure_time,stop_id,stop_sequence\n"
    # weekday departures from A at 05:30 (before 6), 06:00, 12:00, 19:59, 20:00 (after 20)
    # and 25:10 (after midnight): only the three between 06:00 and 20:00 count.
    + "".join(
        f"T{i},{t},{t},A,1\nT{i},{t},{t},B,2\n"
        for i, t in enumerate(
            ["05:30:00", "06:00:00", "12:00:00", "19:59:00", "20:00:00", "25:10:00"]
        )
    )
    + "S1,10:00:00,10:00:00,A,1\nS1,10:10:00,10:10:00,B,2\n",
}


def _feed(tmp_path: Path) -> Path:
    path = tmp_path / "gtfs.zip"
    with zipfile.ZipFile(path, "w") as zf:
        for name, text in FILES.items():
            zf.writestr(name, text)
    return path


def test_weekday_departures_between_six_and_twenty_per_hour(tmp_path: Path) -> None:
    df = gtfs_departures(_feed(tmp_path), "gtfs_sibenik", date(2026, 11, 9)).set_index("name")
    assert df.loc["Prvo", "service_date"] == "2026-11-11"  # the first Wednesday with service
    assert df.loc["Prvo", "departures_per_hour"] == round(3 / 14, 2)  # Sunday trip not counted
    assert df.loc["Zadnje", "departures_per_hour"] == 0  # arrivals at the last stop
    assert set(df["mode"]) == {"bus"}
    assert set(df["source"]) == {"gtfs_sibenik"}


def test_sibenik_feed_is_open_and_from_the_city_company() -> None:
    feed = GTFS_FEEDS["gtfs_sibenik"]
    assert feed["license"] == "Otvorena dozvola Republike Hrvatske"
    assert feed["url"].startswith("https://www.gradski-parking.hr/")
    assert "Grada Šibenika" in feed["publisher"]
