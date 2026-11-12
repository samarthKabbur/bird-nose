# bird_nose_survey

## Purpose

The survey behaviour from the project memo: drive a route, stop every 20 ft, stay at each stop to record, and report progress. Navigation itself is Nav2's job; this package decides where to go and when to stop.

Package type: `ament_python`.

## Contents

| Path | What it is |
| --- | --- |
| `bird_nose_survey/route.py` | `stops_along_route()`: turns a route into stops every N metres along it, each facing along the route; no ROS needed |
| `bird_nose_survey/survey_node.py` | The `survey` node: sends one Nav2 goal per stop and publishes `SurveyEvent`s; executable `survey` |
| `bird_nose_survey/wait_for_topics.py` | Exits once messages arrive on given topics; executable `wait_for_topics`, used by `scenario.launch.py` |
| `test/test_route.py` | Unit tests for stop placement |
| `test/test_flake8.py`, `test/test_pep257.py` | ROS's Python style checks |

## Usage

Normally started by `bird_nose_bringup scenario.launch.py`, which converts the scenario's route to the map frame. By hand, with the simulation and Nav2 already running:

```bash
ros2 run bird_nose_survey survey --ros-args -r __ns:=/Nuvo_7100VTC_Series \
  -p use_sim_time:=true -p route_xy:="[0.0, 0.0, 12.0, 0.0]" -p dwell_s:=5.0
ros2 topic echo /Nuvo_7100VTC_Series/bird_nose/survey_events      # second terminal
ros2 run bird_nose_survey wait_for_topics --timeout 60 /clock      # exits 0 once /clock publishes
```

What the node does:

1. Waits until Nav2's `bt_navigator` reports the active state and SLAM has published a map (`nav2_timeout_s`). Nav2 can be active a moment before its costmaps have any map, and a goal sent then fails.
2. Computes the stops: every `stop_spacing_m` along `route_xy`, plus the route's end. The first route point is where the robot starts, so it is not a stop.
3. For each stop, sends a `NavigateToPose` goal facing along the route, up to `max_attempts` times. If Nav2 reports `SUCCEEDED`, publishes `arrived` (its detail lists earlier attempts, if any), waits `dwell_s` (simulation time), then publishes `recorded`. Otherwise publishes `failed` with Nav2's status for each attempt (`TIMEOUT` after `goal_timeout_s`) and moves on to the next stop.
4. Publishes `finished` and exits.

> **Side note: why one goal per stop.** Nav2 also has a "navigate through poses" action, but it does not stop at the poses. Separate goals give the survey a clear arrival at each stop, a place to record, and a per-stop success or failure that the evaluator can count.

## Interfaces

### Node `survey` (in the robot namespace)

| Kind | Name | Type | Notes |
| --- | --- | --- | --- |
| Publisher | `bird_nose/survey_events` | `bird_nose_interfaces/msg/SurveyEvent` | Reliable, transient local, depth 100, so a late subscriber or recorder still gets every event |
| Action client | `navigate_to_pose` | `nav2_msgs/action/NavigateToPose` | Nav2's goal interface |
| Service client | `bt_navigator/get_state` | `lifecycle_msgs/srv/GetState` | Checks that Nav2 is active before starting |
| Subscriber | `map` | `nav_msgs/msg/OccupancyGrid` | Only to know SLAM has produced a map; transient local |
| Parameter | `route_xy` | double array | Route in the map frame as `[x0, y0, x1, y1, ...]`, metres. Required |
| Parameter | `stop_spacing_m` | double | Distance between stops along the route. Default 6.096 (20 ft), range 0.5–100 |
| Parameter | `dwell_s` | double | Time at each stop reached, simulation seconds. Default 30, range 0–600 |
| Parameter | `goal_timeout_s` | double | Wall-clock seconds allowed per stop. Default 180, range 10–1800 |
| Parameter | `max_attempts` | integer | Goals sent to one stop before it counts as failed. Default 2 (one retry), range 1–5 |
| Parameter | `nav2_timeout_s` | double | Wall-clock seconds to wait for Nav2. Default 300, range 10–1800 |
| Parameter | `use_sim_time` | bool | Set to `true` by the launch file |

All parameters are read-only after start-up. `ros2 param describe /Nuvo_7100VTC_Series/survey <name>` shows the same descriptions.

### Executable `wait_for_topics`

`wait_for_topics [--timeout S] TOPIC [TOPIC ...]` exits with status 0 once at least one message has arrived on every topic, or 1 after the timeout (default 300 s). It subscribes with best-effort QoS, which matches both reliable and best-effort publishers.

## Configuration

Nothing beyond the parameters above. Routes come from scenario files in `config/scenarios/` (simulation) and, in Phase 5, from field routes.

## Testing

```bash
colcon test --packages-select bird_nose_survey && colcon test-result --verbose
```

The node itself is tested end to end by `tools/ci/run_scenario.sh`.

## Limitations

- At each stop the robot only waits; recording replaces the wait in step 4.2 (`RecordSample`).
- A stop Nav2 still cannot reach after `max_attempts` goals is skipped; the survey does not come back to it.
- The node trusts the route: it does not check it against the map. Scenario files are checked by `bird_nose_evaluation` before a run.

## See also

- [bird_nose_interfaces](../bird_nose_interfaces/README.md): `SurveyEvent`
- [bird_nose_bringup](../bird_nose_bringup/README.md): `scenario.launch.py`
- [bird_nose_evaluation](../bird_nose_evaluation/README.md): judges the events
