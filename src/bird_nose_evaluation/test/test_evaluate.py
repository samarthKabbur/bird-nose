"""Tests for judging a run's survey events against a scenario."""
from bird_nose_evaluation.evaluate_run import evaluate, overall, write_report
import pytest

SCENARIO = {
    'name': 'demo', 'seed': 1,
    'robot_start': {'x': 0.0, 'y': 0.0, 'yaw': 0.0},
    'survey': {'waypoints': [[0.0, 0.0], [12.0, 0.0]], 'stop_spacing_m': 6.0, 'record_s': 1},
    'checks': {'stops_reached': 'all', 'max_nav_failures': 0, 'species_found': ['x']},
}


def event(kind, index=0, count=2, time_s=0.0, detail=''):
    """Return one survey event as read from a recording."""
    return {'event': kind, 'stop_index': index, 'stop_count': count, 'time_s': time_s,
            'target_xy': [0.0, 0.0], 'detail': detail}


def test_complete_survey_passes():
    """Both stops reached, no failures: every evaluated check passes."""
    events = [event('started'), event('arrived', 0, time_s=10), event('recorded', 0),
              event('arrived', 1, time_s=20), event('recorded', 1),
              event('finished', time_s=30)]
    metrics, checks = evaluate(events, SCENARIO)
    assert metrics['stops_reached'] == 2
    assert metrics['duration_s'] == pytest.approx(30.0)
    assert overall(checks)
    planned = [c for c in checks if c['name'] == 'species_found'][0]
    assert planned['passed'] is None


def test_failed_stop_fails_both_checks():
    """A stop Nav2 could not reach fails stops_reached and max_nav_failures."""
    events = [event('started'), event('arrived', 0), event('failed', 1, detail='ABORTED'),
              event('finished')]
    metrics, checks = evaluate(events, SCENARIO)
    assert metrics['failures'] == ['stop 2: ABORTED']
    failed = {c['name'] for c in checks if c['passed'] is False}
    assert failed == {'stops_reached', 'max_nav_failures'}
    assert not overall(checks)


def test_unfinished_survey_fails():
    """A run that never reports finished fails, even with stops reached."""
    events = [event('started'), event('arrived', 0), event('arrived', 1)]
    _, checks = evaluate(events, SCENARIO)
    assert not overall(checks)


def test_wrong_stop_count_fails():
    """The survey must plan the stops the scenario implies."""
    events = [event('started', count=3), event('finished', count=3)]
    _, checks = evaluate(events, SCENARIO)
    assert [c['passed'] for c in checks if c['name'].startswith('stops planned')] == [False]


def test_report_files_are_written(tmp_path):
    """write_report produces report.md and metrics.json."""
    metrics, checks = evaluate([event('started'), event('finished')], SCENARIO)
    text = write_report(str(tmp_path), SCENARIO, '/bags/run', metrics, checks)
    assert text.startswith('# Scenario demo: FAIL')
    assert (tmp_path / 'metrics.json').is_file()
    assert (tmp_path / 'report.md').read_text() == text
