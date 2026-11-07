# bird_nose_bringup

## Purpose

The entry points that start Bird Nose: the simulated Husky A200, Nav2, and RViz. They wrap Clearpath's own launch files so Bird Nose uses the repository's `robot.yaml` and keeps generated files out of Git. Hardware bringup is added in Phase 5.

Package type: `ament_cmake`, launch files only.

## Contents

| File | What it starts |
| --- | --- |
| `launch/sim.launch.py` | Copies `robot.yaml` into a scratch setup folder, then runs `clearpath_gz simulation.launch.py` from it |
| `launch/nav2.launch.py` | Clearpath's Nav2 demo, with SLAM by default, against that setup folder |
| `launch/rviz.launch.py` | Clearpath's navigation RViz view, with the namespace read from `robot.yaml` |

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

Clearpath's Nav2 demos default to a 2D lidar scan, `sensors/lidar2d_0/scan`. Bird Nose has no 2D lidar, so `nav2.launch.py` reads `robot.yaml` from the setup folder and passes the Ouster's scan topic instead. In simulation, Clearpath's Gazebo bridge publishes that topic as `sensor_msgs/LaserScan` alongside the point cloud (`sensors/lidar3d_0/points`). `nav2.launch.py` stops with a clear error if the simulation has not written `robot.yaml` yet.

## Why the setup folder is copied

Clearpath's generators write launch and parameter files next to `robot.yaml`. Mounting the repository copy directly would fill the repository with generated files, so `sim.launch.py` copies `robot.yaml` into `setup_path` first. In Compose, that folder is the shared `bird-nose-sim-setup` volume, so `nav2` and `rviz` read the same files as `sim`.

## Testing

`colcon test --packages-select bird_nose_bringup` runs ROS's style checks (flake8, pep257, xmllint, CMake lint). Behavior is checked by running the simulation; scenario tests arrive in Phase 4.

## Limitations

- `nav2.launch.py` uses Clearpath's demo parameters. Tuned parameters move to `bird_nose_navigation` in Phase 2.
- Whether SLAM and Nav2 accept the simulated Ouster scan as-is is confirmed in the first Phase 2 run. If they do not, the next step is to flatten the point cloud into a 2D scan.

## See also

- [containers](../../containers/README.md): the `sim`, `nav2`, and `rviz` services
- [Clearpath simulator docs](https://docs.clearpathrobotics.com/docs/ros/tutorials/simulator/simulate)
