"""FastAPI application entry point."""

from __future__ import annotations

import gzip
import json
import threading
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Annotated, Any, Literal

from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from app import brand, map_layer, pvgis, valhalla
from app.address_grid import get_address_grid
from app.assistant import AssistantReply, AssistantRequest, answer
from app.config import REPO_ROOT
from app.finder import (
    FindOptions,
    FindRequest,
    FindResponse,
    ParseUnavailable,
    find,
    options,
    parse_question,
)
from app.geo import in_bbox
from app.geocode import Suggestion, get_geocoder
from app.layers import get_layers
from app.live_sources import LiveSources, live_sources
from app.models import Location, Report, RouteFeature, SourceInfo
from app.report import OutsideCroatia, build_report, locate, report_geojson
from app.sources import manifest, source_info
from app.walk_route import TooFar, walk_route


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    warm_up()
    yield


app = FastAPI(
    lifespan=lifespan,
    title=f"{brand.NAME} API",
    description=(
        f"{brand.TAGLINE}, iz otvorenih podataka. Svaka vrijednost nosi "
        "izvor (`source`), datum preuzimanja izvora (`retrieved_at`) i vrstu (`kind`: "
        "`measured`, `modelled` ili `estimate`). Informativni alat, nije službena procjena."
    ),
    version="0.1.0",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url=None,
)

Lat = Annotated[float, Query(ge=-90, le=90, description="Geografska širina (WGS84)")]
Lon = Annotated[float, Query(ge=-180, le=180, description="Geografska dužina (WGS84)")]


def warm_up() -> None:
    # Load in-memory indexes once so the first report is fast.
    get_geocoder()
    get_layers()
    get_address_grid()  # house numbers around a point, for the greenery card
    demo = REPO_ROOT / "scripts" / "demo_addresses.json"
    if demo.exists():
        points = json.loads(demo.read_text(encoding="utf-8"))["addresses"]
        pvgis.warm([(p["lat"], p["lon"]) for p in points])
    # The map layers take a few seconds to build; do it in the background.
    threading.Thread(target=map_layer.warm, daemon=True).start()


@app.get("/api/health", tags=["sustav"])
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/geocode", tags=["adrese"], response_model=list[Suggestion])
def geocode(
    q: Annotated[str, Query(min_length=2, max_length=120, description="Adresa ili naselje")],
    limit: Annotated[int, Query(ge=1, le=20)] = 8,
) -> list[Suggestion]:
    """Prijedlozi adresa, ulica i naselja (DGU adrese i upravne jedinice)."""
    return get_geocoder().search(q, limit=limit)


def _check_point(lat: float, lon: float) -> None:
    if not in_bbox(lon, lat):
        raise HTTPException(status_code=422, detail="Lokacija nije na kopnu u Hrvatskoj.")


@app.get("/api/reverse", tags=["adrese"], response_model=Location)
def reverse(lat: Lat, lon: Lon) -> Location:
    """Naselje, grad ili općina i županija za točku."""
    _check_point(lat, lon)
    try:
        return locate(lat, lon)
    except OutsideCroatia as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get(
    "/api/report",
    tags=["izvještaj"],
    response_model=Report,
    responses={200: {"content": {"application/geo+json": {}}}},
)
def report(
    lat: Lat,
    lon: Lon,
    label: Annotated[str | None, Query(max_length=200)] = None,
    format: Annotated[Literal["json", "geojson"], Query()] = "json",
) -> Any:
    """Okolišni pregled, život bez auta i svakodnevni život za točku."""
    _check_point(lat, lon)
    try:
        result = build_report(lat, lon, label)
    except OutsideCroatia as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    if format == "geojson":
        return JSONResponse(report_geojson(result), media_type="application/geo+json")
    return result


ROUTE_UNAVAILABLE = "Put trenutačno nije moguće izračunati. Pokušajte ponovno."


@app.get(
    "/api/route",
    tags=["izvještaj"],
    response_model=RouteFeature,
    responses={
        404: {"description": "Usmjerivač nije pronašao pješački put"},
        503: {"description": "Usmjerivač trenutačno ne odgovara"},
    },
)
def route(from_lat: Lat, from_lon: Lon, to_lat: Lat, to_lon: Lon) -> RouteFeature:
    """Pješački put po ulicama i stazama od točke izvještaja do mjesta na karti (GeoJSON).

    Isti usmjerivač (Valhalla), profil i brzina hoda kao izokrone i vremena u izvještaju.
    Računa se samo na zahtjev i ne sprema se.
    """
    _check_point(from_lat, from_lon)
    _check_point(to_lat, to_lon)
    try:
        result = walk_route((from_lat, from_lon), (to_lat, to_lon))
    except TooFar as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except (valhalla.RouterUnavailable, ValueError, KeyError) as exc:
        raise HTTPException(status_code=503, detail=ROUTE_UNAVAILABLE) from exc
    if result is None:
        raise HTTPException(status_code=404, detail="Pješački put do ovog mjesta nije pronađen.")
    return result


@app.get("/api/sources", tags=["izvori"], response_model=list[SourceInfo])
def sources() -> list[SourceInfo]:
    """Svi izvori korišteni u obradi, s licencom i datumom preuzimanja."""
    ids = [*manifest(), "pvgis", "valhalla"]
    return [source_info(s) for s in ids]


@app.get("/api/sources/live", tags=["izvori"], response_model=LiveSources)
def sources_live() -> LiveSources:
    """Datumi zadnje izmjene korištenih skupova uživo s Portala otvorenih podataka (CKAN)."""
    return live_sources()


@app.post("/api/assistant", tags=["asistent"], response_model=AssistantReply)
def assistant(request: AssistantRequest) -> AssistantReply:
    """Odgovor na pitanje o jednoj ili dvjema adresama, samo iz rezultata izračuna.

    Pitanja se ne spremaju i ne bilježe.
    """
    for point in request.locations:
        _check_point(point.lat, point.lon)
    try:
        return answer(request, build_report)
    except OutsideCroatia as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@app.get("/api/find/options", tags=["predloži mjesto"], response_model=FindOptions)
def find_options() -> FindOptions:
    """Županije, broj obuhvaćenih naselja i je li dostupan jezični model."""
    return options()


@app.post("/api/find", tags=["predloži mjesto"], response_model=FindResponse)
def find_places(request: FindRequest) -> FindResponse:
    """Najbolja naselja prema filtrima i ocjeni mjesta; deterministički izračun."""
    return find(request)


class ParseQuestion(BaseModel):
    question: str = Field(min_length=3, max_length=300)


@app.post("/api/find/parse", tags=["predloži mjesto"], response_model=FindRequest)
def find_parse(body: ParseQuestion) -> FindRequest:
    """Slobodno pitanje u filtre (samo ako je postavljen jezični model). Pitanje se ne sprema."""
    try:
        return parse_question(body.question)
    except ParseUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


# --- Karta Hrvatske --------------------------------------------------------------------------

MAP_CACHE = "public, max-age=3600"


def _gzip_response(body: bytes, request: Request) -> Response:
    """Pre-compressed body; decompressed for the rare client that does not accept gzip."""
    if "gzip" in request.headers.get("accept-encoding", ""):
        return Response(
            body,
            media_type="application/json",
            headers={
                "Content-Encoding": "gzip",
                "Cache-Control": MAP_CACHE,
                "Vary": "Accept-Encoding",
            },
        )
    return Response(
        gzip.decompress(body), media_type="application/json", headers={"Cache-Control": MAP_CACHE}
    )


@app.get("/api/map/geometry/{level}", tags=["karta"])
def map_geometry(level: Literal["overview", "detail"], request: Request) -> Response:
    """Pojednostavljene granice svih naselja (DGU) u sažetom obliku.

    `{"step": s, "features": [[id, [[[x0, y0, dx1, dy1, ...], ...], ...]], ...]}`: koordinate
    su cijeli brojevi u koracima od `s` stupnjeva, svaka sljedeća kao razlika od prethodne;
    `id` je šifra naselja. `overview` (300 m) služi za cijelu Hrvatsku, `detail` (80 m) za
    približeni prikaz.
    """
    return _gzip_response(map_layer.geometry(level), request)


@app.get("/api/map/settlements", tags=["karta"], response_model=map_layer.MapColumns)
def map_settlements(request: Request) -> Response:
    """Pokazatelji za središte svakog naselja u Hrvatskoj, za bojenje karte."""
    return _gzip_response(map_layer.table_json(), request)


@app.get("/api/map/point", tags=["karta"], response_model=map_layer.MapPoint)
def map_point(lat: Lat, lon: Lon) -> map_layer.MapPoint:
    """Što je na kliknutoj točki: naselje, more ili područje izvan Hrvatske. Točka se ne sprema."""
    return map_layer.point(lat, lon)
