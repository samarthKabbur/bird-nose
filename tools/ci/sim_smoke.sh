#!/usr/bin/env bash
# Simulation smoke test: start the simulated Husky without a window, start
# Nav2 with SLAM, send one navigation goal, and pass only if the robot
# reaches it.
#
# Runs inside the dev container, either by hand from a ./tools/dev.sh shell
# or from the manual "Simulation smoke test" workflow on a self-hosted runner:
#
#   tools/ci/sim_smoke.sh                 # goal 1.0 m ahead of the spawn point
#   GOAL_X=2.0 GOAL_Y=0.5 tools/ci/sim_smoke.sh
#   SIM_HEADLESS=false tools/ci/sim_smoke.sh   # with the Gazebo window
#
# Logs and a short report go to data/reports/sim_smoke/<UTC time>/, which
# Git ignores.
#
# Safety: refuses to run on ROS domain 0 or with discovery wider than
# localhost, so it can never reach the physical robot.
set -euo pipefail

GOAL_X="${GOAL_X:-1.0}"
GOAL_Y="${GOAL_Y:-0.0}"
SIM_HEADLESS="${SIM_HEADLESS:-true}"
SIM_TIMEOUT_S="${SIM_TIMEOUT_S:-300}"
NAV2_TIMEOUT_S="${NAV2_TIMEOUT_S:-240}"
GOAL_TIMEOUT_S="${GOAL_TIMEOUT_S:-180}"

WS="${BIRD_NOSE_WS:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
ROBOT_YAML="${ROBOT_YAML:-$WS/config/robots/husky-a200/robot.yaml}"
OUT="$WS/data/reports/sim_smoke/$(date -u +%Y%m%dT%H%M%SZ)"

log() { echo "[sim_smoke $(date -u +%H:%M:%S)] $*"; }
fail() { log "FAIL: $*"; echo "- Result: **FAIL** ($*)" >> "$OUT/report.md"; exit 1; }

# --- Safety guard -----------------------------------------------------------
if [[ "${ROS_DOMAIN_ID:-0}" == "0" ]]; then
  echo "Refusing to run: ROS_DOMAIN_ID is 0 (the physical robot's domain) or unset." >&2
  exit 2
fi
if [[ "${ROS_AUTOMATIC_DISCOVERY_RANGE:-}" != "LOCALHOST" ]]; then
  echo "Refusing to run: ROS_AUTOMATIC_DISCOVERY_RANGE must be LOCALHOST." >&2
  exit 2
fi

mkdir -p "$OUT"
{
  echo "# Simulation smoke test"
  echo
  echo "- Commit: $(git -C "$WS" rev-parse --short HEAD 2>/dev/null || echo unknown)"
  echo "- ROS domain: $ROS_DOMAIN_ID, discovery: $ROS_AUTOMATIC_DISCOVERY_RANGE"
  echo "- Goal: x=$GOAL_X m, y=$GOAL_Y m in the map frame"
  echo "- Gazebo headless: $SIM_HEADLESS"
} > "$OUT/report.md"

# Stop everything this script started, whatever happens.
PIDS=()
cleanup() {
  for pid in "${PIDS[@]}"; do kill -INT -- "-$pid" 2>/dev/null || true; done
  sleep 5
  for pid in "${PIDS[@]}"; do kill -KILL -- "-$pid" 2>/dev/null || true; done
  log "logs and report in ${OUT#"$WS"/}"
}
trap cleanup EXIT

# Show the lines of a log that usually explain a failure, then its tail.
show_log() {
  local file="$1"
  [[ -f "$file" ]] || return 0
  echo "----- errors in ${file#"$WS"/} -----"
  grep -nE 'ERROR|WARN|\[Err\]|died|exception|Traceback|EGL|[Rr]endering|[Aa]bort|[Ff]ail' "$file" | tail -n 40 || true
  echo "----- last 40 lines of ${file#"$WS"/} -----"
  tail -n 40 "$file"
  # Known cause: an NVIDIA card (PCI vendor 10de) is visible in /dev/dri but
  # its driver is not in the container, and windowless rendering picked it.
  if grep -q 'Failed to create dummy render window' "$file" &&
     grep -q 'pci id for fd [0-9]*: 10de' "$file"; then
    echo "HINT: Gazebo tried to render on the NVIDIA GPU, whose driver is not in this"
    echo "      container. Start the container with GPU=1 (NVIDIA Container Toolkit),"
    echo "      or run with SIM_HEADLESS=false on a desktop. See tools/ci/README.md."
  fi
}

# Wait until a command succeeds, retrying every 5 s. Each check must have its
# own timeout: a ROS command that waits for a missing node forever would
# otherwise stop this loop from ever reaching its timeout. Fails early if the launch
# writing to the log has stopped or reports a crashed process, and fails
# after the timeout otherwise. Either way, prints that log's useful lines.
wait_for() {
  local what="$1" timeout_s="$2" pid="$3" logfile="$4"; shift 4
  local start=$SECONDS
  log "waiting for $what (up to ${timeout_s}s)"
  until "$@" > /dev/null 2>&1; do
    if ! kill -0 "$pid" 2>/dev/null; then
      show_log "$logfile"; fail "$what: the launch exited after $(( SECONDS - start ))s"
    fi
    if grep -q 'process has died' "$logfile" 2>/dev/null; then
      show_log "$logfile"; fail "$what: a process died after $(( SECONDS - start ))s"
    fi
    if (( SECONDS - start >= timeout_s )); then
      show_log "$logfile"; fail "$what not ready after ${timeout_s}s"
    fi
    sleep 5
  done
  log "$what ready after $(( SECONDS - start ))s"
  echo "- $what ready after $(( SECONDS - start )) s" >> "$OUT/report.md"
}

# --- Build ------------------------------------------------------------------
# set -u is relaxed while sourcing: ROS setup scripts read unset variables.
set +u
# shellcheck source=/dev/null
source /opt/ros/jazzy/setup.bash
log "building the workspace"
(cd "$WS" && colcon build --symlink-install --event-handlers console_cohesion+) \
  > "$OUT/colcon_build.log" 2>&1 || fail "colcon build failed (see colcon_build.log)"
# shellcheck source=/dev/null
source "$WS/install/setup.bash"
set -u

NS="$(python3 -c 'import sys, yaml; print(yaml.safe_load(open(sys.argv[1]))["system"]["ros2"]["namespace"])' "$ROBOT_YAML")"
log "robot namespace: $NS"

# --- Simulation ---------------------------------------------------------------
# setsid gives each launch its own process group, so cleanup stops all of it.
setsid ros2 launch bird_nose_bringup sim.launch.py headless:="$SIM_HEADLESS" robot_yaml:="$ROBOT_YAML" \
  > "$OUT/sim.log" 2>&1 &
PIDS+=($!)

sim_ready() {
  timeout 8 ros2 topic echo /clock --once &&
    timeout 20 ros2 topic list --no-daemon | grep -x "/$NS/platform/odom/filtered"
}
wait_for "simulation clock and odometry" "$SIM_TIMEOUT_S" "${PIDS[0]}" "$OUT/sim.log" sim_ready

# --- Nav2 with SLAM -------------------------------------------------------------
setsid ros2 launch bird_nose_bringup nav2.launch.py > "$OUT/nav2.log" 2>&1 &
PIDS+=($!)

nav2_ready() {
  timeout 10 ros2 lifecycle get "/$NS/bt_navigator" | grep '^active' &&
    timeout 10 ros2 topic echo "/$NS/map" --once
}
wait_for "Nav2 active and SLAM map published" "$NAV2_TIMEOUT_S" "${PIDS[1]}" "$OUT/nav2.log" nav2_ready

# --- One goal ---------------------------------------------------------------------
GOAL="{pose: {header: {frame_id: map}, pose: {position: {x: $GOAL_X, y: $GOAL_Y, z: 0.0}, orientation: {w: 1.0}}}}"
# Send the goal once; prints Nav2's final status (empty if there was none).
send_goal() {
  local goal_log="$1"
  timeout "$GOAL_TIMEOUT_S" ros2 action send_goal "/$NS/navigate_to_pose" \
    nav2_msgs/action/NavigateToPose "$GOAL" > "$goal_log" 2>&1 || true
  sed -n 's/^Goal finished with status: //p' "$goal_log" | tail -n 1
}

log "sending goal x=$GOAL_X y=$GOAL_Y"
start=$SECONDS
status="$(send_goal "$OUT/goal.log")"

elapsed=$(( SECONDS - start ))
if [[ "$status" == "SUCCEEDED" ]]; then
  log "PASS: goal reached in ${elapsed}s"
  echo "- Result: **PASS**, goal reached in ${elapsed} s" >> "$OUT/report.md"
else
  # Nav2's log says why a goal was aborted (planner, controller, costmap).
  show_log "$OUT/goal.log"
  show_log "$OUT/nav2.log"
  if [[ -n "$status" ]]; then
    fail "goal finished with status $status after ${elapsed}s (see nav2.log)"
  else
    fail "no result within ${GOAL_TIMEOUT_S}s (see goal.log and nav2.log)"
  fi
fi
