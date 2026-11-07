# bird_nose_sim

## Purpose

Gazebo Harmonic worlds and simulation assets for Bird Nose: environments resembling where the robot will look for birds, and the props scenarios need.

Package type: `ament_cmake`, assets only.

## Contents

| Path | What it holds |
| --- | --- |
| `worlds/` | Empty until a Bird Nose world is needed. Clearpath's worlds (default `warehouse`) are used until then. |

## Usage

Once a world is added, start it with `ros2 launch bird_nose_bringup sim.launch.py world:=<name>`. Phase 2 makes `sim.launch.py` find worlds in this package.

## Rules for assets

- Worlds are `.sdf` files for Gazebo Harmonic.
- Large meshes go through Git LFS, never plain Git.
- Each world gets a short comment block at the top: what it represents and which scenarios use it.

## Testing

`colcon test --packages-select bird_nose_sim`. Each world must load headless (`headless:=true`) without errors.

## See also

- [config/scenarios](../../config/scenarios/README.md): scenario definitions that pick a world
- [bird_nose_bringup](../bird_nose_bringup/README.md)
