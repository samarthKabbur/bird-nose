#!/usr/bin/env bash
# Run one scenario and judge it: build, launch scenario.launch.py, then
# evaluate the recording with evaluate_run.
#
# Runs inside the dev container:
#
#   tools/ci/run_scenario.sh                        # orchard_nav_survey, with the Gazebo window
#   tools/ci/run_scenario.sh orchard_nav_survey
#   SIM_HEADLESS=true tools/ci/run_scenario.sh      # without the window (needs GPU=1 on hero)
#   SEED=7 tools/ci/run_scenario.sh                 # override the scenario's seed
#
# The launch log goes to data/reports/scenario_logs/<UTC time>_<scenario>.log,
# the recording to data/bags/, and the report to data/reports/<recording>/.
# Exit status is evaluate_run's: 0 pass, 1 fail, 2 could not evaluate.
#
# Safety: refuses to run on ROS domain 0, with discovery wider than
# localhost, or while other nodes are running on the same domain.
set -euo pipefail

SCENARIO="${1:-orchard_nav_survey}"
SIM_HEADLESS="${SIM_HEADLESS:-false}"
WS="${BIRD_NOSE_WS:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"
LOGS="$WS/data/reports/scenario_logs"

log() { echo "[run_scenario $(date -u +%H:%M:%S)] $*"; }

if [[ "${ROS_DOMAIN_ID:-0}" == "0" ]]; then
  echo "Refusing to run: ROS_DOMAIN_ID is 0 (the physical robot's domain) or unset." >&2
  exit 2
fi
if [[ "${ROS_AUTOMATIC_DISCOVERY_RANGE:-}" != "LOCALHOST" ]]; then
  echo "Refusing to run: ROS_AUTOMATIC_DISCOVERY_RANGE must be LOCALHOST." >&2
  exit 2
fi

set +u  # ROS setup scripts read unset variables
# shellcheck source=/dev/null
source /opt/ros/jazzy/setup.bash
log "building the workspace"
(cd "$WS" && colcon build --symlink-install --event-handlers console_cohesion+ > /dev/null) \
  || { echo "colcon build failed; run it by hand to see why." >&2; exit 2; }
# shellcheck source=/dev/null
source "$WS/install/setup.bash"
set -u

others="$(timeout 20 ros2 node list --no-daemon 2>/dev/null || true)"
if [[ -n "$others" ]]; then
  echo "$others" | head -n 10
  echo "ROS domain $ROS_DOMAIN_ID already has running nodes (above). Stop them, or run" \
       "with another domain, e.g. ROS_DOMAIN_ID=44 $0" >&2
  exit 2
fi

mkdir -p "$LOGS"
launch_log="$LOGS/$(date -u +%Y%m%dT%H%M%SZ)_${SCENARIO//[^A-Za-z0-9_-]/_}.log"
marker="$(mktemp)"
log "running scenario $SCENARIO (headless: $SIM_HEADLESS); launch log: ${launch_log#"$WS"/}"
set +e
ros2 launch bird_nose_bringup scenario.launch.py scenario:="$SCENARIO" \
  headless:="$SIM_HEADLESS" seed:="${SEED:-}" > "$launch_log" 2>&1
launch_status=$?
set -e
grep -E 'Scenario ending|Scenario [a-z_]+ \(seed' "$launch_log" || true
if (( launch_status != 0 )); then
  log "ros2 launch exited with status $launch_status; last lines of the log:"
  tail -n 30 "$launch_log"
fi

# The recording this run made: the newest one for this scenario, newer than the marker.
name="$(basename "$SCENARIO" .yaml)"
bag="$(find "$WS/data/bags" -maxdepth 1 -type d -name "*_scenario-${name}" -newer "$marker" \
       2>/dev/null | sort | tail -n 1)"
rm -f "$marker"
if [[ -z "$bag" ]]; then
  log "no recording was made; see the launch log"
  exit 2
fi

log "evaluating ${bag#"$WS"/}"
set +e
ros2 run bird_nose_evaluation evaluate_run "$bag" --scenario "$SCENARIO"
status=$?
set -e
exit "$status"
