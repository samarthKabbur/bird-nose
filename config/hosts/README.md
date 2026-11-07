# config/hosts

## Purpose

Versioned, non-secret settings for each kind of computer, so a computer's job comes from configuration rather than from a Git branch. Machine-local values (addresses, passwords) never go here; they belong in that machine's untracked `containers/.env`.

## Contents

| File | Computer | ROS domain | Discovery | Role |
| --- | --- | --- | --- | --- |
| `workstation.env` | Ubuntu 24.04 laptop | 42 | `LOCALHOST` | Development, simulation, operator station |
| `nuvo.env` | Nuvo (Neousys Nuvo-7100VTC) | 0 | `SUBNET` | Clearpath robot stack: base, IMU, GNSS receiver |
| `bender.env` | bender (i9, RTX 3060) | 0 | `SUBNET` | Bird Nose nodes and heavy sensor drivers; microphone array |

Every file sets `RMW_IMPLEMENTATION=rmw_fastrtps_cpp`.

## Why these values

- **Domain 0 on the robot and 42 everywhere else:** a ROS domain is a separate channel, so simulation can never command the physical robot.
- **`SUBNET` on the robot:** Nuvo and bender must find each other's topics over the Ethernet link. Tested 2026-11-06: bender received Nuvo's battery messages.
- **`LOCALHOST` on the workstation:** simulation traffic stays on the laptop instead of spreading across the lab network.

## Usage

These files are documentation and the source for Phase 5's hardware overlay; nothing reads them automatically yet. The workstation's live settings are in `containers/.env`, created from `containers/.env.example` with the same values.

## Limitations

Which sensor drivers run on Nuvo and which on bender is decided in Phase 5. Current intent: most on bender; the IMU, GNSS receiver, and base on Nuvo, because they connect to it by USB or serial.

## See also

- [containers](../../containers/README.md)
- [docs/architecture.md](../../docs/architecture.md)
