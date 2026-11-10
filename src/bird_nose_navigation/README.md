# bird_nose_navigation

## Purpose

Bird Nose's changes to Clearpath's Nav2 parameters, and the Python helper that merges them. Clearpath's tuned parameters stay the baseline; this package records only what Bird Nose changes, and why.

Package type: `ament_cmake` with a Python module (`ament_cmake_python`).

## Contents

| Path | What it holds |
| --- | --- |
| `config/nav2_overrides.yaml` | Bird Nose's changes, each with its old value and the reason |
| `bird_nose_navigation/nav2_params.py` | `build_params()`: Clearpath's file, plus Clearpath's launch-time changes, plus the overrides |
| `test/test_nav2_params.py` | Unit tests for the merge (no Nav2 needed) |

## Usage

`bird_nose_bringup nav2.launch.py` builds Nav2's parameters on every launch:

1. Clearpath's file for the platform: `clearpath_nav2_demos/config/a200/nav2.yaml` in the installed package.
2. The changes Clearpath's own launch file makes: scan topic, diff-drive motion model, and the global costmap's shape: a 20 m window around the robot with SLAM, the whole map without.
3. `config/nav2_overrides.yaml` from this package, merged on top. Nested keys merge one by one; a list replaces the whole list.

The result is written to `/tmp/bird_nose_nav2_<namespace>.yaml`, and the launch log prints the path. Open it to see exactly what Nav2 received:

```bash
grep -A3 '^bt_navigator' /tmp/bird_nose_nav2_Nuvo_7100VTC_Series.yaml   # inside the container
```

To change a parameter, add it to `nav2_overrides.yaml` under the same node and `ros__parameters` keys as in Clearpath's file, with a comment giving the old value and the reason. A different overrides file can be tried without editing this one: `ros2 launch bird_nose_bringup nav2.launch.py nav2_overrides:=/path/to/file.yaml`.

> **Side note: why overrides instead of a copy.** Copying Clearpath's whole file would freeze their tuning and hide our few changes among hundreds of lines. Keeping only the differences means a reviewer sees exactly what Bird Nose changed, and improvements in Clearpath's file still arrive when the image is rebuilt.

### Current changes

| Parameter | Clearpath | Bird Nose | Why |
| --- | --- | --- | --- |
| `bt_navigator` `default_server_timeout` | 20 ms | 200 ms | Under load the controller took longer than 20 ms to accept its first path, and Jazzy's default behavior tree then aborted the goal without trying a recovery (smoke test on hero, 2026-11-07). |

## Configuration rules

- Start each tuned file from Clearpath's demo file, and record which version it came from.
- Comment every changed value with what changed and why (for example, `# was 0.5; robot oscillated in narrow corridors`).
- Parameters use REP 103 units: metres, seconds, radians.
- Any parameter change that affects motion is tested in simulation, and the recording is noted in the pull request.

## Testing

`colcon test --packages-select bird_nose_navigation` runs the merge tests, which need no Nav2. A parameter change is then checked in simulation with `tools/ci/sim_smoke.sh`, and Phase 4 scenarios compare navigation results between revisions. `record_run` stores the Git commit that last changed `config/` as the Nav2 configuration revision.

## Limitations

- The merge reproduces Clearpath's launch-time changes from their `nav2.launch.py` (Jazzy, November 2026). A parameter Clearpath's launch file names but the installed parameter file lacks is skipped and logged, never created.
- Only Nav2's parameters are changed here. SLAM still uses Clearpath's `slam.yaml` unchanged.

## See also

- [bird_nose_bringup](../bird_nose_bringup/README.md)
- [Nav2 configuration guide](https://docs.nav2.org/configuration/index.html)
