#!/usr/bin/env bash
# One-command development environment.
#
#   ./tools/dev.sh            build (first time), start, and open a shell
#   ./tools/dev.sh build      rebuild the image only
#   ./tools/dev.sh down       stop and remove the dev container
#   GPU=1 ./tools/dev.sh      same, with the NVIDIA overlay
#
# Requirements on the host: Docker Engine with the Compose plugin, and Git.
# Nothing ROS-related is installed on the host.
set -Eeuo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"

command -v docker >/dev/null 2>&1 || { echo "Error: Docker is not installed." >&2; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "Error: the Docker Compose plugin is missing." >&2; exit 1; }

"${REPO_ROOT}/tools/setup_env.sh"

compose=(docker compose -f containers/compose.yaml)
if [[ "${GPU:-0}" == "1" ]]; then
  compose+=(-f containers/compose.nvidia.yaml)
fi

# Allow containers run as this user to open windows on this display
# (needed for Gazebo and RViz). Only this user is allowed, not everyone.
if command -v xhost >/dev/null 2>&1 && [[ -n "${DISPLAY:-}" ]]; then
  xhost "+SI:localuser:$(id -un)" >/dev/null || true
fi

case "${1:-shell}" in
  build)
    "${compose[@]}" build dev
    ;;
  down)
    "${compose[@]}" down
    ;;
  shell)
    "${compose[@]}" up -d --build dev
    exec "${compose[@]}" exec dev bash
    ;;
  *)
    echo "Usage: $0 [shell|build|down]" >&2
    exit 1
    ;;
esac
