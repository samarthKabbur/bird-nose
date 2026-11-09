# config/scenarios

## Purpose

Scenario files: each one describes a simulated run completely (world, start pose, seed, survey route, simulated birds, time limit) and the checks that decide whether it passed. The same scenario and seed should give the same result every run, within small tolerances, so two versions of an algorithm can be compared fairly.

## Contents

| File | What it tests |
| --- | --- |
| `orchard_nav_survey.yaml` | Navigation only: four 20 ft stops down one aisle of Clearpath's orchard world |

## Usage

Inside the dev container:

```bash
tools/ci/run_scenario.sh orchard_nav_survey                  # run and judge; Gazebo window
SIM_HEADLESS=true tools/ci/run_scenario.sh orchard_nav_survey # no window (GPU=1 on hero)
ros2 launch bird_nose_bringup scenario.launch.py scenario:=orchard_nav_survey   # run only
```

Scenarios run on a simulation ROS domain only; both commands refuse domain 0.

## Format (version 1)

All coordinates are in the Gazebo **world** frame, in metres; angles in radians. `scenario.launch.py` converts the route to the map frame, whose origin SLAM puts at the robot's start pose.

```yaml
format: 1                               # required; this README describes version 1
name: orchard_nav_survey                # required; must equal the file name
description: One line for reports       # optional
world: orchard                          # required; a clearpath_gz world
robot_start: {x: 0.0, y: 1.4, yaw: 0.0} # required; spawn pose
seed: 1                                 # required; integer, recorded with the run
survey:                                 # required
  waypoints: [[0.0, 1.4], [24.4, 1.4]]  # at least two points; the first within 0.5 m of robot_start
  stop_every_ft: 20                     # stop spacing along the route, feet
  record_s: 10                          # time at each stop, simulation seconds
birds: []                               # optional; used from step 4.2 (species, x, y, z, clip, ...)
noise: {}                               # optional; used from step 4.2
timeout_s: 900                          # required; wall-clock limit for the whole run
checks:                                 # required
  stops_reached: all                    # "all" or a minimum number
  max_nav_failures: 0                   # most stops Nav2 may fail to reach
```

Unknown keys are errors, so a typo is caught before a run. Checks for later steps (`species_found`, `min_confidence`, `max_analysis_s`, `max_bearing_error_deg`, `max_location_error_ft`) may already be written; they are reported as "not evaluated" until their step adds them. CI loads every file here on each pull request.

## Writing a new scenario

1. Copy an existing file and change `name` to match the new file name.
2. Pick the route in the world: Clearpath's `docs/` folder in `clearpath_simulator` has a picture of each world, and Gazebo shows coordinates under the mouse.
3. Run it with `run_scenario.sh` and include the report in the pull request.

## Limitations

- Navigation only for now: `birds` and `noise` are accepted but unused until step 4.2.
- One robot, `config/robots/husky-a200/robot.yaml`.

## See also

- [bird_nose_evaluation](../../src/bird_nose_evaluation/README.md): the loader and the checks
- [bird_nose_bringup](../../src/bird_nose_bringup/README.md): `scenario.launch.py`
- [bird_nose_sim](../../src/bird_nose_sim/README.md): worlds and assets
- Living doc: "Phase 4 design", Scenarios and evaluation
