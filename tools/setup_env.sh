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

# Group IDs that own /dev/dri on this machine (they differ between installs).
gid_of() { getent group "$1" | cut -d: -f3 || true; }
video_gid="$(gid_of video)"
render_gid="$(gid_of render)"

# Fill in this machine's values for a key in a freshly rendered .env.
render_example() {
  sed \
    -e "s/^HOST_UID=.*/HOST_UID=$(id -u)/" \
    -e "s/^HOST_GID=.*/HOST_GID=$(id -g)/" \
    -e "s/^DISPLAY=.*/DISPLAY=${DISPLAY:-:0}/" \
    -e "s/^VIDEO_GID=.*/VIDEO_GID=${video_gid:-44}/" \
    -e "s/^RENDER_GID=.*/RENDER_GID=${render_gid:-993}/" \
    "${EXAMPLE}"
}

if [[ ! -f "${ENV_FILE}" ]]; then
  render_example > "${ENV_FILE}"
  echo "Created ${ENV_FILE} (UID $(id -u), GID $(id -g)). Edit it for machine-local settings."
  exit 0
fi

# Existing .env: never change values, only add settings introduced since it
# was created, so updates to .env.example reach every machine.
added=0
while IFS= read -r line; do
  key="${line%%=*}"
  if ! grep -q "^${key}=" "${ENV_FILE}"; then
    echo "${line}" >> "${ENV_FILE}"
    echo "Added ${line} to ${ENV_FILE}"
    added=1
  fi
done < <(render_example | grep -E '^[A-Z_]+=')
(( added )) || echo "Using existing ${ENV_FILE}"
