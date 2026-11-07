#!/usr/bin/env bash

set -Eeuo pipefail

# Always run Docker Compose from the directory containing this script so that
# compose.yaml and .env are found even when the script is launched elsewhere.
SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

START_TIMEOUT="${CLEARPATH_START_TIMEOUT:-120}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Error: Docker is not installed or is not in PATH." >&2
  exit 1
fi

if ! docker compose version >/dev/null 2>&1; then
  echo "Error: the Docker Compose plugin is unavailable." >&2
  exit 1
fi

if [[ ! -f .env ]]; then
  echo "Error: $SCRIPT_DIR/.env was not found." >&2
  echo "It must define SETUP_PATH_HOST=/etc/clearpath." >&2
  exit 1
fi

if [[ ! -f /etc/clearpath/robot.yaml ]]; then
  echo "Error: /etc/clearpath/robot.yaml was not found." >&2
  exit 1
fi

echo "Starting the Clearpath robot container..."
docker compose up -d robot

echo "Waiting for clearpath-platform to become active (up to ${START_TIMEOUT}s)..."
deadline=$((SECONDS + START_TIMEOUT))

while (( SECONDS < deadline )); do
  if docker compose exec -T --user root robot \
      systemctl is-active --quiet clearpath-platform 2>/dev/null; then
    echo
    echo "Clearpath platform is active."
    docker compose ps robot
    echo
    echo "Keep the physical Stop engaged until ROS feedback and controller input are verified."
    echo "Opening an interactive robot shell with ROS initialized..."
    echo "Type 'exit' when you want to leave the container."
    echo
    exec docker compose exec --user robot robot \
      bash -lc 'source /etc/clearpath/setup.bash && exec bash -i'
  fi

  sleep 2
done

echo >&2
echo "Error: clearpath-platform did not become active within ${START_TIMEOUT}s." >&2
echo "Container status:" >&2
docker compose ps robot >&2 || true
echo >&2
echo "Recent container output:" >&2
docker compose logs --tail=100 robot >&2 || true
echo >&2
echo "For detailed platform logs, run:" >&2
echo "  docker compose exec --user root robot journalctl -u clearpath-platform -b --no-pager -l" >&2
exit 1
