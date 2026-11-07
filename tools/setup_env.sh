#!/usr/bin/env bash
# Create containers/.env from containers/.env.example on first use, filling
# in this machine's user and group IDs. An existing .env is never changed.
set -Eeuo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
ENV_FILE="${REPO_ROOT}/containers/.env"
EXAMPLE="${REPO_ROOT}/containers/.env.example"

if [[ "$(id -u)" -eq 0 ]]; then
  echo "Error: run this as your normal user, not root or sudo." >&2
  echo "The container user must match your own user ID." >&2
  exit 1
fi

if [[ -f "${ENV_FILE}" ]]; then
  echo "Using existing ${ENV_FILE}"
  exit 0
fi

sed \
  -e "s/^HOST_UID=.*/HOST_UID=$(id -u)/" \
  -e "s/^HOST_GID=.*/HOST_GID=$(id -g)/" \
  -e "s/^DISPLAY=.*/DISPLAY=${DISPLAY:-:0}/" \
  "${EXAMPLE}" > "${ENV_FILE}"

echo "Created ${ENV_FILE} (UID $(id -u), GID $(id -g)). Edit it for machine-local settings."
