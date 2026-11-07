#!/usr/bin/env bash

set -Eeuo pipefail

# Always run Docker Compose from the directory containing this script.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: Docker is not installed or is not in PATH." >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Error: the Docker Compose plugin is unavailable." >&2
  exit 1
fi

if ! docker compose ps --status running --services 2>/dev/null | \
    grep -Fxq robot; then
  echo "The Clearpath robot container is already stopped."
  docker compose ps robot
  exit 0
fi

echo "Before stopping Clearpath:"
echo "  1. Center both controller sticks."
echo "  2. Release LB and RB."
echo "  3. Set the controller down."
echo "  4. Push the physical red Stop button inward until it latches."
echo

read -r -p "Is the physical Stop engaged? Type YES to continue: " confirmation

if [[ "$confirmation" != "YES" ]]; then
  echo "Shutdown cancelled. The robot container is still running."
  exit 1
fi

echo "Stopping the Clearpath robot container..."
docker compose stop --timeout 30 robot

if docker compose ps --status running --services 2>/dev/null | \
    grep -Fxq robot; then
  echo "Error: the robot container is still running." >&2
  docker compose ps robot >&2
  exit 1
fi

echo
echo "Clearpath robot container stopped."
docker compose ps robot
