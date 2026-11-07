# bird_nose_algorithms

## Purpose

Bird Nose's autonomy nodes. For now it holds one heartbeat node that proves the build, launch, parameter, and test pipeline works end to end. Real algorithms replace it in Phase 4, behind stable topic and action interfaces.

Package type: `ament_python`.

## Contents

| Path | What it is |
| --- | --- |
| `bird_nose_algorithms/status_node.py` | `StatusNode`: publishes a heartbeat; executable `status_node` |
| `launch/algorithms.launch.py` | Starts `status_node` as `bird_nose_status` |
| `test/test_status_node.py` | Unit test of the heartbeat text |
| `test/test_flake8.py`, `test/test_pep257.py` | ROS's Python style checks |

## Usage

```bash
ros2 launch bird_nose_algorithms algorithms.launch.py
ros2 topic echo /bird_nose_status/status                  # second terminal
ros2 param describe /bird_nose_status period_s            # self-documenting parameter
ros2 run bird_nose_algorithms status_node --ros-args -p period_s:=0.5
```

## Interfaces

### Node `bird_nose_status`

| Kind | Name | Type | Notes |
| --- | --- | --- | --- |
| Publisher | `~/status` (`/bird_nose_status/status`) | `std_msgs/msg/String` | One message per `period_s`, reliable QoS, depth 10 |
| Parameter | `period_s` | double | Seconds between messages. Default 1.0, range 0.1–60.0, read-only after start-up |
| Parameter | `use_sim_time` | bool | Set by the launch file (default `true`) |

### Launch arguments

| Argument | Default | Meaning |
| --- | --- | --- |
| `use_sim_time` | `true` | Use `/clock` instead of wall time |

## Conventions for new nodes

These keep nodes self-documenting, so `ros2` tools show what this README would otherwise have to explain:

- Declare every parameter with a `ParameterDescriptor`: a description, units in the name (`_s`, `_m`, `_hz`), and a valid range. `status_node.py` shows the pattern.
- Put units and frames in topic and message comments. Custom messages, once added, get a comment on every field (`ros2 interface show` displays them).
- Give every function a docstring; `ament_pep257` enforces this.
- Add each node's interfaces to the table above in the same pull request.

## Testing

```bash
colcon test --packages-select bird_nose_algorithms && colcon test-result --verbose
```

## Limitations

The heartbeat is a placeholder. Bird detection, sound localization, and nest-search behavior arrive in Phase 4.

## See also

- [bird_nose_bringup](../bird_nose_bringup/README.md)
- [ROS 2 parameter descriptors](https://docs.ros.org/en/jazzy/Concepts/Basic/About-Parameters.html)
