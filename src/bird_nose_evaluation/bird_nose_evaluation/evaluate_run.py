"""
Judge a recorded scenario run against its scenario's checks.

    ros2 run bird_nose_evaluation evaluate_run BAG_DIR [--scenario FILE] [--out DIR]

Reads the survey's progress (bird_nose/survey_events) from the run's MCAP
recording, computes metrics, compares them with the scenario's checks, and
writes metrics.json and report.md to $BIRD_NOSE_WS/data/reports/<run>/.

Exit status: 0 every evaluated check passed, 1 a check failed, 2 the input
could not be read. Checks planned for later steps are listed as not
evaluated and do not affect the result.
"""
import argparse
import json
import os
import sys

from bird_nose_evaluation.scenario import (EVALUATED_CHECKS, find_scenario, load_scenario,
                                           PLANNED_CHECKS, route_in_map, ScenarioError)
from bird_nose_survey.route import stops_along_route
import yaml

EVENTS_TOPIC_SUFFIX = '/bird_nose/survey_events'


def read_events(bag_dir):
    """Return the survey events in a recording as a list of dictionaries, in order."""
    # Imported here so the rest of this module works without a ROS installation.
    from rclpy.serialization import deserialize_message
    import rosbag2_py
    from rosidl_runtime_py.utilities import get_message

    reader = rosbag2_py.SequentialReader()
    reader.open(rosbag2_py.StorageOptions(uri=bag_dir, storage_id=''),
                rosbag2_py.ConverterOptions('', ''))
    types = {t.name: t.type for t in reader.get_all_topics_and_types()}
    topics = [name for name in types if name.endswith(EVENTS_TOPIC_SUFFIX)]
    if not topics:
        return []
    reader.set_filter(rosbag2_py.StorageFilter(topics=topics))
    events = []
    while reader.has_next():
        topic, data, _ = reader.read_next()
        msg = deserialize_message(data, get_message(types[topic]))
        events.append({
            'event': msg.event,
            'stop_index': msg.stop_index,
            'stop_count': msg.stop_count,
            'time_s': msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9,
            'target_xy': [msg.target.position.x, msg.target.position.y],
            'detail': msg.detail,
        })
    return events


def evaluate(events, scenario):
    """
    Return (metrics, checks) for a run's survey events.

    Each check is a dictionary with name, expected, actual, and passed
    (True, False, or None for a check this version does not evaluate).
    """
    by_kind = {}
    for e in events:
        by_kind.setdefault(e['event'], []).append(e)
    started = by_kind.get('started', [])
    finished = by_kind.get('finished', [])
    # The survey reports its stop count when it starts, and also when it
    # finishes, including a survey that ended before it could start.
    planned = started or finished
    stop_count = planned[0]['stop_count'] if planned else 0
    survey = scenario['survey']
    expected_stops = len(stops_along_route(route_in_map(scenario), survey['stop_spacing_m']))
    reached = sorted({e['stop_index'] for e in by_kind.get('arrived', [])})
    failures = by_kind.get('failed', [])

    metrics = {
        'survey_started': bool(started),
        'survey_finished': bool(finished),
        'survey_result': finished[-1]['detail'] if finished else 'no finished event',
        'stop_count': stop_count,
        'expected_stop_count': expected_stops,
        'stops_reached': len(reached),
        'nav_failures': len(failures),
        'stops_reached_after_retry': sum(1 for e in by_kind.get('arrived', [])
                                         if e['detail'].startswith('attempts:')),
        'failures': [f"stop {e['stop_index'] + 1}: {e['detail']}" for e in failures],
        'duration_s': (round(finished[-1]['time_s'] - started[0]['time_s'], 1)
                       if started and finished else None),
    }

    checks = [
        {'name': 'survey started', 'expected': True, 'actual': metrics['survey_started'],
         'passed': metrics['survey_started']},
        {'name': 'survey finished', 'expected': True, 'actual': metrics['survey_finished'],
         'passed': metrics['survey_finished']},
        {'name': 'stops planned as the scenario says', 'expected': expected_stops,
         'actual': stop_count, 'passed': stop_count == expected_stops},
    ]
    wanted = scenario['checks']
    if 'stops_reached' in wanted:
        target = stop_count if wanted['stops_reached'] == 'all' else wanted['stops_reached']
        checks.append({'name': 'stops_reached', 'expected': f'>= {target}',
                       'actual': len(reached),
                       'passed': stop_count > 0 and len(reached) >= target})
    if 'max_nav_failures' in wanted:
        checks.append({'name': 'max_nav_failures', 'expected': f"<= {wanted['max_nav_failures']}",
                       'actual': len(failures),
                       'passed': len(failures) <= wanted['max_nav_failures']})
    for name in wanted:
        if name not in EVALUATED_CHECKS:
            checks.append({'name': name, 'expected': wanted[name], 'actual': None,
                           'passed': None, 'note': f'evaluated from step {PLANNED_CHECKS[name]}'})
    return metrics, checks


def overall(checks):
    """Return True when every evaluated check passed."""
    return all(c['passed'] for c in checks if c['passed'] is not None)


def write_report(out_dir, scenario, bag_dir, metrics, checks):
    """Write metrics.json and report.md; return the report's text."""
    os.makedirs(out_dir, exist_ok=True)
    result = 'PASS' if overall(checks) else 'FAIL'
    with open(os.path.join(out_dir, 'metrics.json'), 'w', encoding='utf-8') as f:
        json.dump({'scenario': scenario['name'], 'seed': scenario['seed'], 'recording': bag_dir,
                   'result': result, 'metrics': metrics, 'checks': checks}, f, indent=2)

    def mark(passed):
        return {True: 'pass', False: '**FAIL**', None: 'not evaluated'}[passed]

    lines = [
        f'# Scenario {scenario["name"]}: {result}',
        '',
        f'- Recording: `{bag_dir}`',
        f"- Seed: {scenario['seed']}",
        f"- Stops reached: {metrics['stops_reached']} of {metrics['stop_count']} "
        f"({metrics['stops_reached_after_retry']} needed a second goal)",
        f"- Survey time: {metrics['duration_s']} s (simulation time)",
        f"- Survey's own summary: {metrics['survey_result']}",
        '',
        '| Check | Expected | Actual | Result |',
        '| --- | --- | --- | --- |',
    ]
    for c in checks:
        note = f" ({c['note']})" if c.get('note') else ''
        lines.append(f"| {c['name']} | {c['expected']} | {c['actual']} "
                     f"| {mark(c['passed'])}{note} |")
    if metrics['failures']:
        lines += ['', 'Navigation failures:', ''] + [f'- {f}' for f in metrics['failures']]
    text = '\n'.join(lines) + '\n'
    with open(os.path.join(out_dir, 'report.md'), 'w', encoding='utf-8') as f:
        f.write(text)
    return text


def scenario_from_metadata(bag_dir, workspace):
    """Return the scenario file named in the recording's run_metadata.yaml."""
    path = os.path.join(bag_dir, 'run_metadata.yaml')
    with open(path, encoding='utf-8') as f:
        name = (yaml.safe_load(f) or {}).get('scenario')
    if not name or name == 'none':
        raise ScenarioError(f'{path} names no scenario; pass --scenario')
    return find_scenario(name, workspace)


def main(argv=None):
    """Evaluate one recording and exit with 0 (pass), 1 (fail), or 2 (bad input)."""
    workspace = os.environ.get('BIRD_NOSE_WS', '/workspaces/bird-nose')
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('bag_dir', help='recording folder (contains the .mcap file)')
    parser.add_argument('--scenario', help='scenario name or file; default: from the recording')
    parser.add_argument('--out', help='report folder; default data/reports/<recording name>')
    options = parser.parse_args(argv)

    bag_dir = os.path.abspath(options.bag_dir)
    try:
        path = (find_scenario(options.scenario, workspace) if options.scenario
                else scenario_from_metadata(bag_dir, workspace))
        scenario = load_scenario(path)
        events = read_events(bag_dir)
    except (OSError, ScenarioError, RuntimeError) as error:
        print(f'evaluate_run: {error}', file=sys.stderr)
        sys.exit(2)

    out_dir = options.out or os.path.join(workspace, 'data', 'reports',
                                          os.path.basename(bag_dir.rstrip('/')))
    metrics, checks = evaluate(events, scenario)
    print(write_report(out_dir, scenario, bag_dir, metrics, checks))
    print(f'Report: {out_dir}/report.md')
    sys.exit(0 if overall(checks) else 1)


if __name__ == '__main__':
    main()
