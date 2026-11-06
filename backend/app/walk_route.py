"""Walking route from the report point to a place on the map (`GET /api/route`).

The route comes from the same Valhalla router, costing and walking speed as the
isochrones and the walking times in the report, so the minutes on the map and in the
"Svakodnevni život" list agree. Routes are computed only when someone asks for one.
"""

from __future__ import annotations

import math

from app import valhalla
from app.geo import to_htrs
from app.models import LineString, RouteFeature, RouteProperties
from app.sources import retrieved_at

# Places on the map are at most 15 km away in a straight line (analysis/walking.py).
MAX_ROUTE_DISTANCE_M = 20_000.0


class TooFar(ValueError):
    """The two points are too far apart for a walking route."""


def straight_distance_m(start: tuple[float, float], end: tuple[float, float]) -> float:
    """Straight-line distance between two (lat, lon) points, in metres (HTRS96/TM)."""
    return math.dist(to_htrs(start[1], start[0]), to_htrs(end[1], end[0]))


def route_feature(path: valhalla.WalkPath) -> RouteFeature:
    return RouteFeature(
        geometry=LineString(coordinates=path.coordinates),
        properties=RouteProperties(
            distance_m=round(path.length_m),
            # the router's time, rounded like the walking times in the report
            walk_minutes=round(path.time_s / 60.0, 1),
            walking_speed_kmh=valhalla.WALKING_SPEED_KMH,
            source="valhalla",
            retrieved_at=retrieved_at("valhalla"),
            kind="modelled",
        ),
    )


def walk_route(start: tuple[float, float], end: tuple[float, float]) -> RouteFeature | None:
    """Route between two (lat, lon) points, or None when the router finds no path.

    Raises TooFar for points more than 20 km apart and valhalla.RouterUnavailable when
    the router does not answer.
    """
    if straight_distance_m(start, end) > MAX_ROUTE_DISTANCE_M:
        raise TooFar("Odredište je predaleko za pješački put.")
    path = valhalla.route(start, end)
    return route_feature(path) if path else None
