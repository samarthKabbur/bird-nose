"""
Load and check scenario files (format version 1).

A scenario is one YAML file in config/scenarios/ that describes a simulated
run completely: world, start pose, seed, survey route, simulated birds, time
limit, and the checks that decide pass or fail. load_scenario() reports
every problem in a file at once, so a typo is found before a long run.

Coordinates in a scenario are in the Gazebo world frame, in metres. SLAM
puts the map frame's origin where the robot starts, so world_to_map()
converts using robot_start.
"""
import math
import os

import yaml

FORMAT = 1
FEET_TO_M = 0.3048

REQUIRED_KEYS = ('format', 'name', 'world', 'robot_start', 'seed', 'survey', 'timeout_s',
                 'checks')
OPTIONAL_KEYS = ('description', 'birds', 'noise')

# Checks this version of evaluate_run can judge, and the ones planned for
# later steps (accepted in files, reported as not evaluated yet).
EVALUATED_CHECKS = ('stops_reached', 'max_nav_failures')
PLANNED_CHECKS = {
    'species_found': '4.3', 'min_confidence': '4.3', 'max_analysis_s': '4.3',
    'max_bearing_error_deg': '4.4', 'max_location_error_ft': '4.4',
}


class ScenarioError(ValueError):
    """A scenario file is missing something or has a wrong value."""


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _check(data, stem):
    """Return a list of problems with a loaded scenario."""
    problems = []
    if not isinstance(data, dict):
        return ['the file must be a YAML mapping (key: value pairs)']
    for key in REQUIRED_KEYS:
        if key not in data:
            problems.append(f'missing required key "{key}"')
    for key in data:
        if key not in REQUIRED_KEYS + OPTIONAL_KEYS:
            problems.append(f'unknown key "{key}" (typo?)')
    if 'format' in data and data['format'] != FORMAT:
        problems.append(f'format is {data["format"]!r}; this version reads format {FORMAT}')
    if 'name' in data and data['name'] != stem:
        problems.append(f'name "{data["name"]}" must match the file name "{stem}"')
    if 'world' in data and not (isinstance(data['world'], str) and data['world']):
        problems.append('world must be a Gazebo world name, such as orchard')
    seed = data.get('seed')
    if 'seed' in data and (not isinstance(seed, int) or isinstance(seed, bool)):
        problems.append('seed must be an integer')
    if 'timeout_s' in data and not (_is_number(data['timeout_s']) and data['timeout_s'] > 0):
        problems.append('timeout_s must be a positive number of seconds')

    start = data.get('robot_start')
    if 'robot_start' in data:
        if not (isinstance(start, dict) and _is_number(start.get('x'))
                and _is_number(start.get('y')) and _is_number(start.get('yaw', 0.0))):
            problems.append('robot_start must have numbers x, y, and optionally yaw (radians)')
            start = None

    survey = data.get('survey')
    if 'survey' in data:
        if not isinstance(survey, dict):
            problems.append('survey must be a mapping with waypoints, stop_every_ft, record_s')
        else:
            points = survey.get('waypoints')
            if not (isinstance(points, list) and len(points) >= 2 and all(
                    isinstance(p, list) and len(p) == 2 and all(map(_is_number, p))
                    for p in points)):
                problems.append('survey.waypoints must be a list of at least two [x, y] pairs')
            elif start and math.dist(points[0], (start['x'], start['y'])) > 0.5:
                problems.append('survey.waypoints must start within 0.5 m of robot_start')
            if not (_is_number(survey.get('stop_every_ft')) and survey['stop_every_ft'] > 0):
                problems.append('survey.stop_every_ft must be a positive number of feet')
            if not (_is_number(survey.get('record_s')) and survey['record_s'] >= 0):
                problems.append('survey.record_s must be a number of seconds, 0 or more')
            for key in survey:
                if key not in ('waypoints', 'stop_every_ft', 'record_s'):
                    problems.append(f'unknown key "survey.{key}" (typo?)')

    birds = data.get('birds', [])
    if not isinstance(birds, list) or not all(
            isinstance(b, dict) and isinstance(b.get('species'), str)
            and _is_number(b.get('x')) and _is_number(b.get('y')) for b in birds):
        problems.append('birds must be a list, each with species, x, and y')

    checks = data.get('checks')
    if 'checks' in data:
        if not isinstance(checks, dict):
            problems.append('checks must be a mapping')
        else:
            for key, value in checks.items():
                if key not in EVALUATED_CHECKS and key not in PLANNED_CHECKS:
                    problems.append(f'unknown check "{key}"')
            reached = checks.get('stops_reached')
            if 'stops_reached' in checks and not (
                    reached == 'all' or (isinstance(reached, int) and reached >= 0)):
                problems.append('checks.stops_reached must be "all" or a whole number')
            failures = checks.get('max_nav_failures')
            if 'max_nav_failures' in checks and not (isinstance(failures, int)
                                                     and failures >= 0):
                problems.append('checks.max_nav_failures must be a whole number')
    return problems


def load_scenario(path):
    """
    Load a scenario file and return it as a dictionary.

    Raises ScenarioError listing every problem found. The result has two
    added keys: path (the file) and survey.stop_spacing_m (metres).
    """
    with open(path, encoding='utf-8') as f:
        data = yaml.safe_load(f)
    stem = os.path.splitext(os.path.basename(path))[0]
    problems = _check(data, stem)
    if problems:
        raise ScenarioError(f'{path}:\n  - ' + '\n  - '.join(problems))
    data['robot_start'].setdefault('yaw', 0.0)
    data.setdefault('birds', [])
    data['path'] = os.path.abspath(path)
    data['survey']['stop_spacing_m'] = data['survey']['stop_every_ft'] * FEET_TO_M
    return data


def find_scenario(name_or_path, workspace):
    """Return the file for a scenario given as a path or as a name in config/scenarios/."""
    if os.path.isfile(name_or_path):
        return os.path.abspath(name_or_path)
    path = os.path.join(workspace, 'config', 'scenarios', f'{name_or_path}.yaml')
    if not os.path.isfile(path):
        raise ScenarioError(f'no scenario file {name_or_path!r} (looked for {path})')
    return path


def world_to_map(scenario, x, y):
    """Convert a world point to the map frame, whose origin is the robot's start pose."""
    start = scenario['robot_start']
    dx, dy = x - start['x'], y - start['y']
    c, s = math.cos(-start['yaw']), math.sin(-start['yaw'])
    return c * dx - s * dy, s * dx + c * dy


def route_in_map(scenario):
    """Return the survey waypoints converted to the map frame."""
    return [world_to_map(scenario, x, y) for x, y in scenario['survey']['waypoints']]
