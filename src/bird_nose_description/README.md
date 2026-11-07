# bird_nose_description

## Purpose

Robot-model additions for parts Clearpath does not know about: the 16SoundsUSB microphone modules and the custom aluminium crossbar holding the Ouster. The Husky itself and its Clearpath-supported sensors come from `config/robots/husky-a200/robot.yaml`; this package adds only Bird Nose's own payloads, so it never copies Clearpath's description.

Package type: `ament_cmake`, URDF/xacro only.

## Contents

| File | What it is |
| --- | --- |
| `urdf/bird_nose_payloads.urdf.xacro` | Macro `bird_nose_payloads(parent)`, empty until positions are measured |

## Usage

Once filled in, Clearpath's `robot.yaml` will include it through the `platform.extras.urdf` field, so it appears in both the simulator and the real robot's model. Not wired in yet.

## Interfaces

None yet. Planned: one frame per microphone module (for example `mic_0_link` … `mic_15_link`, matching the 16SoundsUSB channel numbers) under the robot's TF tree. Sound localization depends on knowing each microphone's exact position.

## Testing

`colcon test --packages-select bird_nose_description` runs xmllint and CMake lint. When links are added, `xacro bird_nose_payloads.urdf.xacro` must render, and RViz must show them in the right places.

## Limitations

Waiting on lab measurements: each microphone module's position relative to `base_link`, which 16SoundsUSB channel each connects to, and the crossbar geometry. The photos show modules at the corners and four on the crossbar.

## See also

- [config/robots](../../config/robots/README.md)
- Living doc: "Still to measure"
