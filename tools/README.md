# tools

## Purpose

Helper scripts that run on the host computer (outside containers) to set up and enter the development environment.

## Contents

| Path | What it does |
| --- | --- |
| `dev.sh` | One-command development environment: creates `containers/.env`, allows GUI windows, builds the image if needed, starts `dev`, and opens a shell |
| `setup_env.sh` | Creates `containers/.env` from `containers/.env.example` with your user and group IDs. Never overwrites an existing `.env`. Refuses to run as root. |
| [`robot/`](robot/README.md) | Robot container scripts from Nuvo, preserved unchanged for Phase 5 |

## Usage

```bash
./tools/dev.sh            # build (first time), start, and open a shell
./tools/dev.sh build      # rebuild the image only
./tools/dev.sh down       # stop and remove the containers
GPU=1 ./tools/dev.sh      # same, with the NVIDIA overlay
```

Run these as your normal user, not with `sudo`. The container user is created with your user ID, so files it writes into the repository stay yours. Root would make them root-owned.

`dev.sh` runs `xhost +SI:localuser:<you>`. That lets your own user's processes, including the container, open windows on your display, without opening the display to anyone else.

## Testing

`bash -n tools/*.sh` checks syntax. `./tools/dev.sh` ending at a `dev@<host>` prompt confirms the whole chain.

## Limitations

Linux hosts only: `xhost` and host networking assume Ubuntu with X11 or XWayland.

## See also

- [containers](../containers/README.md)
- [CONTRIBUTING.md](../CONTRIBUTING.md)
