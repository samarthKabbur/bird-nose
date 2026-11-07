# bird_nose_telemetry

## Purpose

Live dashboards and recordings. Foxglove Bridge makes ROS topics viewable in Foxglove from a browser on any computer, including the MacBook, and MCAP is the recording format for runs worth keeping.

Package type: `ament_cmake`, launch files only.

## Contents

| File | What it starts |
| --- | --- |
| `launch/telemetry.launch.py` | Foxglove Bridge (`foxglove_bridge_launch.xml`) on `127.0.0.1:8765` |

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

The image includes `rosbag2_storage_mcap`. Recordings go in `data/bags/`; see [data](../../data/README.md) for naming and what to note about each run.

## Testing

`colcon test --packages-select bird_nose_telemetry` runs the style checks. Manual check: start the bridge, open the tunnel, and confirm Foxglove lists topics.

## See also

- [Foxglove ROS 2 docs](https://docs.foxglove.dev/docs/getting-started/frameworks/ros2)
- Living doc: "Visualization, telemetry, and data"
