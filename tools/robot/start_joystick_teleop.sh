#!/usr/bin/env bash

set -Eeo pipefail

SETUP_FILE="${CLEARPATH_SETUP_FILE:-/etc/clearpath/setup.bash}"
ROBOT_NAMESPACE="${CLEARPATH_ROBOT_NAMESPACE:-/Nuvo_7100VTC_Series}"
ROBOT_NAMESPACE="/${ROBOT_NAMESPACE#/}"

fail() {
  echo "Error: $*" >&2
  exit 1
}

if [[ "$(id -un)" != "robot" ]]; then
  fail "run this script inside the container as the 'robot' user."
fi

[[ -f "$SETUP_FILE" ]] || fail "$SETUP_FILE was not found."

# shellcheck source=/dev/null
source "$SETUP_FILE"

# ROS setup is now loaded; enable unset-variable checking for this script's
# remaining logic.
set -u

command -v ros2 >/dev/null 2>&1 || fail "ROS 2 is unavailable after sourcing $SETUP_FILE."

TELEOP_NODE="${ROBOT_NAMESPACE}/teleop_twist_joy_node"
JOY_TOPIC="${ROBOT_NAMESPACE}/joy_teleop/joy"
TELEOP_TOPIC="${ROBOT_NAMESPACE}/joy_teleop/cmd_vel"
OUTPUT_TOPIC="${ROBOT_NAMESPACE}/platform/cmd_vel"
ESTOP_TOPIC="${ROBOT_NAMESPACE}/platform/emergency_stop"
CONTROLLER_SERVICE="${ROBOT_NAMESPACE}/controller_manager/list_controllers"

echo "Checking Clearpath joystick teleoperation for ${ROBOT_NAMESPACE}..."

nodes="$(timeout 10 ros2 node list 2>/dev/null)" || \
  fail "could not read the ROS node list."

grep -Fxq "$TELEOP_NODE" <<<"$nodes" || \
  fail "$TELEOP_NODE is not running. Restart the Clearpath robot container instead of launching a duplicate teleop node."

for topic in "$JOY_TOPIC" "$TELEOP_TOPIC" "$OUTPUT_TOPIC" "$ESTOP_TOPIC"; do
  topic_info="$(timeout 10 ros2 topic info "$topic" 2>/dev/null)" || \
    fail "required topic $topic is unavailable."

  if ! grep -Eq 'Publisher count: [1-9][0-9]*' <<<"$topic_info"; then
    fail "required topic $topic has no publisher."
  fi
done

controller_output="$(
  timeout 10 ros2 service call \
    "$CONTROLLER_SERVICE" \
    controller_manager_msgs/srv/ListControllers '{}' 2>&1
)" || fail "could not query the controller manager."

grep -Fq "name='platform_velocity_controller', state='active'" \
  <<<"$controller_output" || \
  fail "platform_velocity_controller is not active. Keep the physical Stop engaged."

grep -Fq "name='joint_state_broadcaster', state='active'" \
  <<<"$controller_output" || \
  fail "joint_state_broadcaster is not active. Keep the physical Stop engaged."

if ! timeout 6 ros2 topic echo "$JOY_TOPIC" \
    --qos-reliability best_effort --once >/dev/null 2>&1; then
  fail "no joystick message was received. Wake the F710, select X mode, turn the MODE light off, and rerun this script."
fi

estop_output="$(
  timeout 6 ros2 topic echo "$ESTOP_TOPIC" \
    --qos-reliability best_effort --once 2>/dev/null
)" || fail "no motion-stop state was received."

echo
echo "Joystick teleoperation is running."
echo "  Left stick up/down: forward/backward"
echo "  Left stick left/right: turn"
echo "  Hold LB: normal speed"
echo "  Hold RB: turbo speed (avoid until experienced)"
echo "  F710 rear switch: X"
echo "  MODE light: off"
echo

if grep -Eq 'data:[[:space:]]*true' <<<"$estop_output"; then
  echo "Motion status: PHYSICAL STOP ENGAGED (data: true)"
  echo "Set the controller down, center both sticks, release LB/RB, and only then twist the red Stop button outward."
elif grep -Eq 'data:[[:space:]]*false' <<<"$estop_output"; then
  echo "Motion status: ENABLED (data: false)"
  echo "The Husky can move now. Keep a person beside the physical Stop and hold LB only for normal driving."
else
  fail "the motion-stop message did not contain a recognized true/false state."
fi

echo
echo "Warning: an F710 disconnect may leave the previous command active. Keep the physical Stop accessible."
