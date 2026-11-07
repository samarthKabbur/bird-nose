# bird_nose_telemetry

## Purpose

Live dashboards and recordings. Foxglove Bridge makes ROS topics viewable in Foxglove from a browser on any computer, including the MacBook, and MCAP is the recording format for runs worth keeping.

Package type: `ament_cmake`, launch files only.

## Contents

| File | What it starts |
| --- | --- |
| `launch/telemetry.launch.py` | Foxglove Bridge (`foxglove_bridge_launch.xml`) on `127.0.0.1:8765` |
| `scripts/record_run` | Records a run to MCAP and writes `run_metadata.yaml` beside it; installed as `ros2 run bird_nose_telemetry record_run` |

## Usage

```bash
ros2 launch bird_nose_telemetry telemetry.launch.py
```

Or `docker compose -f containers/compose.yaml --profile telemetry up -d`.

From another computer, tunnel through SSH, then connect Foxglove to `ws://localhost:8765`:

```bash
ssh -L 8765:localhost:8765 <user>@<computer running the bridge>
```

| Argument | Default | Meaning |
| --- | --- | --- |
| `address` | `127.0.0.1` | Interface to listen on |
| `port` | `8765` | WebSocket port |

## Why localhost only

The bridge gives full read access to every topic, and it has no password. Listening only on `127.0.0.1` means nothing outside the computer can connect directly. The SSH tunnel adds the authentication and encryption that SSH already provides. Never set `address:=0.0.0.0` on a public or campus network.

## Recording

```bash
ros2 run bird_nose_telemetry record_run first-sim-nav2              # every topic
ros2 run bird_nose_telemetry record_run nav-test /clock /tf /tf_static \
    /Nuvo_7100VTC_Series/platform/odom/filtered                     # chosen topics
SCENARIO=empty-world SEED=7 ros2 run bird_nose_telemetry record_run empty-world-7
```

Stop with Ctrl+C. The script then asks for one line of notes and the outcome, and writes `data/bags/<date>_<time>_<name>/` containing:

| File | Contents |
| --- | --- |
| `*.mcap` | The recording; open it in Foxglove |
| `metadata.yaml` | Topic list and message counts, written by `ros2 bag` |
| `run_metadata.yaml` | Git commit, branch, and whether there were uncommitted changes; base image digest; `robot.yaml` hash; Nav2 configuration revision (`clearpath-defaults` until tuned files exist); ROS domain and middleware; scenario, seed, notes, and outcome |

That is everything the plan asks each retained run to carry, so any recording can be traced back to the exact code and configuration that produced it. `SCENARIO`, `SEED`, and `NOTES` can also be set as environment variables. Recording every topic includes point clouds, which grow by hundreds of MB per minute; name the topics for long runs.

## Testing

`colcon test --packages-select bird_nose_telemetry` runs the style checks. Manual check: start the bridge, open the tunnel, and confirm Foxglove lists topics.

## See also

- [Foxglove ROS 2 docs](https://docs.foxglove.dev/docs/getting-started/frameworks/ros2)
- Living doc: "Visualization, telemetry, and data"
