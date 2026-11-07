# Bird Nose

ROS 2 software for Bird Nose, a Clearpath Husky A200 that identifies birds by sound and localizes them, built by senior design team FH12 at UT Austin.

Everything ROS-related runs in Docker containers: ROS 2 Jazzy, Gazebo Harmonic, Nav2, and Clearpath's Jazzy packages. A computer needs only Docker and Git, so every machine runs the same environment.

The plan, decisions, and lab findings live in the team's living architecture doc; this README covers how to use the repository.

## Quick start (Ubuntu workstation)

Requirements: Docker Engine with the Compose plugin, Git, and a desktop session for Gazebo and RViz windows.

```bash
git clone https://github.com/samarthKabbur/bird-nose.git
cd bird-nose
./tools/dev.sh                      # first run builds the image (several minutes)
```

`./tools/dev.sh` creates `containers/.env` with your user and group IDs, builds the `dev` image, and opens a shell inside the container. In that shell:

```bash
colcon build --symlink-install      # build the workspace (the repo root)
source install/setup.bash
colcon test && colcon test-result --verbose
ros2 launch bird_nose_bringup sim.launch.py rviz:=true
```

With an NVIDIA GPU and the NVIDIA Container Toolkit installed, use `GPU=1 ./tools/dev.sh`. GPU passthrough is optional.

VS Code users can instead run **Dev Containers: Reopen in Container**, which uses the same `dev` service.

## Services

All services share one image and are defined in `containers/compose.yaml`. Run Compose from the repository root:

| Service | Profile | What it runs |
| --- | --- | --- |
| `dev` | (default) | Interactive shell for building and testing |
| `sim` | `sim` | Simulated Husky in Gazebo Harmonic |
| `nav2` | `sim` | Nav2 with SLAM against the simulation |
| `algorithm` | `sim` | Bird Nose autonomy nodes |
| `rviz` | `sim`, `operator` | RViz navigation view |
| `telemetry` | `telemetry`, `operator` | Foxglove Bridge on `localhost:8765` |

```bash
docker compose -f containers/compose.yaml --profile sim up
docker compose -f containers/compose.yaml --profile telemetry up -d
```

To view telemetry from another computer, such as the MacBook, open an SSH tunnel and point Foxglove at `ws://localhost:8765`:

```bash
ssh -L 8765:localhost:8765 <user>@<workstation>
```

## Safety: simulation can never reach the robot

| Setting | Development and simulation | Physical robot |
| --- | --- | --- |
| `ROS_DOMAIN_ID` | 42 | 0 |
| Discovery range | `LOCALHOST` | `SUBNET` |
| Middleware | Fast DDS | Fast DDS |

Everything in `containers/compose.yaml` uses the left column. The robot is started only through the hardware overlay (`containers/compose.hardware.yaml`), which stays empty until Phase 5. Commands that can drive the robot are added only after the hardware safety controls are documented.

## Repository layout

```text
bird-nose/
├── .devcontainer/          VS Code dev container (uses the dev service)
├── containers/             Dockerfile, Compose file, overlays, .env.example
├── config/
│   ├── hosts/              per-role settings (workstation, Nuvo, bender)
│   ├── robots/husky-a200/  Clearpath robot.yaml for the A200
│   └── scenarios/          simulation scenario definitions
├── src/                    ROS 2 packages (bird_nose_*)
├── tools/
│   ├── dev.sh              one-command development environment
│   └── robot/              robot container scripts (wired up in Phase 5)
├── data/                   bags, logs, reports (contents never committed)
└── dependencies.repos      extra source repositories for vcs import
```

| Package | Purpose |
| --- | --- |
| `bird_nose_bringup` | Launch entry points: simulation, Nav2, RViz |
| `bird_nose_description` | Bird Nose payloads (microphone modules, crossbar) |
| `bird_nose_navigation` | Nav2 parameters, maps, behavior trees |
| `bird_nose_sim` | Gazebo worlds and scenario assets |
| `bird_nose_algorithms` | Bird Nose autonomy nodes |
| `bird_nose_telemetry` | Foxglove Bridge and MCAP recording |

## Robot configuration

`config/robots/husky-a200/robot.yaml` describes the robot and its sensors in Clearpath's format. It is Nuvo's working file with corrections, and each change is marked `CHANGED` inline. Simulation reads it directly. For the physical robot it is copied to `/etc/clearpath/robot.yaml` on Nuvo rather than mounted, because Clearpath's generators write files next to it.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md). In short: branch from `main`, open a pull request, and never commit machine-local addresses, passwords, or recordings.
