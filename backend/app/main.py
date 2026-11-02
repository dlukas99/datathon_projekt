"""FastAPI application entry point."""

from __future__ import annotations

from typing import Annotated, Any, Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse

from app.geo import in_bbox
from app.geocode import Suggestion, get_geocoder
from app.layers import get_layers
from app.models import Location, Report, SourceInfo
from app.report import OutsideCroatia, build_report, locate, report_geojson
from app.sources import manifest, source_info

app = FastAPI(
    title="Prije potpisa API",
    description=(
        "Okolišni pregled adrese u Hrvatskoj iz otvorenih podataka. Svaka vrijednost nosi "
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


@app.on_event("startup")
def warm_up() -> None:
    # Load in-memory indexes once so the first report is fast.
    get_geocoder()
    get_layers()


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
        raise HTTPException(status_code=422, detail="Lokacija nije u Hrvatskoj.")


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


@app.get("/api/sources", tags=["izvori"], response_model=list[SourceInfo])
def sources() -> list[SourceInfo]:
    """Svi izvori korišteni u obradi, s licencom i datumom preuzimanja."""
    ids = [*manifest(), "pvgis", "valhalla"]
    return [source_info(s) for s in ids]
