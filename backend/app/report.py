"""Assemble the full report for a point."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any

from analysis.daily import car_free_category, daily_category, transit_category
from analysis.environment import (
    air_category,
    fire_category,
    flood_category,
    green_category,
    noise_category,
)
from analysis.solar import solar_category
from analysis.walking import compute_reach
from app import fmt, valhalla
from app.admin import get_admin
from app.layers import get_layers
from app.models import Category, Location, Report, SourceInfo, Value
from app.sources import retrieved_at, source_info

DISCLAIMER = (
    "Prije potpisa informativni je alat izrađen iz otvorenih podataka i modela. Nije službena "
    "procjena rizika, geodetski ni građevinski pregled i ne zamjenjuje karte i upozorenja "
    "nadležnih tijela (Hrvatske vode, DHMZ, civilna zaštita). Način izračuna opisan je u "
    "metodologiji."
)

TIMETABLE_SOURCES = ("gtfs_zet", "gtfs_hzpp", "autotrolej")


class OutsideCroatia(ValueError):
    pass


def locate(lat: float, lon: float, label: str | None = None) -> Location:
    admin = get_admin()
    place = admin.lookup(lon, lat) if admin else None
    if admin is not None and place is None:
        raise OutsideCroatia("Lokacija nije u Hrvatskoj.")
    population = None
    if place is not None and place.population is not None:
        population = Value(
            key="settlement_population",
            label=f"Stanovnika u naselju {place.settlement}",
            value=place.population,
            unit="stanovnika",
            display=f"{fmt.num(place.population)} stanovnika (Popis 2021.)",
            source="dzs_popis",
            retrieved_at=retrieved_at("dzs_popis"),
            kind="measured",
        )
    return Location(
        lat=round(lat, 6),
        lon=round(lon, 6),
        label=label,
        settlement=place.settlement if place else None,
        municipality=place.municipality if place else None,
        county=place.county if place else None,
        population=population,
    )


def summary(categories: dict[str, Category]) -> list[str]:
    """Two to three sentences built only from category headlines (templates)."""
    sentences = [categories["flood"].headline, categories["air"].headline]
    car_free = categories["car_free"]
    if car_free.status != "no_data":
        sentences.append(car_free.headline.split(" Nedostaje:")[0].split(" Nije provjereno:")[0])
    return sentences


def _isochrones(lat: float, lon: float) -> dict[str, Any] | None:
    try:
        data = valhalla.isochrones(lat, lon)
    except valhalla.RouterUnavailable:
        return None
    if not isinstance(data, dict):
        return None
    for feature in data.get("features", []):
        props = feature.get("properties", {})
        feature["properties"] = {"minutes": props.get("contour")}
    return data


def build_report(lat: float, lon: float, label: str | None = None) -> Report:
    location = locate(lat, lon, label)
    layers = get_layers()
    with ThreadPoolExecutor(max_workers=3) as pool:
        solar_future = pool.submit(solar_category, lat, lon)
        iso_future = pool.submit(_isochrones, lat, lon)
        reach = compute_reach(lat, lon, layers)
        solar = solar_future.result()
        iso = iso_future.result()

    has_timetables = any(layers.category("stop").sources.count(s) for s in TIMETABLE_SOURCES)
    cats = {
        "flood": flood_category(lon, lat),
        "air": air_category(lon, lat),
        "green": green_category(lon, lat, reach.nearest("park")),
        "noise": noise_category(lon, lat, layers),
        "fire": fire_category(lon, lat, layers),
        "solar": solar,
        "car_free": car_free_category(reach),
        "transit": transit_category(reach, has_timetables),
        "daily": daily_category(reach),
    }
    used: list[str] = []
    for cat in cats.values():
        for v in cat.values:
            if v.source not in used:
                used.append(v.source)
        for p in cat.places:
            if p.source not in used:
                used.append(p.source)
    if location.population is not None:
        used.append("dzs_popis")
    for extra in ("dgu_au", "valhalla"):
        if extra not in used:
            used.append(extra)
    sources: list[SourceInfo] = [source_info(s) for s in used]
    return Report(
        location=location,
        generated_at=datetime.now(UTC).isoformat(timespec="seconds"),
        summary=summary(cats),
        categories=list(cats.values()),
        isochrones=iso,
        sources=sources,
        disclaimer=DISCLAIMER,
    )


def report_geojson(report: Report) -> dict[str, Any]:
    """The same report as a GeoJSON FeatureCollection (EPSG:4326)."""
    loc = report.location
    features: list[dict[str, Any]] = [
        {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [loc.lon, loc.lat]},
            "properties": {
                "role": "location",
                "label": loc.label,
                "settlement": loc.settlement,
                "municipality": loc.municipality,
                "county": loc.county,
                "generated_at": report.generated_at,
                "summary": report.summary,
                "disclaimer": report.disclaimer,
                "categories": [c.model_dump(exclude={"places"}) for c in report.categories],
            },
        }
    ]
    for feature in (report.isochrones or {}).get("features", []):
        features.append(
            {
                "type": "Feature",
                "geometry": feature["geometry"],
                "properties": {
                    "role": "isochrone",
                    "minutes": feature["properties"].get("minutes"),
                    "source": "valhalla",
                    "kind": "modelled",
                },
            }
        )
    for cat in report.categories:
        for place in cat.places:
            features.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [place.lon, place.lat]},
                    "properties": {"role": "place", **place.model_dump(exclude={"lat", "lon"})},
                }
            )
    return {"type": "FeatureCollection", "features": features}
