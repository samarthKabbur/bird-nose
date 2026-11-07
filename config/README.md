# config

## Purpose

Versioned configuration that is not code: what the robot is, what each computer's role is, and (from Phase 4) which scenarios simulation runs. Machine-local values such as addresses and passwords never go here; they belong in each machine's untracked `containers/.env`.

## Contents

| Folder | What it holds |
| --- | --- |
| [`robots/`](robots/README.md) | Clearpath `robot.yaml` for the Husky A200 |
| [`hosts/`](hosts/README.md) | Settings for each computer role: workstation, Nuvo, bender |
| [`scenarios/`](scenarios/README.md) | Simulation scenario definitions (Phase 4) |

## Usage

Simulation reads `robots/husky-a200/robot.yaml` directly through `bird_nose_bringup`. The host files document each role's settings; Phase 5 makes the hardware overlay read them.

## See also

- [containers](../containers/README.md): how the dev and simulation settings are applied
- Living doc: "Lab findings" and "Decision log"
