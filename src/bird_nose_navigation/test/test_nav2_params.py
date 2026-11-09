"""Tests for building Bird Nose's Nav2 parameters."""
import os

from bird_nose_navigation.nav2_params import (
    build_params, deep_merge, load_yaml, set_existing, write_params)
import pytest

PKG = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OVERRIDES = os.path.join(PKG, 'config', 'nav2_overrides.yaml')
SCAN = '/ns/sensors/lidar3d_0/scan'


@pytest.fixture
def clearpath():
    """Return a small parameter file shaped like Clearpath's a200 nav2.yaml."""
    return {
        'bt_navigator': {'ros__parameters': {
            'default_server_timeout': 20, 'wait_for_service_timeout': 1000}},
        'controller_server': {'ros__parameters': {
            'controller_frequency': 20.0,
            'FollowPath': {'motion_model': 'Omni', 'TwirlingCritic': {'enabled': True}}}},
        'local_costmap': {'local_costmap': {'ros__parameters': {
            'voxel_layer': {'scan': {'topic': '/x/sensors/lidar2d_0/scan'}}}}},
        'global_costmap': {'global_costmap': {'ros__parameters': {
            'rolling_window': True,
            'obstacle_layer': {'scan': {'topic': '/x/sensors/lidar2d_0/scan'}}}}},
        'collision_monitor': {'ros__parameters': {'scan': {'topic': '/x/sensors/lidar2d_0/scan'}}},
    }


def test_overrides_file_raises_server_timeout():
    """The committed overrides change the 20 ms acknowledgement timeout."""
    timeout = load_yaml(OVERRIDES)['bt_navigator']['ros__parameters']['default_server_timeout']
    assert timeout > 20


def test_build_applies_clearpath_rewrites_then_overrides(clearpath):
    """Scan topics, drive type, and overrides all land; other values stay."""
    params, skipped = build_params(clearpath, load_yaml(OVERRIDES), SCAN, diff_drive=True,
                                   rolling_global_costmap=True)
    assert skipped == []
    bt = params['bt_navigator']['ros__parameters']
    assert bt['default_server_timeout'] == 200
    assert bt['wait_for_service_timeout'] == 1000
    follow = params['controller_server']['ros__parameters']['FollowPath']
    assert follow['motion_model'] == 'DiffDrive'
    assert follow['TwirlingCritic']['enabled'] is False
    assert params['collision_monitor']['ros__parameters']['scan']['topic'] == SCAN
    assert params['global_costmap']['global_costmap']['ros__parameters']['rolling_window']


def test_default_global_costmap_covers_whole_map(clearpath):
    """By default the global costmap is not a rolling window."""
    params, _ = build_params(clearpath, {}, SCAN)
    assert params['global_costmap']['global_costmap']['ros__parameters']['rolling_window'] is False


def test_missing_clearpath_keys_are_skipped_not_created(clearpath):
    """A parameter file without a rewritten key is reported, not changed."""
    del clearpath['collision_monitor']
    params, skipped = build_params(clearpath, {}, SCAN)
    assert 'collision_monitor' not in params
    assert skipped == ['collision_monitor.ros__parameters.scan.topic']


def test_build_does_not_modify_inputs(clearpath):
    """The caller's dictionaries are left as they were."""
    overrides = {'bt_navigator': {'ros__parameters': {'default_server_timeout': 200}}}
    build_params(clearpath, overrides, SCAN)
    assert clearpath['bt_navigator']['ros__parameters']['default_server_timeout'] == 20


def test_deep_merge_replaces_lists():
    """Lists are replaced whole, never appended to."""
    merged = deep_merge({'a': {'plugins': ['x', 'y'], 'k': 1}}, {'a': {'plugins': ['z']}})
    assert merged == {'a': {'plugins': ['z'], 'k': 1}}


def test_set_existing_reports_missing_parents():
    """A missing intermediate key returns False."""
    assert set_existing({'a': {}}, 'a.b.c', 1) is False


def test_write_params_round_trips(tmp_path, monkeypatch):
    """The written file loads back to the same parameters."""
    monkeypatch.setattr('tempfile.tempdir', str(tmp_path))
    params = {'bt_navigator': {'ros__parameters': {'default_server_timeout': 200}}}
    path = write_params(params, 'ns')
    assert os.path.basename(path) == 'bird_nose_nav2_ns.yaml'
    assert load_yaml(path) == params
