# .devcontainer

## Purpose

Lets VS Code open this repository inside the same `dev` container that `./tools/dev.sh` starts. The editor's language servers, terminal, and debugger then see exactly the same ROS installation as everyone else.

## Contents

| File | What it does |
| --- | --- |
| `devcontainer.json` | Uses `containers/compose.yaml`, service `dev`, workspace `/workspaces/bird-nose`, user `dev`. Runs `tools/setup_env.sh` on the host first. Installs Python, C++, YAML, and XML extensions in the container. Stops the container when VS Code closes. |

## Usage

1. Install VS Code and its **Dev Containers** extension on the Ubuntu host.
2. Open the repository folder in VS Code.
3. Run **Dev Containers: Reopen in Container** from the command palette.
4. Build and test from VS Code's terminal: `colcon build --symlink-install && colcon test`.

## Limitations

`remoteUser` is fixed to `dev`. If you change `CONTAINER_USER` in `containers/.env`, change it here too.

## See also

- [containers](../containers/README.md)
