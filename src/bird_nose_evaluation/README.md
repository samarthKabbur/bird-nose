# bird_nose_evaluation

## Purpose

Turns a recorded run into a verdict. It reads scenario files (and finds mistakes in them before a long run), reads a run's MCAP recording, computes metrics, and checks them against the scenario's `checks:`. The same command works by hand and in automation, so "did this change make things better?" has a repeatable answer.

Package type: `ament_python`.

## Contents

| Path | What it is |
| --- | --- |
| `bird_nose_evaluation/scenario.py` | `load_scenario()` (format version 1, every problem reported at once), `find_scenario()`, `world_to_map()`, `route_in_map()` |
| `bird_nose_evaluation/evaluate_run.py` | `read_events()`, `evaluate()`, `write_report()`; executable `evaluate_run` |
| `test/test_scenario.py` | Loader tests, including that every file in `config/scenarios/` is valid |
| `test/test_evaluate.py` | Metric and check tests on made-up events |
| `test/test_read_events.py` | Writes events to a small MCAP file and reads them back |
| `test/test_flake8.py`, `test/test_pep257.py` | ROS's Python style checks |

## Usage

```bash
ros2 run bird_nose_evaluation evaluate_run data/bags/<date>_<time>_scenario-orchard_nav_survey
ros2 run bird_nose_evaluation evaluate_run <recording> --scenario orchard_nav_survey --out /tmp/report
```

`tools/ci/run_scenario.sh` runs a scenario and then this command. The scenario defaults to the one named in the recording's `run_metadata.yaml`. Output, in `data/reports/<recording name>/` unless `--out` is given:

- `report.md`: the result, the stops reached, and a table of checks.
- `metrics.json`: the same, for scripts and comparisons.

Exit status: 0 every evaluated check passed, 1 a check failed, 2 the recording or scenario could not be read.

To check a scenario file without running it:

```bash
python3 -c "from bird_nose_evaluation.scenario import load_scenario as l; l('config/scenarios/orchard_nav_survey.yaml')"
```

## Interfaces

Reads `bird_nose/survey_events` (`bird_nose_interfaces/msg/SurveyEvent`) from recordings. Publishes nothing.

### Metrics and checks

| Metric | Meaning |
| --- | --- |
| `stop_count` | Stops the survey planned (from its `started` event) |
| `expected_stop_count` | Stops the scenario's route and spacing imply, computed independently |
| `stops_reached` | Distinct stops with an `arrived` event |
| `nav_failures`, `failures` | Stops the survey gave up on, with Nav2's status for each attempt |
| `stops_reached_after_retry` | Stops reached only on a second (or later) goal |
| `duration_s` | Simulation time from `started` to `finished` |

Always checked: the survey finished, and it planned the expected number of stops. Checked when the scenario lists them: `stops_reached` (`all` or a number) and `max_nav_failures`. Checks for later steps (`species_found`, `max_location_error_ft`, …) are accepted in scenario files and reported as "not evaluated" until their step adds them; they do not change the result.

## Configuration

Scenario files: see [config/scenarios](../../config/scenarios/README.md) for the format. `BIRD_NOSE_WS` sets where `config/scenarios/` and `data/reports/` are (default `/workspaces/bird-nose`).

## Testing

```bash
colcon test --packages-select bird_nose_evaluation && colcon test-result --verbose
```

Hosted CI runs these tests on every pull request, including the check that every committed scenario file is valid.

## Limitations

- Version 1 judges navigation only. Audio, detection, bearing, and location checks arrive with steps 4.2 to 4.4.
- `stops_reached` trusts Nav2's `SUCCEEDED`; it does not yet compare the robot's true pose with the stop.

## See also

- [config/scenarios](../../config/scenarios/README.md): the scenario format
- [bird_nose_survey](../bird_nose_survey/README.md): produces the events
- [tools/ci](../../tools/ci/README.md): `run_scenario.sh`
