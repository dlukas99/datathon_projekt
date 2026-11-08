"""Walking times from an address to nearby places, in one router request."""

from __future__ import annotations

from dataclasses import dataclass, field

from shapely.geometry import Point
from shapely.ops import nearest_points

from app import valhalla
from app.geo import to_htrs, to_wgs84
from app.layers import Layers
from app.models import Place
from app.sources import retrieved_at

# Search radius for candidates: 15 minutes at 4.5 km/h is 1125 m along the network,
# which is never shorter than the straight line, so 1300 m keeps every candidate.
CANDIDATE_RADIUS_M = 1300.0
# Beyond the radius we still route to the few nearest places to report "nearest".
NEAREST_FALLBACK = 3
MAX_PER_CATEGORY = 40
MAX_FALLBACK_DISTANCE_M = 15000.0

POINT_CATEGORIES = (
    "grocery",
    "pharmacy",
    "doctor",
    "pediatrician",
    "kindergarten",
    "school",
    "playground",
    "recycling",
    "stop",
)


@dataclass
class Reach:
    places: dict[str, list[Place]] = field(default_factory=dict)
    router_ok: bool = True

    def within(self, category: str, minutes: float) -> list[Place]:
        return [
            p
            for p in self.places.get(category, [])
            if p.walk_minutes is not None and p.walk_minutes <= minutes
        ]

    def nearest(self, category: str) -> Place | None:
        places = self.places.get(category, [])
        return places[0] if places else None

    def nearby(self, minutes: float, nearest: int = NEAREST_FALLBACK) -> list[Place]:
        """Every place within `minutes` and at least the `nearest` closest of each kind."""
        result: list[Place] = []
        for category, places in self.places.items():
            # places are sorted by walking time, so the ones within reach come first
            result.extend(places[: max(len(self.within(category, minutes)), nearest)])
        return result


def _sort_key(p: Place) -> tuple[int, float]:
    if p.walk_minutes is not None:
        return (0, p.walk_minutes)
    return (1, p.distance_m or 0.0)


def _park_candidates(layers: Layers, x: float, y: float) -> list[Place]:
    parks = layers.parks
    if parks is None:
        return []
    origin = Point(x, y)
    idx = list(parks.tree.query(origin.buffer(CANDIDATE_RADIUS_M), predicate="intersects"))
    if not idx:
        nearest = parks.tree.query_nearest(origin, max_distance=MAX_FALLBACK_DISTANCE_M)
        idx = [int(i) for i in nearest]
    places = []
    for i in idx[:MAX_PER_CATEGORY]:
        geom = parks.geoms[int(i)]
        if geom.contains(origin):
            px, py = x, y
        else:
            target = nearest_points(geom, origin)[0]
            px, py = target.x, target.y
        lon, lat = to_wgs84(px, py)
        places.append(
            Place(
                category="park",
                name=parks.names[int(i)] or "Park bez naziva",
                lat=round(lat, 6),
                lon=round(lon, 6),
                walk_minutes=None,
                distance_m=round(float(origin.distance(Point(px, py)))),
                source="osm",
                retrieved_at=retrieved_at("osm"),
                kind="modelled",
                detail="ulaz najbliži adresi (rub parka)",
            )
        )
    return places


def compute_reach(
    lat: float, lon: float, layers: Layers, extra: dict[str, list[Place]] | None = None
) -> Reach:
    """Find candidate places per category and route to all of them at once.

    `extra` lets other modules (public transport) add their own candidates.
    """
    x, y = to_htrs(lon, lat)
    candidates: dict[str, list[Place]] = {}
    for cat in POINT_CATEGORIES:
        layer = layers.category(cat)
        found = []
        for i in layer.nearest(x, y, CANDIDATE_RADIUS_M, NEAREST_FALLBACK, MAX_PER_CATEGORY):
            dist = layer.distance(i, x, y)
            if dist > MAX_FALLBACK_DISTANCE_M:
                continue
            found.append(
                Place(
                    category=cat,
                    name=layer.names[i] or "",
                    lat=round(float(layer.lat[i]), 6),
                    lon=round(float(layer.lon[i]), 6),
                    walk_minutes=None,
                    distance_m=round(dist),
                    source=layer.sources[i],
                    retrieved_at=retrieved_at(layer.sources[i]),
                    kind="modelled",
                    detail=layer.details[i] or None,
                )
            )
        candidates[cat] = found
    candidates["park"] = _park_candidates(layers, x, y)
    for cat, places in (extra or {}).items():
        candidates[cat] = places

    flat = [p for places in candidates.values() for p in places]
    reach = Reach()
    if flat:
        try:
            times = valhalla.walk_minutes(lat, lon, [(p.lat, p.lon) for p in flat])
        except (valhalla.RouterUnavailable, KeyError, IndexError, TypeError):
            reach.router_ok = False
            times = [None] * len(flat)
        for place, minutes in zip(flat, times, strict=True):
            place.walk_minutes = minutes
    for cat, places in candidates.items():
        reach.places[cat] = sorted(places, key=_sort_key)
    return reach
