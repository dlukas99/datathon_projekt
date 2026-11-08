"""Which roads count as major traffic, and the settlement value over its addresses."""

import numpy as np
import pytest

from analysis.environment import is_traffic_road
from ingest import settlement_traffic


def test_county_roads_do_not_count_but_city_main_streets_do() -> None:
    assert is_traffic_road("motorway", "A3")
    assert is_traffic_road("trunk", "D1")
    assert is_traffic_road("primary", "D2")
    assert is_traffic_road("primary", "")
    assert is_traffic_road("secondary", "")  # former county road, now a main city street
    assert not is_traffic_road("secondary", "4290")  # county road Ž4290
    assert not is_traffic_road("secondary", "2001;2002")
    assert not is_traffic_road("tertiary", "")


def test_bands_follow_the_report_thresholds() -> None:
    assert settlement_traffic.NEAR_M == 300.0
    assert settlement_traffic.EDGE_M == 500.0


@pytest.mark.skipif(
    not (settlement_traffic.processed_dir() / "osm_noise_lines.parquet").exists(),
    reason="needs processed OSM roads (make data)",
)
def test_a_point_on_a_motorway_is_near_and_one_at_sea_is_far() -> None:
    # A3 near Zagreb (Jankomir interchange) and the open Adriatic.
    dist = settlement_traffic.address_distances(
        np.array([15.8817, 15.0]), np.array([45.7961, 43.5])
    )
    assert dist[0] <= settlement_traffic.NEAR_M
    assert dist[1] > settlement_traffic.EDGE_M
