"""
Turn a route into survey stops.

A route is a list of (x, y) points in metres. The robot stops every
spacing_m metres measured along the route, and always at the route's end.
Each stop faces along the route at that point, so the robot arrives already
pointing toward the next stop.
"""
import math

FEET_TO_M = 0.3048


def route_length(points):
    """Return the total length of a polyline, in metres."""
    return sum(math.dist(a, b) for a, b in zip(points, points[1:]))


def stops_along_route(points, spacing_m):
    """
    Return the survey stops as a list of (x, y, yaw) tuples.

    Stops fall every spacing_m along the route, plus one at the end unless
    the last regular stop is already within 1 cm of it. The start point is
    not a stop: the robot is already there.
    """
    if len(points) < 2:
        raise ValueError('a route needs at least two points')
    if spacing_m <= 0:
        raise ValueError('stop spacing must be positive')
    segments = [(a, b, math.dist(a, b)) for a, b in zip(points, points[1:])]
    segments = [s for s in segments if s[2] > 0]
    if not segments:
        raise ValueError('the route has zero length')
    total = sum(length for _, _, length in segments)

    distances = []
    d = spacing_m
    while d < total - 0.01:
        distances.append(d)
        d += spacing_m
    distances.append(total)

    stops = []
    for target in distances:
        travelled = 0.0
        for (ax, ay), (bx, by), length in segments:
            if travelled + length >= target - 1e-9:
                f = (target - travelled) / length
                yaw = math.atan2(by - ay, bx - ax)
                stops.append((ax + f * (bx - ax), ay + f * (by - ay), yaw))
                break
            travelled += length
    return stops


def yaw_to_quaternion(yaw):
    """Return (z, w) of the quaternion for a rotation of yaw about +z."""
    return math.sin(yaw / 2.0), math.cos(yaw / 2.0)
