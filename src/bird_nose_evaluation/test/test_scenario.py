"""Tests for loading and checking scenario files."""
import glob
import math
import os

from bird_nose_evaluation.scenario import (find_scenario, load_scenario, route_in_map,
                                           ScenarioError, world_to_map)
import pytest
import yaml

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
VALID = {
    'format': 1, 'name': 'demo', 'world': 'orchard',
    'robot_start': {'x': 1.0, 'y': 2.0, 'yaw': 0.0}, 'seed': 3,
    'survey': {'waypoints': [[1.0, 2.0], [11.0, 2.0]], 'stop_every_ft': 20, 'record_s': 5},
    'timeout_s': 600, 'checks': {'stops_reached': 'all'},
}


def write(tmp_path, data, name='demo'):
    """Write data as a scenario file and return its path."""
    path = tmp_path / f'{name}.yaml'
    path.write_text(yaml.safe_dump(data))
    return str(path)


def test_valid_scenario_loads_with_derived_fields(tmp_path):
    """A complete file loads, gains stop_spacing_m in metres, and defaults birds."""
    scenario = load_scenario(write(tmp_path, VALID))
    assert scenario['survey']['stop_spacing_m'] == pytest.approx(6.096)
    assert scenario['birds'] == []


def test_every_problem_is_reported_at_once(tmp_path):
    """Several mistakes produce one error naming all of them."""
    bad = dict(VALID, format=2, nmae='x', seed='seven')
    bad['checks'] = {'stops_reachd': 'all'}
    with pytest.raises(ScenarioError) as error:
        load_scenario(write(tmp_path, bad))
    text = str(error.value)
    for fragment in ('format is 2', 'unknown key "nmae"', 'seed must be an integer',
                     'unknown check "stops_reachd"'):
        assert fragment in text


def test_name_must_match_file(tmp_path):
    """The name key and the file name agree."""
    with pytest.raises(ScenarioError, match='must match the file name'):
        load_scenario(write(tmp_path, VALID, name='other'))


def test_route_must_start_at_robot(tmp_path):
    """A route that starts away from the robot is rejected."""
    bad = dict(VALID, survey=dict(VALID['survey'], waypoints=[[5.0, 5.0], [9.0, 5.0]]))
    with pytest.raises(ScenarioError, match='start within 0.5 m'):
        load_scenario(write(tmp_path, bad))


def test_world_to_map_uses_start_pose(tmp_path):
    """The start pose maps to the origin, and yaw rotates the axes."""
    scenario = load_scenario(write(tmp_path, dict(
        VALID, robot_start={'x': 1.0, 'y': 2.0, 'yaw': math.pi / 2},
        survey=dict(VALID['survey'], waypoints=[[1.0, 2.0], [1.0, 12.0]]))))
    assert world_to_map(scenario, 1.0, 2.0) == pytest.approx((0.0, 0.0))
    assert route_in_map(scenario)[1] == pytest.approx((10.0, 0.0))


def test_find_scenario_by_name(tmp_path):
    """A bare name is looked up in config/scenarios/ of the workspace."""
    folder = tmp_path / 'config' / 'scenarios'
    folder.mkdir(parents=True)
    path = write(folder, VALID)
    assert find_scenario('demo', str(tmp_path)) == path
    with pytest.raises(ScenarioError):
        find_scenario('missing', str(tmp_path))


@pytest.mark.parametrize('path', sorted(glob.glob(os.path.join(REPO, 'config', 'scenarios',
                                                               '*.yaml'))))
def test_repository_scenarios_are_valid(path):
    """Every scenario committed to the repository loads without problems."""
    load_scenario(path)
