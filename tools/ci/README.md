# tools/ci

## Purpose

Scripts that the CI workflows run, written so that you can run the same check yourself before pushing. The workflows themselves are in `.github/workflows/` and are described in [docs/ci.md](../../docs/ci.md).

## Contents

| Path | What it does | Where it runs |
| --- | --- | --- |
| `check_docs.py` | Checks that the docs still match the code (see below) | Host or container; needs only Python 3 and Git |
| `diff_params.py` | Lists every parameter that differs between two ROS parameter files, such as Clearpath's Nav2 file and the one Bird Nose generates | Host or container; needs Python 3 and PyYAML |
| `sim_smoke.sh` | Starts the simulation without a window, starts Nav2 with SLAM, sends one goal, and passes if the robot reaches it | Inside the dev container |

## Usage

```bash
python3 tools/ci/check_docs.py      # on the host or in the container
```

```bash
# In a ./tools/dev.sh shell. Stop any simulation you already have running first.
tools/ci/sim_smoke.sh
GOAL_X=2.0 GOAL_Y=0.5 tools/ci/sim_smoke.sh
SIM_HEADLESS=false tools/ci/sim_smoke.sh     # show the Gazebo window
```

`check_docs.py` checks:

| Check | Fails when |
| --- | --- |
| `links` | A relative Markdown link points at a file not in Git, or at a `#heading` that does not exist |
| `map` | A module folder is missing from the README's repository map |
| `readmes` | A module folder has no `README.md`, or the README lacks a Purpose, Contents, or See also section |
| `launch` | A launch argument has no `description=`, or is not named in its package README |
| `params` | A ROS parameter is declared without a `ParameterDescriptor`, or is not named in its package README |
| `services` | A Compose service is missing from the README's Services table |

A module folder is any top-level folder, any folder directly under `config/` or `tools/`, and any ROS package under `src/`. `docs/` and `.github/` are documented by the files in `docs/` instead of a README.

## Configuration

`sim_smoke.sh` reads these environment variables:

| Variable | Default | Meaning |
| --- | --- | --- |
| `GOAL_X`, `GOAL_Y` | `1.0`, `0.0` | Goal in the `map` frame, metres, relative to where SLAM starts (the spawn point) |
| `SIM_TIMEOUT_S` | `300` | Seconds to wait for `/clock` and the robot's odometry |
| `NAV2_TIMEOUT_S` | `240` | Seconds to wait for Nav2's `bt_navigator` to become active and SLAM to publish a map |
| `SIM_HEADLESS` | `true` | `false` opens the Gazebo window, which renders through the desktop like a normal simulation |
| `GOAL_TIMEOUT_S` | `180` | Seconds allowed to reach the goal |
| `ROBOT_YAML` | `config/robots/husky-a200/robot.yaml` | Robot to simulate; the namespace is read from it |

It refuses to run when `ROS_DOMAIN_ID` is `0` or unset, or when `ROS_AUTOMATIC_DISCOVERY_RANGE` is not `LOCALHOST`, so it cannot reach the physical robot. Logs (`colcon_build.log`, `sim.log`, `nav2.log`, `goal.log`) and `report.md` go to `data/reports/sim_smoke/<UTC time>/`. On a failure it prints the error lines and the last 40 lines of the log for the step that failed. It stops early, without waiting for the timeout, when a launch exits or reports `process has died`.

## Testing

`bash -n tools/ci/sim_smoke.sh` and `shellcheck tools/ci/sim_smoke.sh` check the script, and CI runs both. `check_docs.py` is exercised by every pull request.

## Limitations

- Without a window, Gazebo still renders the Ouster's simulated scan, but it picks the first graphics card it finds rather than the one your desktop uses. On a laptop with both Intel and NVIDIA graphics, such as `hero`, it picks the NVIDIA card. Without the NVIDIA driver in the container, Gazebo then crashes with "Failed to create dummy render window", and the script prints a hint. Fixes: start the container with `GPU=1 ./tools/dev.sh` (needs the NVIDIA Container Toolkit on the host), or run with `SIM_HEADLESS=false` on a desktop. Computers with only Intel or AMD graphics are not affected.
- It runs in the same container as everything else, so a simulation you already have running on the same ROS domain would interfere. The self-hosted workflow avoids this with domain 43.

## See also

- [docs/ci.md](../../docs/ci.md): the workflows, runner setup, and who updates what
- [tools](../README.md)
- [bird_nose_bringup](../../src/bird_nose_bringup/README.md): the launch files the smoke test uses
