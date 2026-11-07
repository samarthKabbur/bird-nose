# containers

## Purpose

Defines the one Docker image and the Compose services that run Bird Nose on a workstation. Everything ROS-related (ROS 2 Jazzy, Gazebo Harmonic, Nav2, RViz, Clearpath's Jazzy packages) lives inside the image, so a computer needs only Docker and Git.

## Contents

| File | What it is |
| --- | --- |
| `Dockerfile` | Two-stage image. `base` adds ROS packages to `ros:jazzy-ros-base-noble`, pinned by digest. `dev` adds build and lint tools and a non-root user matching your host user ID. |
| `entrypoint.sh` | Sources ROS and, once built, the workspace (`install/setup.bash`), then runs the command. Also sourced by the dev user's `~/.bashrc`. |
| `compose.yaml` | The services below, all sharing the `bird-nose-dev:jazzy` image |
| `compose.nvidia.yaml` | Optional overlay that passes an NVIDIA GPU into `dev`, `sim`, and `rviz` |
| `compose.hardware.yaml` | Physical robot overlay. Deliberately empty until Phase 5. |
| `.env.example` | Template for `containers/.env`, which holds machine-local settings and is ignored by Git |

## Usage

The easy path is `./tools/dev.sh` from the repository root (see [tools](../tools/README.md)). Manually, always from the repository root:

```bash
docker compose -f containers/compose.yaml up -d dev          # start the dev container
docker compose -f containers/compose.yaml exec dev bash      # open a shell in it
docker compose -f containers/compose.yaml --profile sim up   # simulation stack
docker compose -f containers/compose.yaml --profile telemetry up -d
docker compose -f containers/compose.yaml -f containers/compose.nvidia.yaml up -d dev  # with GPU
docker compose -f containers/compose.yaml down               # stop everything
```

`ros2` commands in the `sim`, `nav2`, `algorithm`, `rviz`, and `telemetry` services need the workspace built first: run `colcon build --symlink-install` in the `dev` shell.

## Services

| Service | Profiles | Command | Notes |
| --- | --- | --- | --- |
| `dev` | default | `sleep infinity` | Interactive shell; the only service built by `tools/dev.sh` |
| `sim` | `sim` | `ros2 launch bird_nose_bringup sim.launch.py` | Gazebo window needs a display |
| `nav2` | `sim` | `ros2 launch bird_nose_bringup nav2.launch.py` | Waits for `sim` to be healthy; reads the shared setup folder |
| `algorithm` | `sim` | `ros2 launch bird_nose_algorithms algorithms.launch.py` | Waits for `sim` to be healthy; heartbeat node for now |
| `rviz` | `sim`, `operator` | `ros2 launch bird_nose_bringup rviz.launch.py` | Needs a display; waits for `sim` when started together |
| `telemetry` | `telemetry`, `operator` | `ros2 launch bird_nose_telemetry telemetry.launch.py` | Foxglove Bridge on `127.0.0.1:8765` |

`sim` reports healthy once Gazebo's `/clock` is ticking and the robot's `platform/odom/filtered` topic exists, which is the same check Clearpath's own simulation image uses. It allows 120 s for start-up, then checks every 10 s. `docker compose -f containers/compose.yaml ps` shows each service's health.

Shared by every service:

- Host networking and host IPC, so ROS discovery and shared-memory transport work like on a normal Ubuntu install.
- The repository mounted at `/workspaces/bird-nose`; the colcon workspace is the repository root.
- Volume `bird-nose-history`: shell history that survives container restarts.
- Volume `bird-nose-sim-setup`, mounted at `~/.bird_nose`: Clearpath's generated simulation files, shared by `sim`, `nav2`, and `rviz`.
- The X11 socket, for Gazebo and RViz windows.
- GPU access through Mesa (Intel or AMD graphics): `/dev/dri` is mounted, a cgroup rule allows DRM devices (major number 226), and the container user joins the host's `video` and `render` groups. Without this, Mesa reports "Failed to query drm device" and RViz may fail to start. NVIDIA graphics use `compose.nvidia.yaml` instead.

## Configuration

`containers/.env` is created on first run by `tools/setup_env.sh` from `.env.example`:

| Variable | Default | Meaning |
| --- | --- | --- |
| `HOST_UID`, `HOST_GID` | your IDs | The container user gets these, so files it creates stay yours. Changing them requires rebuilding the image. |
| `CONTAINER_USER` | `dev` | User name inside the container |
| `ROS_DOMAIN_ID` | `42` | Development and simulation domain. The robot uses `0`; keep them different. |
| `RMW_IMPLEMENTATION` | `rmw_fastrtps_cpp` | Fast DDS, the same middleware as the robot |
| `ROS_AUTOMATIC_DISCOVERY_RANGE` | `LOCALHOST` | Keeps simulation traffic on this computer |
| `DISPLAY` | `:0` | X display for GUI windows |
| `VIDEO_GID`, `RENDER_GID` | your machine's | Host group IDs that own `/dev/dri`; they differ between installs, so `setup_env.sh` looks them up |

`tools/setup_env.sh` never changes values in an existing `.env`, but it adds any setting that `.env.example` gained since, so every machine picks up new settings by running `./tools/dev.sh`.

To change the base image, update the digest in `Dockerfile` in its own pull request and note why.

## Testing

`docker compose -f containers/compose.yaml --profile sim --profile telemetry config --quiet` checks the Compose file. A successful `./tools/dev.sh` followed by `colcon build && colcon test` in the container checks the image.

## Limitations

- GUI forwarding assumes X11 or XWayland on an Ubuntu desktop. macOS and Windows hosts are not supported for running ROS.
- The first image build downloads several GB.

## See also

- [tools](../tools/README.md): `dev.sh` and `setup_env.sh`
- [docs/architecture.md](../docs/architecture.md): how containers map to computers
- Living doc: "Containers" and "Safety and deployment boundaries"
