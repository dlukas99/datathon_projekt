"""Daily needs, public transport and the car-free summary, built on walking times."""

from __future__ import annotations

from analysis.status import label
from analysis.walking import Reach
from app import fmt
from app.models import Category, Place, Status, Value

WALK_LIMIT_MIN = 15.0
TRANSIT_LIMIT_MIN = 10.0

DAILY_ITEMS: tuple[tuple[str, str, str], ...] = (
    # category, label, label for "nearest ..."
    ("kindergarten", "Vrtić", "najbliži vrtić"),
    ("school", "Osnovna škola", "najbliža osnovna škola"),
    ("doctor", "Obiteljski liječnik", "najbliža ordinacija obiteljske medicine"),
    ("pediatrician", "Pedijatar", "najbliža pedijatrijska ordinacija"),
    ("pharmacy", "Ljekarna", "najbliža ljekarna"),
    ("grocery", "Trgovina namirnicama", "najbliža trgovina namirnicama"),
    ("playground", "Igralište", "najbliže igralište"),
    ("recycling", "Reciklaža (spremnici ili dvorište)", "najbliže mjesto za odvojeno odlaganje"),
)

# The seven needs of the car-free check (CLAUDE.md, section 6).
CAR_FREE_NEEDS: tuple[tuple[str, str], ...] = (
    ("grocery", "trgovina namirnicama"),
    ("pharmacy", "ljekarna"),
    ("doctor", "obiteljski liječnik"),
    ("kindergarten", "vrtić"),
    ("school", "osnovna škola"),
    ("park", "park"),
    ("frequent_stop", "stajalište s barem jednim polaskom na sat radnim danom"),
)


# Source shown when nothing was found (the layer that was searched).
SEARCHED_SOURCE = {
    "doctor": "hzzo_doctor",
    "pediatrician": "hzzo_pediatrician",
    "pharmacy": "hzzo_ljekarne",
    "kindergarten": "mzom_vrtici",
    "school": "mzom_skole",
    "recycling": "osm",
}


def departures(per_hour: float) -> str:
    """Departures per hour as a whole number with the right Croatian form ("32 polaska")."""
    n = max(1, round(per_hour))
    return f"{fmt.num(n)} {fmt.plural(n, 'polazak', 'polaska', 'polazaka')}"


def _value_for_nearest(cat: str, title: str, place: Place | None, router_ok: bool) -> Value:
    if place is None:
        return Value(
            key=f"nearest_{cat}",
            label=title,
            value=None,
            display="nije pronađeno u krugu od 15 km",
            source=SEARCHED_SOURCE.get(cat, "osm"),
            retrieved_at=None,
            kind="modelled",
        )
    if place.walk_minutes is not None:
        display = fmt.walk(place.walk_minutes)
        value: float | None = place.walk_minutes
        unit = "min"
        kind = place.kind
    else:
        display = f"{fmt.metres(place.distance_m)} zračne udaljenosti"
        value = place.distance_m
        unit = "m"
        kind = "estimate"
    name = place.name or "bez naziva"
    return Value(
        key=f"nearest_{cat}",
        label=title,
        value=value,
        unit=unit,
        display=f"{display} ({name})",
        source=place.source,
        retrieved_at=place.retrieved_at,
        kind=kind,
        note=None
        if router_ok
        else "Mreža hoda nije bila dostupna; prikazana je zračna udaljenost.",
    )


def frequent_stops(reach: Reach) -> list[Place]:
    return [
        p
        for p in reach.within("stop", WALK_LIMIT_MIN)
        if p.detail is not None and _departures(p) >= 1.0
    ]


def _departures(place: Place) -> float:
    # detail of a GTFS stop: "<mode>|<departures per hour>|<feed>"
    parts = (place.detail or "").split("|")
    try:
        return float(parts[1])
    except (IndexError, ValueError):
        return -1.0


def daily_category(reach: Reach) -> Category:
    values = []
    places: list[Place] = []
    for cat, title, _ in DAILY_ITEMS:
        nearest = reach.nearest(cat)
        values.append(_value_for_nearest(cat, title, nearest, reach.router_ok))
        within = reach.within(cat, WALK_LIMIT_MIN)
        values.append(
            Value(
                key=f"count15_{cat}",
                label=f"{title}: broj unutar 15 minuta hoda",
                value=len(within) if reach.router_ok else None,
                display=str(len(within)) if reach.router_ok else "nije izračunato",
                source=nearest.source if nearest else "osm",
                retrieved_at=nearest.retrieved_at if nearest else None,
                kind="modelled",
            )
        )
        places.extend(within or ([nearest] if nearest else []))
    found = sum(1 for cat, _, _ in DAILY_ITEMS if reach.within(cat, WALK_LIMIT_MIN))
    headline = (
        f"Unutar 15 minuta hoda nalazi se {found} od {len(DAILY_ITEMS)} vrsta "
        "svakodnevnih ustanova i trgovina."
        if reach.router_ok
        else "Mreža hoda trenutačno nije dostupna; prikazane su zračne udaljenosti."
    )
    return Category(
        id="daily",
        group="daily",
        title="Svakodnevni život",
        status="info" if reach.router_ok else "no_data",
        status_label=label("info" if reach.router_ok else "no_data"),
        headline=headline,
        values=values,
        places=places,
        notes=[
            "Trgovine, igrališta i većina mjesta za reciklažu dolaze iz OpenStreetMapa, koji "
            "izvan gradova nije potpun: „nije pronađeno” može značiti i da objekt nije ucrtan.",
        ],
    )


def _stops_phrase(n: int) -> str:
    verb = fmt.plural(n, "nalazi se", "nalaze se", "nalazi se")
    noun = fmt.plural(n, "stajalište", "stajališta", "stajališta")
    return f"{verb} {n} {noun}"


def transit_category(reach: Reach, has_timetables: bool) -> Category:
    stops = reach.within("stop", TRANSIT_LIMIT_MIN)
    with_tt = [p for p in stops if _departures(p) >= 0]
    best = max((_departures(p) for p in with_tt), default=None)
    values = [
        Value(
            key="stops_10min",
            label="Stajališta unutar 10 minuta hoda",
            value=len(stops),
            display=str(len(stops)),
            source="osm",
            retrieved_at=stops[0].retrieved_at if stops else None,
            kind="modelled",
        )
    ]
    if best is not None:
        top = max(with_tt, key=_departures)
        values.append(
            Value(
                key="max_departures_per_hour",
                label="Najviše polazaka na sat radnim danom (jedno stajalište)",
                value=round(best, 1),
                unit="polazaka/h",
                display=f"{departures(best)} na sat ({top.name})",
                source=top.source,
                retrieved_at=top.retrieved_at,
                kind="measured",
                note="Prosjek od 6 do 20 sati za jedan radni dan iz voznog reda.",
            )
        )
    status: Status
    if not reach.router_ok:
        status, headline = "no_data", "Mreža hoda trenutačno nije dostupna."
    elif not stops:
        status, headline = (
            "info",
            "Unutar 10 minuta hoda nema ucrtanih stajališta javnog prijevoza.",
        )
    elif best is None:
        n = len(stops)
        status = "info"
        headline = (
            f"Unutar 10 minuta hoda {_stops_phrase(n)}; "
            "vozni red za ovo područje nije dostupan u otvorenom obliku."
        )
    else:
        status = "info"
        headline = (
            f"Unutar 10 minuta hoda {_stops_phrase(len(stops))}, "
            f"s najviše {departures(best)} na sat radnim danom."
        )
    notes = []
    if stops and not with_tt:
        notes.append("Stajališta su iz OpenStreetMapa, bez voznog reda.")
    if not has_timetables:
        notes.append("Vozni redovi u otvorenom obliku (GTFS) nisu učitani.")
    return Category(
        id="transit",
        group="car_free",
        title="Javni prijevoz",
        status=status,
        status_label=label(status),
        headline=headline,
        values=values,
        places=stops[:30],
        notes=notes,
    )


def car_free_category(reach: Reach) -> Category:
    have: list[str] = []
    missing: list[str] = []
    unknown: list[str] = []
    stops = reach.within("stop", WALK_LIMIT_MIN)
    timetabled = [p for p in stops if _departures(p) >= 0]
    for cat, name in CAR_FREE_NEEDS:
        if cat == "frequent_stop":
            if frequent_stops(reach):
                have.append(name)
            elif stops and not timetabled:
                unknown.append(name)  # stops exist, but no open timetable to check
            else:
                missing.append(name)
        elif reach.within(cat, WALK_LIMIT_MIN):
            have.append(name)
        else:
            missing.append(name)
    n = len(have)
    total = len(CAR_FREE_NEEDS)
    if not reach.router_ok:
        return Category(
            id="car_free",
            group="car_free",
            title="Život bez auta",
            status="no_data",
            status_label=label("no_data"),
            headline="Mreža hoda trenutačno nije dostupna, pa provjeru nije moguće napraviti.",
        )
    headline = f"{n} od {total} svakodnevnih potreba dostupno je unutar 15 minuta hoda."
    if missing:
        headline += " Nedostaje: " + ", ".join(missing) + "."
    if unknown:
        headline += (
            " Nije provjereno: " + ", ".join(unknown) + " (stajališta postoje, ali vozni red "
            "nije dostupan u otvorenom obliku)."
        )
    values = [
        Value(
            key="needs_within_15min",
            label="Svakodnevne potrebe unutar 15 minuta hoda",
            value=n,
            unit=f"od {total}",
            display=f"{n} od {total}",
            source="valhalla",
            retrieved_at=None,
            kind="modelled",
        ),
        Value(
            key="needs_missing",
            label="Nedostaje unutar 15 minuta hoda",
            value=", ".join(missing) if missing else "ništa",
            display=", ".join(missing) if missing else "ništa",
            source="valhalla",
            retrieved_at=None,
            kind="modelled",
        ),
    ]
    if unknown:
        values.append(
            Value(
                key="needs_unknown",
                label="Nije moguće provjeriti",
                value=", ".join(unknown),
                display=", ".join(unknown),
                source="osm",
                retrieved_at=None,
                kind="modelled",
            )
        )
    return Category(
        id="car_free",
        group="car_free",
        title="Život bez auta",
        status="info",
        status_label=label("info"),
        headline=headline,
        values=values,
    )
