"""Land cover within 300 m: a metric circle, whole across tile edges, and a village among
fields is never judged by the urban 3-30-300 rule.

Control values were computed independently (outside the app) in the equal-area EPSG:3035
projection from the same WorldCover tiles, and checked on the DGU orthophoto 2021/22.
"""

from __future__ import annotations

import math

import numpy as np
import pytest
from pyproj import Geod

from analysis.environment import (
    GREEN_BUFFER_M,
    _worldcover_path,
    green_category,
    green_status,
    landcover_pixels,
    landcover_shares,
    metres_per_degree,
)
from analysis.score import green_points

WGS84 = Geod(ellps="WGS84")
PIXEL_DEG = 1 / 12000  # WorldCover 10 m grid: 3 degrees in 36,000 pixels


def test_metres_per_degree_matches_the_ellipsoid() -> None:
    for lat in (42.5, 45.0, 46.4):
        lon_m, lat_m = metres_per_degree(lat)
        _, _, d_lon = WGS84.inv(16.0, lat, 16.001, lat)
        _, _, d_lat = WGS84.inv(16.0, lat - 0.0005, 16.0, lat + 0.0005)
        assert lon_m / 1000 == pytest.approx(d_lon, rel=1e-4)
        assert lat_m / 1000 == pytest.approx(d_lat, rel=1e-4)


def test_shares_are_of_land_and_nature_includes_fields() -> None:
    # 40 tree, 20 grass, 20 cropland, 10 built, 10 water, 5 nodata pixels
    values = np.array([10.0] * 40 + [30.0] * 20 + [40.0] * 20 + [50.0] * 10 + [80.0] * 10 + [0] * 5)
    s = landcover_shares(values)
    assert s is not None
    assert s["tree"] == pytest.approx(40 / 90 * 100)
    assert s["nature"] == pytest.approx(80 / 90 * 100)
    assert s["crop"] == pytest.approx(20 / 90 * 100)
    assert s["built"] == pytest.approx(10 / 90 * 100)
    assert s["water"] == pytest.approx(10 / 100 * 100)


def test_a_village_among_fields_is_not_judged_by_the_city_rule() -> None:
    fields = {"tree": 1.0, "nature": 99.0, "built": 0.5}
    village = {"tree": 9.3, "nature": 66.4, "built": 33.5}  # Čaglin, centre
    assert green_status(fields, None) == "good"
    assert green_status(village, None) == "good"
    assert green_points(1.0, 99.0, False, None) == 100
    assert green_points(9.3, 66.4, False, None) == 100


def test_a_built_up_centre_follows_3_30_300() -> None:
    centre = {"tree": 6.6, "nature": 8.6, "built": 91.3}  # Vinkovci, centre
    assert green_status(centre, None) == "bad"
    assert green_status(centre, 120.0) == "warning"
    assert green_status({**centre, "tree": 31.0}, 120.0) == "good"
    assert green_points(6.6, 8.6, True, 120.0) == pytest.approx(6.6 / 30 * 60 + 40)


def _have(lon: float, lat: float) -> bool:
    return _worldcover_path(lon, lat).exists()


needs_data = pytest.mark.skipif(not _have(18.8, 45.3), reason="needs WorldCover tiles (make data)")


@needs_data
@pytest.mark.parametrize(
    ("lon", "lat"),
    [(17.988166, 45.349534), (18.804525, 45.288377), (16.439966, 43.511638)],
)
def test_the_circle_is_metric(lon: float, lat: float) -> None:
    values = landcover_pixels(lon, lat, GREEN_BUFFER_M)
    assert values is not None
    lon_m, lat_m = metres_per_degree(lat)
    area = values.size * (PIXEL_DEG * lon_m) * (PIXEL_DEG * lat_m)
    assert area == pytest.approx(math.pi * GREEN_BUFFER_M**2, rel=0.01)


@needs_data
def test_a_circle_across_a_tile_edge_is_whole() -> None:
    # 18 degrees east is the edge between tiles N45E015 and N45E018.
    edge = landcover_pixels(17.9995, 45.6, GREEN_BUFFER_M)
    assert edge is not None
    assert int((edge == 0).sum()) == 0


@needs_data
@pytest.mark.parametrize(
    ("lon", "lat", "tree", "nature", "built", "urban", "status"),
    [
        # Independent check in EPSG:3035 (tree, nature, built %), within 1.5 points.
        (17.988166, 45.349534, 9.3, 66.4, 33.5, False, "good"),  # Čaglin
        (18.930000, 45.215000, 0.7, 100.0, 0.0, False, "good"),  # field near Nijemci
        (14.750644, 45.358183, 28.7, 65.9, 34.1, False, "good"),  # Lokve, by the forest
        (18.804525, 45.288377, 6.6, 8.6, 91.3, True, "bad"),  # Vinkovci centre, no park
        (16.439966, 43.511638, 11.1, 11.5, 88.5, True, "bad"),  # Split centre, no park
    ],
)
def test_control_locations(
    lon: float,
    lat: float,
    tree: float,
    nature: float,
    built: float,
    urban: bool,
    status: str,
) -> None:
    cat = green_category(lon, lat, None)
    values = {v.key: v.value for v in cat.values}
    assert values["tree_share_300m"] == pytest.approx(tree, abs=1.5)
    assert values["nature_share_300m"] == pytest.approx(nature, abs=1.5)
    assert values["built_share_300m"] == pytest.approx(built, abs=1.5)
    assert values["urban_area"] == (1.0 if urban else 0.0)
    assert cat.status == status
    assert cat.status != "bad" or urban


def test_settlement_values_are_medians_with_quartiles() -> None:
    import pandas as pd

    from ingest.settlement_landcover import summarise

    # Four village houses among fields and one by a forest: the median is the typical house.
    frame = pd.DataFrame(
        {
            "code": ["s"] * 5,
            "real": [True] * 5,
            "tree": [5.0, 6.0, 7.0, 8.0, 90.0],
            "nature": [80.0, 82.0, 84.0, 86.0, 99.0],
            "built": [20.0, 18.0, 16.0, 14.0, 1.0],
            "urban": [0.0] * 5,
            "green": [100.0] * 5,
            "pm25": [10.0, 10.5, 11.0, 11.5, 12.0],
            "no2": [8.0] * 5,
            "air": [50.0] * 5,
        }
    )
    row = summarise(frame).iloc[0]
    assert row["tree_med"] == 7.0  # the mean would be 23.2
    assert (row["tree_p25"], row["tree_p75"]) == (6.0, 8.0)
    assert row["nature_med"] == 84.0
    assert row["urban_share"] == 0.0
    assert row["air_band_med"] == "umjerena"


def test_house_numbers_are_counted_and_named() -> None:
    from analysis.environment import houses_text, share_text
    from app.address_grid import AddressGrid
    from app.geo import to_htrs

    assert [houses_text(n) for n in (1, 3, 11, 14, 21, 22, 25)] == [
        "1 kućni broj",
        "3 kućna broja",
        "11 kućnih brojeva",
        "14 kućnih brojeva",
        "21 kućni broj",
        "22 kućna broja",
        "25 kućnih brojeva",
    ]
    assert share_text(99.7) == "99 %"  # never "100 %" while some land is not nature
    assert share_text(100.0) == "100 %"
    x0, y0 = to_htrs(18.08, 45.38)
    xs = np.array([x0 + 10, x0 - 250, x0 + 299, x0 + 301, x0 + 900])
    ys = np.array([y0, y0, y0, y0, y0 - 900])
    grid = AddressGrid.from_points(xs, ys)
    assert grid.count_within(18.08, 45.38, 300.0) == 3


@needs_data
def test_a_village_card_says_there_are_houses() -> None:
    # Mokreš (Čaglin): houses among meadows and trees, almost no "built-up" pixels.
    cat = green_category(18.082674, 45.377593, None, houses=14)
    assert cat.status == "good"
    assert "oko kuća" in cat.headline
    assert "100 %" not in cat.headline
    values = {v.key: v.display for v in cat.values}
    assert values["houses_300m"] == "14 kućnih brojeva"
