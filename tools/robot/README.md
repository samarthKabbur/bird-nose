# tools/robot

## Purpose

Scripts that start and stop Clearpath's Jazzy robot container on Nuvo and check that joystick teleoperation is ready. They have driven the Husky. They are committed here **unchanged** from `~/bird_nose_ws/clearpath_docker` on Nuvo so they are preserved and reviewable.

## Contents

| Script | Where it runs | What it does |
| --- | --- | --- |
| `start_clearpath_docker.sh` | Nuvo host | Checks Docker and `/etc/clearpath/robot.yaml`, starts the `robot` service, waits up to 120 s for `clearpath-platform`, reminds the operator to keep the physical stop engaged, then opens a ROS shell as `robot` |
| `stop_clearpath_docker.sh` | Nuvo host | Lists the safe-stop steps (sticks centered, LB and RB released, stop latched), requires typing `YES`, then stops the container |
| `start_joystick_teleop.sh` | Inside the robot container, as `robot` | Checks without starting anything: teleop node running, joystick and command topics have publishers, `platform_velocity_controller` and `joint_state_broadcaster` active, a live joystick message, and the stop state. Then prints driving instructions. |

## Usage

These scripts expect to sit next to Clearpath's `compose.yaml` and `.env`, so they do not run from this folder yet. Until Phase 5, use them on Nuvo:

```bash
cd ~/bird_nose_ws/clearpath_docker
./start_clearpath_docker.sh      # opens a shell inside the robot container
./start_joystick_teleop.sh       # inside that shell
exit
./stop_clearpath_docker.sh       # with the physical stop latched
```

Nuvo's setup there also has `compose.override.yaml`, which pins the robot image, and `ROS_AUTOMATIC_DISCOVERY_RANGE=SUBNET` in `.env`. Both were added 2026-11-06.

## Interfaces used

All under the namespace `/Nuvo_7100VTC_Series`:

| Name | Kind | Used for |
| --- | --- | --- |
| `joy_teleop/joy` | topic | Joystick input present |
| `joy_teleop/cmd_vel` | topic | Teleop output present |
| `platform/cmd_vel` | topic | Command into the base |
| `platform/emergency_stop` | topic | Physical stop state (`true` = engaged) |
| `controller_manager/list_controllers` | service | Controllers active |

## Safety

The scripts never command motion themselves. Motion happens only when the operator holds LB (normal) or RB (turbo) on the F710 with the physical stop released. An F710 disconnect may leave the last command active, so a person always stays by the physical stop.

## Limitations

Phase 5 wires these into `containers/compose.hardware.yaml`, keeping the robot image pinned at:

```text
ghcr.io/clearpathrobotics/clearpath_docker@sha256:d54617757d37b875152839f4a6195887caf49fdefe87237a4919619be57aded0
```

## See also

- [config/robots](../../config/robots/README.md)
- Living doc: "Existing Jazzy robot container"
