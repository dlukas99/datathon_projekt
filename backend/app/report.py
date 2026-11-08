"""Assemble the full report for a point."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime
from typing import Any

from analysis import score
from analysis.daily import WALK_LIMIT_MIN, car_free_category, daily_category, transit_category
from analysis.environment import (
    air_category,
    air_level,
    fire_category,
    flood_category,
    green_category,
    noise_category,
)
from analysis.solar import solar_category
from analysis.walking import compute_reach
from app import brand, fmt, valhalla
from app.admin import get_admin
from app.layers import get_layers
from app.models import Category, Location, Report, SourceInfo, Value
from app.sources import retrieved_at, source_info

DISCLAIMER = (
    f"{brand.NAME} informativni je alat izrađen iz otvorenih podataka i modela. Nije službena "
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


FLOOD_WARNINGS: dict[str, str] = {
    "bad": "Pažnja: lokacija je u području koje rijeka može poplaviti.",
    "warning": "Pažnja: u rijetkim velikim poplavama rijeka može doći do ove lokacije ili "
    "sasvim blizu nje.",
}
AIR_PHRASES: dict[str, str] = {"vrlo niska": "čistim zrakom", "niska": "dobrim zrakom"}
AIR_CONCERNS: dict[str, str] = {
    "umjerena": "zrak je osrednji, lošiji nego što preporučuje Svjetska zdravstvena organizacija",
    "visoka": "zrak je loš",
}


def _value(cat: Category, key: str) -> Any:
    return next((v.value for v in cat.values if v.key == key), None)


def summary(categories: dict[str, Category]) -> list[str]:
    """Two or three plain sentences, built only from category statuses (templates).

    What is really good or bad here comes first; a flood is named first only when the
    location is in or next to a modelled flood area.
    """
    flood, air, green = categories["flood"], categories["air"], categories["green"]
    noise, car_free = categories["noise"], categories["car_free"]
    level = air_level(air)
    sentences: list[str] = []
    if flood.status in FLOOD_WARNINGS:
        sentences.append(FLOOD_WARNINGS[flood.status])

    quiet = noise.status == "good"
    withs: list[str] = []
    if level in AIR_PHRASES:
        withs.append(AIR_PHRASES[level])
    if green.status == "good":
        withs.append("puno zelenila")
    no_flood = flood.status == "good"
    # Safety from floods is named in the opening sentence only next to other good news;
    # alone it gets a short sentence at the end, so it never leads by default.
    if no_flood and (quiet or withs):
        withs.append("bez opasnosti od riječnih poplava")
        no_flood = False
    if quiet or withs:
        head = "Mirno mjesto" if quiet else "Mjesto"
        if not withs:
            sentences.append("Mirno mjesto, podalje od velikih cesta.")
        else:
            phrase = withs[0] if len(withs) == 1 else ", ".join(withs[:-1]) + " i " + withs[-1]
            joiner = " " if phrase.startswith("bez") else " s "
            sentences.append(f"{head}{joiner}{phrase}.")

    if car_free.status != "no_data":
        have = _value(car_free, "needs_within_15min")
        missing = _value(car_free, "needs_missing")
        unknown = _value(car_free, "needs_unknown")
        if isinstance(have, int):
            if (not missing or missing == "ništa") and not unknown:
                sentences.append("Sve što trebate svaki dan imate pješice unutar 15 minuta.")
            elif not missing or missing == "ništa":
                sentences.append(
                    "Trgovinu, ljekarnu, liječnika, vrtić, školu i park imate pješice unutar "
                    "15 minuta."
                )
            elif have >= 4:
                sentences.append(
                    f"Većinu svakodnevnih potreba imate pješice unutar 15 minuta, "
                    f"ali nedostaje: {missing}."
                )
            else:
                sentences.append(
                    "Za većinu svakodnevnih potreba trebat će vam auto ili javni prijevoz."
                )
    if no_flood:
        sentences.append("Riječne poplave ovdje ne prijete.")

    concerns: list[str] = []
    if noise.status == "warning":
        concerns.append("velika cesta je blizu")
    if level in AIR_CONCERNS:
        concerns.append(AIR_CONCERNS[level])
    if green.status == "bad":
        concerns.append("malo je drveća i hlada")
    if concerns:
        sentences.append(f"Na što obratiti pažnju: {concerns[0]}.")
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
    score.attach(cats.values())
    nearby = reach.nearby(WALK_LIMIT_MIN)
    used: list[str] = []
    for cat in cats.values():
        for v in cat.values:
            if v.source not in used:
                used.append(v.source)
        for p in cat.places:
            if p.source not in used:
                used.append(p.source)
    for p in nearby:
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
        nearby_places=nearby,
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
