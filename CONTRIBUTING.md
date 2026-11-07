# Contributing to Bird Nose

## One `main` branch

`main` is the only long-lived branch, and every computer (workstation, Nuvo, bender) runs from it. A branch is a temporary change under review, never a machine or a deployment target. Machine differences live in Compose profiles, `config/hosts/`, `config/robots/`, and untracked `.env` files.

`main` is protected: changes reach it only through a pull request.

## Workflow

1. Update and branch from `main`:
   ```bash
   git switch main && git pull
   git switch -c feature/nav2-tuning
   ```
   Use a prefix that says what the branch is: `feature/`, `fix/`, `docs/`, or `chore/`.
2. Make small, focused commits whose messages say what changed and why.
3. Build and test inside the dev container before pushing:
   ```bash
   colcon build --symlink-install && colcon test && colcon test-result --verbose
   ```
4. Push and open a pull request. Fill in the template, including how you tested.
5. Merge after review, then delete the branch.

## Never commit

- Machine-local addresses, hostnames, usernames, Wi-Fi or SSH credentials. Put them in `containers/.env`, which Git ignores.
- Recordings (`.mcap`, `.db3`), logs, and reports. They belong in `data/`, whose contents Git ignores.
- Colcon output (`build/`, `install/`, `log/`).

## Changing dependencies

- System packages: add them to `containers/Dockerfile`, not by hand inside a container. Changes made only inside a container are lost.
- Extra source repositories: add them to `dependencies.repos`.
- The base image is pinned by digest. Change it deliberately, in its own pull request.

## Documentation

Every module (each top-level folder and each ROS package) has a `README.md` with the same sections: Purpose, Contents, Usage, Interfaces, Configuration, Testing, Limitations, See also. Keep them accurate in the same pull request as the code change.

- **Interfaces are reference:** every topic, service, action, and parameter gets its type, units, frame, default, and QoS in the module's README.
- **Let the code describe itself:** declare parameters with a `ParameterDescriptor` (description and range), give every launch argument a `description=`, comment every field of custom messages, and put units in names (`_m`, `_s`, `_hz`). `ros2 param describe`, `ros2 launch … --show-args`, and `ros2 interface show` then display them.
- **Units and frames follow REP 103 and REP 105**, so link to those rather than re-explaining them.
- **The "why" lives in the living doc:** the team's plan, decisions, and lab findings are kept there; READMEs describe how to use the code and link to it.
- **Diagrams** are Mermaid code blocks in Markdown, so they display on GitHub and change in the same diff as the code. See [docs/architecture.md](docs/architecture.md).
- **New terms** go in [docs/glossary.md](docs/glossary.md).

## Robot safety

- Development and simulation use ROS domain 42 with localhost discovery. The robot uses domain 0. Do not change these defaults in a pull request without discussing it first.
- Nothing that can drive the physical robot is merged until the hardware safety controls and test gates are documented.
