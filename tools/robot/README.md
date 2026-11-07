# Robot container scripts

These three scripts start and stop Clearpath's Jazzy robot container on Nuvo and check that joystick teleoperation is ready. They have driven the Husky, and they are committed here **unchanged** from `~/bird_nose_ws/clearpath_docker` on Nuvo so they are preserved.

| Script | What it does |
| --- | --- |
| `start_clearpath_docker.sh` | Starts the `robot` service, waits for `clearpath-platform`, then opens a ROS shell as the `robot` user |
| `stop_clearpath_docker.sh` | Asks you to confirm the physical stop is latched, then stops the container |
| `start_joystick_teleop.sh` | Run inside the container; checks the teleop chain and prints driving instructions |

They expect to sit next to Clearpath's `compose.yaml` and `.env`, so they do not run from this folder yet. Phase 5 wires them into `containers/compose.hardware.yaml`, keeping the Clearpath robot image pinned at the digest the robot already runs:

```text
ghcr.io/clearpathrobotics/clearpath_docker@sha256:d54617757d37b875152839f4a6195887caf49fdefe87237a4919619be57aded0
```

Until then, keep using them from `~/bird_nose_ws/clearpath_docker` on Nuvo.
