"""Tests for turning routes into survey stops."""
import math

from bird_nose_survey.route import (FEET_TO_M, route_length, stops_along_route,
                                    yaw_to_quaternion)
import pytest


def test_straight_route_stops_every_spacing_and_at_end():
    """A 10 m route with 4 m spacing stops at 4, 8, and 10 m."""
    stops = stops_along_route([(0, 0), (10, 0)], 4.0)
    assert [round(x, 6) for x, _, _ in stops] == [4.0, 8.0, 10.0]
    assert all(y == 0 and yaw == 0 for _, y, yaw in stops)


def test_end_merges_with_a_stop_just_before_it():
    """An 80 ft stop on a 24.4 m route moves to the end rather than adding a fifth."""
    stops = stops_along_route([(0, 0), (24.4, 0)], 20 * FEET_TO_M)
    assert len(stops) == 4
    assert stops[-1][0] == pytest.approx(24.4)


def test_end_not_duplicated_when_spacing_divides_route():
    """Four 20 ft stops on an 80 ft route, not five."""
    length = 80 * FEET_TO_M
    stops = stops_along_route([(0, 0), (length, 0)], 20 * FEET_TO_M)
    assert len(stops) == 4
    assert stops[-1][0] == pytest.approx(length)


def test_stops_follow_corners_and_face_along_route():
    """Distance is measured along the path, and yaw follows each segment."""
    stops = stops_along_route([(0, 0), (3, 0), (3, 4)], 2.0)
    assert [(round(x, 6), round(y, 6)) for x, y, _ in stops] == [
        (2, 0), (3, 1), (3, 3), (3, 4)]
    assert stops[0][2] == pytest.approx(0.0)
    assert stops[1][2] == pytest.approx(math.pi / 2)


def test_route_length_sums_segments():
    """Length is the sum of the segment lengths."""
    assert route_length([(0, 0), (3, 0), (3, 4)]) == pytest.approx(7.0)


@pytest.mark.parametrize('points, spacing', [([(0, 0)], 1.0), ([(0, 0), (1, 0)], 0.0),
                                             ([(1, 1), (1, 1)], 1.0)])
def test_bad_routes_are_rejected(points, spacing):
    """Too few points, zero spacing, or zero length raise ValueError."""
    with pytest.raises(ValueError):
        stops_along_route(points, spacing)


def test_yaw_to_quaternion_quarter_turn():
    """A quarter turn is z = w = sqrt(1/2)."""
    z, w = yaw_to_quaternion(math.pi / 2)
    assert z == pytest.approx(math.sqrt(0.5))
    assert w == pytest.approx(math.sqrt(0.5))
