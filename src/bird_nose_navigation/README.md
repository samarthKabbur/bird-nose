# bird_nose_navigation

## Purpose

Bird Nose's own Nav2 configuration: parameters, maps, and behavior trees, once Clearpath's demo defaults need tuning for this robot and its environments.

Package type: `ament_cmake`, configuration only.

## Contents

| Path | What it holds |
| --- | --- |
| `config/` | Empty until Phase 2. Tuned Nav2 parameter files go here. |

## Usage

Until Phase 2, navigation runs on Clearpath's demo parameters through `bird_nose_bringup nav2.launch.py`. When a file is added here, that launch file gains an argument pointing at it.

## Configuration rules

- Start each tuned file from Clearpath's demo file, and record which version it came from.
- Comment every changed value with what changed and why (for example, `# was 0.5; robot oscillated in narrow corridors`).
- Parameters use REP 103 units: metres, seconds, radians.
- Any parameter change that affects motion is tested in simulation, and the recording is noted in the pull request.

## Testing

`colcon test --packages-select bird_nose_navigation`. Phase 4 scenario tests compare navigation results between parameter revisions.

## See also

- [bird_nose_bringup](../bird_nose_bringup/README.md)
- [Nav2 configuration guide](https://docs.nav2.org/configuration/index.html)
