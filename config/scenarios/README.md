# config/scenarios

## Purpose

Deterministic simulation scenarios, used to compare algorithm versions fairly and to catch regressions (Phase 4). The same scenario with the same random seed must give the same result every run.

## Contents

Empty until Phase 4.

## Planned format

Each scenario file will define:

| Field | Example |
| --- | --- |
| World | a Gazebo world from `bird_nose_sim` or `clearpath_gz` |
| Initial pose | `x`, `y`, `yaw` passed to `sim.launch.py` |
| Obstacles | static and moving objects |
| Sensor noise | noise levels or dropouts to inject |
| Random seed | fixed integer |
| Recording policy | which topics to record to MCAP |
| Assertions | the measurable conditions that decide pass or fail |

Initial classes, from the plan: empty-world motion, static obstacles, dynamic obstacles, localization recovery, sensor dropout or noise, goal cancellation and replanning, and Bird Nose-specific success and safety conditions.

## See also

- [bird_nose_sim](../../src/bird_nose_sim/README.md): worlds and assets
- Living doc: "Simulation and testing"
