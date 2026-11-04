"""API response models. Every value carries its source, retrieval date and kind."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

Kind = Literal["measured", "modelled", "estimate"]
Status = Literal["good", "warning", "bad", "no_data", "info"]


class Value(BaseModel):
    """A single reported value with provenance (CLAUDE.md, rule 2)."""

    key: str
    label: str
    value: float | int | str | bool | None
    unit: str | None = None
    display: str = Field(description="Value formatted for people, in Croatian")
    source: str = Field(description="Source id, see `sources` in the report")
    retrieved_at: str | None = Field(description="When the source was retrieved (ISO 8601)")
    kind: Kind
    note: str | None = None


class Link(BaseModel):
    label: str
    url: str


class Place(BaseModel):
    """A point of interest with walking time."""

    category: str
    name: str
    lat: float
    lon: float
    walk_minutes: float | None
    distance_m: float | None
    source: str
    retrieved_at: str | None
    kind: Kind
    detail: str | None = None


class ScaleBand(BaseModel):
    """One band of a graded scale: values up to `upto` (None = no upper limit)."""

    upto: float | None
    label: str
    status: Status


class ScaleMarker(BaseModel):
    value: float
    label: str


class Scale(BaseModel):
    """A value placed on a graded scale with sourced reference marks."""

    key: str
    label: str
    unit: str
    value: float
    band: str
    bands: list[ScaleBand]
    markers: list[ScaleMarker] = []


class Category(BaseModel):
    id: str
    group: Literal["environment", "car_free", "daily"]
    title: str
    status: Status
    status_label: str
    headline: str
    values: list[Value] = []
    places: list[Place] = []
    notes: list[str] = []
    links: list[Link] = []
    scales: list[Scale] = []


class Location(BaseModel):
    lat: float
    lon: float
    label: str | None = None
    settlement: str | None = None
    municipality: str | None = None
    county: str | None = None
    population: Value | None = Field(
        default=None, description="Broj stanovnika naselja (Popis 2021.)"
    )
    in_croatia: bool = True


class SourceInfo(BaseModel):
    id: str
    title: str
    publisher: str
    url: str
    license: str
    retrieved_at: str | None = None
    data_date: str | None = None


class Report(BaseModel):
    location: Location
    generated_at: str
    summary: list[str]
    categories: list[Category]
    isochrones: dict[str, Any] | None = Field(
        default=None, description="GeoJSON FeatureCollection of 5, 10 and 15 minute walks"
    )
    sources: list[SourceInfo]
    disclaimer: str
