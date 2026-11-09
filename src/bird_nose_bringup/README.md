# bird_nose_bringup

## Purpose

The entry points that start Bird Nose: the simulated Husky A200, Nav2, and RViz. They wrap Clearpath's own launch files so Bird Nose uses the repository's `robot.yaml` and keeps generated files out of Git. Nav2 is the exception: it starts through Nav2's own `navigation_launch.py`, so it can run with Bird Nose's parameters. Hardware bringup is added in Phase 5.

Package type: `ament_cmake`, launch files only.

## Contents

| File | What it starts |
| --- | --- |
| `launch/sim.launch.py` | Copies `robot.yaml` into a scratch setup folder, then runs `clearpath_gz simulation.launch.py` from it |
| `launch/nav2.launch.py` | SLAM (Clearpath's `slam.launch.py`) and Nav2 (Nav2's `navigation_launch.py`) against that setup folder, with Clearpath's Nav2 parameters plus Bird Nose's changes |
| `launch/rviz.launch.py` | Clearpath's navigation RViz view, with the namespace read from `robot.yaml` |
| `launch/scenario.launch.py` | One scenario end to end: simulation, then Nav2 and the survey once the simulation publishes, plus recording; stops when the survey ends |

## Usage

Inside the dev container, after `colcon build --symlink-install`:

```bash
ros2 launch bird_nose_bringup sim.launch.py rviz:=true
ros2 launch bird_nose_bringup nav2.launch.py              # second terminal
ros2 launch bird_nose_bringup sim.launch.py --show-args   # list arguments
```

Or the whole stack with Compose: `docker compose -f containers/compose.yaml --profile sim up`.

### sim.launch.py arguments

| Argument | Default | Meaning |
| --- | --- | --- |
| `robot_yaml` | `$BIRD_NOSE_WS/config/robots/husky-a200/robot.yaml` | Robot to simulate |
| `setup_path` | `$BIRD_NOSE_SIM_SETUP`, else `~/.bird_nose/sim_setup/` | Scratch folder; Clearpath's generators write here |
| `world` | `warehouse` | Gazebo world from `clearpath_gz` |
| `rviz` | `false` | Also open Clearpath's RViz view |
| `headless` | `false` | Run Gazebo without its window |
| `x`, `y` | `0.0` | Spawn position, metres |
| `yaw` | `0.0` | Spawn heading, radians |

### nav2.launch.py arguments

| Argument | Default | Meaning |
| --- | --- | --- |
| `setup_path` | same as above | Must match the folder the simulation used |
| `use_sim_time` | `true` | Use `/clock` from Gazebo |
| `slam` | `true` | Build a map with SLAM (`slam.launch.py`) before starting `nav2.launch.py` |
| `scan_topic` | empty | Scan topic for Nav2 and SLAM. Empty picks one from `robot.yaml`: the Ouster's `/<namespace>/sensors/lidar3d_0/scan` when there is no 2D lidar, as on Bird Nose. |
| `nav2_overrides` | `bird_nose_navigation/config/nav2_overrides.yaml` | Bird Nose's changes to Clearpath's Nav2 parameters; see [bird_nose_navigation](../bird_nose_navigation/README.md) |

### scenario.launch.py arguments

| Argument | Default | Meaning |
| --- | --- | --- |
| `scenario` | `orchard_nav_survey` | Scenario name in `config/scenarios/`, or a file path |
| `seed` | empty | Random seed; empty uses the scenario's own |
| `headless` | `false` | Run Gazebo without its window |
| `rviz` | `false` | Also open Clearpath's RViz view |
| `record` | `true` | Record the run with `record_run` (to `data/bags/<date>_<time>_scenario-<name>/`) |

`scenario.launch.py` uses event handlers rather than fixed delays: Nav2 and the survey start when `wait_for_topics` sees `/clock` and odometry, and the whole launch shuts down when the survey node exits or the scenario's `timeout_s` passes. It refuses to run on ROS domain 0. Run and judge in one step with `tools/ci/run_scenario.sh`.

> **Side note: event handlers instead of sleeps.** A fixed delay ("start Nav2 after 30 s") is too short on a slow computer and wastes time on a fast one. `RegisterEventHandler(OnProcessExit(...))` starts the next part exactly when the previous one reports it is ready, which also makes runs more repeatable.

### rviz.launch.py arguments

| Argument | Default | Meaning |
| --- | --- | --- |
| `robot_yaml` | as for sim | Where the namespace is read from |
| `namespace` | empty | Overrides the namespace from `robot.yaml` |
| `use_sim_time` | `true` | Use `/clock` |

## Interfaces

These launch files add no nodes of their own. The simulated robot publishes Clearpath's standard API under the namespace in `robot.yaml` (`/Nuvo_7100VTC_Series/...`), the same names as the physical robot: for example `platform/cmd_vel`, `platform/odom/filtered`, `tf`, and sensor topics under `sensors/`. Run `ros2 topic list` to see the full set.

## Configuration

- The robot comes from [`config/robots/husky-a200/robot.yaml`](../../config/robots/README.md).
- Every terminal and container must share `ROS_DOMAIN_ID` (42 for simulation) and `RMW_IMPLEMENTATION`; the dev container sets both.

## Why Nav2 is pointed at the Ouster

Clearpath's Nav2 demos default to a 2D lidar scan, `sensors/lidar2d_0/scan`. Bird Nose has no 2D lidar, so `nav2.launch.py` reads `robot.yaml` from the setup folder and passes the Ouster's scan topic instead. In simulation, Clearpath's Gazebo bridge publishes that topic as `sensor_msgs/LaserScan` alongside the point cloud (`sensors/lidar3d_0/points`). It is a single ring, so SLAM accepts it without flattening the point cloud first. `nav2.launch.py` stops with a clear error if the simulation has not written `robot.yaml` yet.

## Why the setup folder is copied

Clearpath's generators write launch and parameter files next to `robot.yaml`. Mounting the repository copy directly would fill the repository with generated files, so `sim.launch.py` copies `robot.yaml` into `setup_path` first. In Compose, that folder is the shared `bird-nose-sim-setup` volume, so `nav2` and `rviz` read the same files as `sim`.

## Testing

`colcon test --packages-select bird_nose_bringup` runs ROS's style checks (flake8, pep257, xmllint, CMake lint). Behavior is checked by running the simulation; scenario tests arrive in Phase 4.

## Limitations

- `nav2.launch.py` reproduces what Clearpath's `nav2.launch.py` does to its parameters (scan topic, drive type, rolling or static global costmap) so it can add Bird Nose's changes. If Clearpath changes that file, compare it with `clearpath_rewrites()` in `bird_nose_navigation`. Composition (all Nav2 nodes in one process) is not offered; Clearpath's launch file has it off by default too.
- The global costmap always covers the whole map, also with SLAM, as in every Phase 2 and 3 run. Clearpath's file would make it a 20 m by 20 m window around the robot when SLAM is on, which leaves goals more than about 10 m away unplannable.
- The simulated Ouster scan works with SLAM and Nav2 as-is: it is one ring of 1024 points from −π to +π at about 11.5 Hz (first Phase 2 run, 2026-11-06). The physical Ouster's driver may publish differently; check in Phase 5.

## See also

- [containers](../../containers/README.md): the `sim`, `nav2`, and `rviz` services
- [Clearpath simulator docs](https://docs.clearpathrobotics.com/docs/ros/tutorials/simulator/simulate)
