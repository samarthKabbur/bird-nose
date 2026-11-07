# Continuous integration

CI is the set of checks GitHub runs on every pull request, so a broken build or out-of-date docs are caught before they reach `main`. The workflows live in `.github/workflows/`; the scripts they call live in [`tools/ci/`](../tools/ci/README.md), so every check can also be run by hand.

## Workflows

| Workflow | File | Runs on | When | What it proves |
| --- | --- | --- | --- | --- |
| CI | `ci.yml` | GitHub-hosted Ubuntu 24.04 | Every pull request and every push to `main` | Docs match the code, scripts and Compose files are valid, and the ROS packages build and pass their tests |
| Docker image | `docker.yml` | GitHub-hosted Ubuntu 24.04 | Pull requests and pushes that change `containers/`, Mondays at 09:17 UTC, and by hand | The `dev` image still builds. The image is never pushed to a registry. |
| Simulation smoke test | `sim-smoke.yml` | A self-hosted runner labelled `bird-nose-sim` | Only by hand, from the Actions tab | Gazebo, Nav2 with SLAM, and one navigation goal work end to end |

### CI jobs

`checks` (Docs, scripts, and config), about one minute:

- `python3 tools/ci/check_docs.py`: links, repository map, module READMEs, launch arguments, parameters, and Compose services. See [tools/ci](../tools/ci/README.md) for each rule.
- `bash -n` and `shellcheck` on the repository's shell scripts, except `tools/robot/`, which keeps Nuvo's scripts unchanged until Phase 5.
- `docker compose config` for the base file with each overlay (none, NVIDIA, hardware) and each profile (none, `sim`, `operator`, `telemetry`).
- `actionlint` on the workflow files, downloaded at a fixed version and checked against its published checksum.

`build-test` (colcon build and test), a few minutes:

- Runs in `ros:jazzy-ros-base-noble`, pinned to the same digest as `containers/Dockerfile`.
- `rosdep install` with build, build-tool, and test dependencies only. Runtime dependencies such as the Clearpath simulator, Nav2, and Foxglove Bridge are skipped: the unit and lint tests do not need them, and skipping them saves most of the job's time. The Docker image workflow is what checks that the full set installs.
- `colcon build`, `colcon test`, and `colcon test-result --verbose`. Test results are kept as a downloadable artifact for 7 days.

> **Side note: why the Docker build is a separate workflow.** Building the full image takes 15–30 minutes and several GB. Most pull requests do not touch `containers/`, so running it on each one would slow every review for no gain. A path filter runs it only when container files change, and the weekly run catches upstream apt packages that change underneath an unchanged Dockerfile.

## Reproduce a check locally

| CI step | Run it yourself |
| --- | --- |
| Docs | `python3 tools/ci/check_docs.py` (host or container) |
| Shell scripts | `shellcheck --severity=warning tools/*.sh tools/ci/*.sh containers/entrypoint.sh src/bird_nose_telemetry/scripts/record_run` |
| Compose | `docker compose -f containers/compose.yaml --profile sim config --quiet` |
| Build and test | In a `./tools/dev.sh` shell: `colcon build --symlink-install && colcon test && colcon test-result --verbose` |
| Docker image | `./tools/dev.sh build` |
| Simulation smoke test | In a `./tools/dev.sh` shell, with no other simulation running: `tools/ci/sim_smoke.sh` |

## Cost and limits

The repository is public, and GitHub does not charge for standard GitHub-hosted runners in public repositories. The workflows keep it that way and keep storage small:

- Only standard runners (`ubuntu-24.04`) are used. Larger runners are always billed, even for public repositories, so do not add them.
- **Concurrency:** a new push to a pull request cancels that pull request's older run. Runs on `main` are never cancelled.
- **Retention:** artifacts (test results, smoke-test logs) are deleted after 7 days.
- **Cache:** the Docker build's layer cache uses GitHub's 10 GB per repository. Only `main` writes it; pull requests read it.
- **Timeouts:** every job has `timeout-minutes`, so a hung job stops instead of running for the 6-hour default.
- **Token:** every workflow sets `permissions: contents: read`, so the token GitHub gives a run can read the code and nothing else.

### Zero-spend budget (repository owner, once)

A budget of $0 that stops usage is a safety net: if anything ever became billable, GitHub would block it instead of charging. Set it in **Settings → Billing and licensing → Budgets and alerts** for the account that owns the repository: an Actions budget of $0 with **Stop usage when budget limit is reached** turned on. GitHub may already have created one; if so, leave it.

If Actions ever reports that usage is blocked even though this public repository should be free, that budget is the first thing to check.

## Repository settings (repository owner)

These are GitHub settings, not files, so they are listed here.

1. **Required checks.** After the first CI run on `main`, open **Settings → Branches → the `main` rule** (or **Rules → Rulesets**), turn on **Require status checks to pass**, and add `Docs, scripts, and config` and `colcon build and test`. Do not require the Docker image or simulation checks: the Docker image workflow runs only when `containers/` changes, and a required check that never runs leaves a pull request waiting forever.
2. **Pull requests from forks.** In **Settings → Actions → General**, find the setting for approving workflow runs from fork pull requests and choose the strictest option, which requires approval for all outside contributors. Before approving a run, look at whether the pull request changes anything in `.github/`: a pull request runs the workflow files from its own branch, so a fork could edit one.
3. **Workflow permissions.** In **Settings → Actions → General → Workflow permissions**, keep **Read repository contents and packages permissions**.

## Self-hosted runner for the simulation test

The simulation test needs Gazebo and graphics, which hosted runners do not provide well, so it runs on a team computer registered as a self-hosted runner. Nothing else uses that runner, and nothing starts it automatically.

> **Side note: what a self-hosted runner is.** A small program from GitHub that you install on your own computer. It polls GitHub for jobs whose `runs-on` labels match its own, runs them as the user it is installed under, and reports the result. Anything a workflow says to run, it runs on that computer, which is why the rules below matter.

### Isolation rules

- **Not on the robot network.** The runner computer must never be connected to the robot's network (`192.168.131.x`) or be Nuvo or bender. The smoke test also refuses to run on ROS domain 0 or with discovery wider than localhost, but the network rule comes first.
- **Manual trigger only.** `sim-smoke.yml` uses `workflow_dispatch`, which only people with write access can start. No workflow may use `runs-on: self-hosted` with `pull_request`, `pull_request_target`, `push`, or `schedule` triggers; reviewers reject any pull request that adds one.
- **A dedicated user account.** Install the runner under its own non-root user (for example `gh-runner`), not your personal account, so jobs cannot read your SSH keys, browser profile, or other files. That user must be in the `docker` group to run containers. Membership in `docker` is effectively root on that computer, which is why the computer must be a trusted team machine and why only manual, write-access runs may use it.
- **Its own containers.** The workflow uses Compose project `bird-nose-ci`, image `bird-nose-ci:jazzy`, and ROS domain 43, so it does not replace or talk to a developer's `bird-nose` containers on domain 42. It removes its containers and volumes when it finishes.
- **Off when not needed.** The simplest safe habit is to start the runner (`./run.sh`) only when you want to run the test and stop it afterwards, rather than installing it as an always-on service.

### Register the runner (repository owner)

1. On the chosen computer (for example the `hero` laptop), create the user: `sudo adduser gh-runner && sudo usermod -aG docker gh-runner`.
2. On GitHub: **Settings → Actions → Runners → New self-hosted runner**, Linux, x64. Follow the download and `./config.sh` commands it shows, as `gh-runner`, in that user's home folder.
3. When `config.sh` asks for labels, add `bird-nose-sim`. The runner adds `self-hosted`, `Linux`, and `X64` itself.
4. Start it with `./run.sh`, then run **Actions → Simulation smoke test (self-hosted) → Run workflow**. Stop it with Ctrl+C when done.

GUI windows are not needed: the test runs Gazebo without a window. It still renders the Ouster's simulated scan on a graphics card, so on a computer with an NVIDIA GPU, such as `hero`, install the NVIDIA Container Toolkit for the runner and leave the workflow's **gpu** option on. On a computer with only Intel or AMD graphics, turn **gpu** off. The reason is under Limitations in [tools/ci](../tools/ci/README.md#limitations).

## Who updates what

| What | How it is kept current | Who acts |
| --- | --- | --- |
| GitHub Actions used by the workflows | Pinned to a commit with the version in a comment. Dependabot opens one grouped pull request a month (`.github/dependabot.yml`). | Any team member reviews and merges it once CI passes |
| `actionlint` version and checksum in `ci.yml` | By hand, when a new release matters. Change both values together. | Whoever needs the newer version |
| ROS base image digest | By hand, in its own pull request (see [CONTRIBUTING.md](../CONTRIBUTING.md)). `ci.yml` and `containers/Dockerfile` must use the same digest. | Repository owner, or whoever needs the update |
| Weekly Docker image build | Fails when an upstream apt package breaks the image. GitHub emails the repository owner. | Repository owner investigates or assigns it |
| Self-hosted runner program | Updates itself when it starts | Nobody, unless an update fails |
| Runner computer (Ubuntu, Docker) | Normal OS updates | The computer's owner |
| Repository settings above, and the budget | Checked when the team changes | Repository owner |

## See also

- [tools/ci](../tools/ci/README.md): the scripts CI runs
- [CONTRIBUTING.md](../CONTRIBUTING.md): the pull request workflow these checks protect
- [containers](../containers/README.md): the image the Docker workflow builds
- Living doc: "Phase 3" and "Safety and deployment boundaries"
