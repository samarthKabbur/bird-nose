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

## Foxglove's 3D panel

The 3D panel needs WebGL, the browser's GPU access. If it shows "Error creating WebGL context", turn on hardware acceleration in the browser (Chrome: Settings → System → **Use graphics acceleration when available**, then relaunch); `https://get.webgl.org` confirms it works. Other panels, such as Raw Messages and Plot, work without it.

## Why localhost only

The bridge gives full read access to every topic, and it has no password. Listening only on `127.0.0.1` means nothing outside the computer can connect directly. The SSH tunnel adds the authentication and encryption that SSH already provides. Never set `address:=0.0.0.0` on a public or campus network.

## Recording

```bash
ros2 run bird_nose_telemetry record_run first-sim-nav2              # all but point clouds and images
FULL=1 ros2 run bird_nose_telemetry record_run with-points          # everything
ros2 run bird_nose_telemetry record_run nav-test /clock /tf /tf_static \
    /Nuvo_7100VTC_Series/platform/odom/filtered                     # chosen topics
SCENARIO=empty-world SEED=7 ros2 run bird_nose_telemetry record_run empty-world-7
```

Stop with Ctrl+C. The script then asks for one line of notes and the outcome, and writes `data/bags/<date>_<time>_<name>/` containing:

| File | Contents |
| --- | --- |
| `*.mcap` | The recording; open it in Foxglove |
| `metadata.yaml` | Topic list and message counts, written by `ros2 bag` |
| `run_metadata.yaml` | Git commit, branch, and whether there were uncommitted changes; base image digest; `robot.yaml` hash; Nav2 configuration revision (the commit that last changed `bird_nose_navigation/config/`, or `clearpath-defaults` if that folder is empty); ROS domain and middleware; scenario, seed, notes, and outcome |

That is everything the plan asks each retained run to carry, so any recording can be traced back to the exact code and configuration that produced it. `SCENARIO`, `SEED`, and `NOTES` can also be set as environment variables.

By default, point clouds (`sensor_msgs/msg/PointCloud2`) and camera images are left out. The first full simulation run recorded 3.4 GB in about a minute, almost all of it Ouster point clouds. The 2D scan that SLAM and Nav2 use is still recorded. Use `FULL=1` when the point cloud itself is under study.

## Testing

`colcon test --packages-select bird_nose_telemetry` runs the style checks. Manual check: start the bridge, open the tunnel, and confirm Foxglove lists topics.

## See also

- [Foxglove ROS 2 docs](https://docs.foxglove.dev/docs/getting-started/frameworks/ros2)
- Living doc: "Visualization, telemetry, and data"
