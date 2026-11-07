#!/usr/bin/env bash
# Container entrypoint for Bird Nose images.
#
# Sources ROS 2 Jazzy and, when it has been built, the Bird Nose workspace
# overlay, then runs the requested command. The same file is sourced from
# the dev user's ~/.bashrc so interactive shells get an identical setup.

# shellcheck source=/dev/null
source "/opt/ros/${ROS_DISTRO:-jazzy}/setup.bash"

BIRD_NOSE_WS="${BIRD_NOSE_WS:-/workspaces/bird-nose}"
if [[ -f "${BIRD_NOSE_WS}/install/setup.bash" ]]; then
  # shellcheck source=/dev/null
  source "${BIRD_NOSE_WS}/install/setup.bash"
fi

# When sourced (from ~/.bashrc) stop here; when executed, run the command.
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
  exec "$@"
fi
