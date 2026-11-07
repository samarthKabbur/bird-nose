# config/robots

## Purpose

Describes the physical robot in Clearpath's `robot.yaml` format: platform, attachments, sensors, ROS namespace, and middleware. Clearpath's tools generate the robot model, launch files, and driver parameters from this one file, both in simulation and on the robot.

## Contents

| Path | What it is |
| --- | --- |
| `husky-a200/robot.yaml` | Husky A200, serial `a200-0539`. Started from the file on Nuvo on 2026-11-06, which has driven the robot. |

## What the file sets

| Section | Value | Note |
| --- | --- | --- |
| `system.ros2.namespace` | `Nuvo_7100VTC_Series` | Kept as is; every robot topic starts with it, and the scripts in `tools/robot/` assume it |
| `system.ros2.domain_id` | `0` | Hardware domain. Simulation overrides this with `ROS_DOMAIN_ID=42`. |
| `system.ros2.rmw_implementation` | `rmw_fastrtps_cpp` | Fast DDS |
| `platform.controller` | `logitech` | Logitech F710 gamepad |
| `sensors.imu` | MicroStrain on `/dev/microstrain_rtk` | Plugged into Nuvo by USB |
| `sensors.lidar3d` | Ouster OS1-128 at `192.168.131.128` | Data sent to Nuvo (`udp_dest: 192.168.131.1`) |
| `sensors.camera`, `gps`, `lidar2d` | empty | The RealSense, both Duro GPS units, and the SICK lidar were removed from the robot |

Every difference from Nuvo's original is marked `CHANGED` in the file:

- Removed the sensors that are no longer fitted.
- Added the Ouster OS1-128.
- Changed the IMU port from `/dev/microstrain_main`, which does not exist on Nuvo, to `/dev/microstrain_rtk`.
- Fixed the velocity-limit keys, which had a stray quote. Their values equal Clearpath's A200 defaults, so driving behavior is unchanged.

## Usage

- **Simulation:** `ros2 launch bird_nose_bringup sim.launch.py` copies this file into a scratch folder and starts Clearpath's simulator from it.
- **Robot (Phase 5):** copy it to Nuvo, never mount it from the repository, because Clearpath's generators write files next to it:
  ```bash
  sudo cp /etc/clearpath/robot.yaml /etc/clearpath/robot.yaml.bak-$(date +%F)
  sudo install -m 664 -o nrgadmin -g nrgadmin config/robots/husky-a200/robot.yaml /etc/clearpath/robot.yaml
  ```

## Testing

Clearpath's `clearpath_config` parser (Jazzy) loads the file and reports one Ouster, one IMU, and no camera, GPS, or 2D lidar. After any edit, check that the simulation still starts.

## Limitations

- The Ouster position (`xyz: [0.0, 0.0, 0.3]`) is a rough estimate. Replace it with measured offsets from `base_link`.
- The GNSS receiver is unconfirmed, so no GPS entry exists yet.
- The photos show a custom crossbar where the file lists Clearpath's `sensor_arch_300`; still to verify.
- Microphone modules are not Clearpath sensors; they belong in `bird_nose_description`.

## See also

- [bird_nose_bringup](../../src/bird_nose_bringup/README.md): uses this file for simulation
- [Clearpath robot.yaml reference](https://docs.clearpathrobotics.com/docs/ros/config/yaml/overview)
- Living doc: "Onboard computer survey" and "Still to measure"
