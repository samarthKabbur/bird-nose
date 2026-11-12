"""
Survey node: drive a route through Nav2, stopping at each survey stop.

The route comes in as parameters (map frame). The node waits until Nav2 is
active and SLAM has published a map, sends NavigateToPose goals stop by
stop (retrying a failed stop up to max_attempts times), waits at each stop
it reaches, and reports every step as a SurveyEvent on
bird_nose/survey_events.
When the survey is over it exits, which lets scenario.launch.py shut the
run down.

Step 4.1 only waits at each stop. Step 4.2 replaces the wait with a
RecordSample request to the recorder.
"""
import sys
import time

from action_msgs.msg import GoalStatus
from bird_nose_interfaces.msg import SurveyEvent
from bird_nose_survey.route import stops_along_route, yaw_to_quaternion
from geometry_msgs.msg import Pose
from lifecycle_msgs.srv import GetState
from nav2_msgs.action import NavigateToPose
from nav_msgs.msg import OccupancyGrid
from rcl_interfaces.msg import FloatingPointRange, IntegerRange, ParameterDescriptor
import rclpy
from rclpy.action import ActionClient
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.parameter import Parameter
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy

STATUS_NAMES = {
    GoalStatus.STATUS_SUCCEEDED: 'SUCCEEDED',
    GoalStatus.STATUS_ABORTED: 'ABORTED',
    GoalStatus.STATUS_CANCELED: 'CANCELED',
}

# Late subscribers, such as a recorder started after the survey, still get
# every event.
EVENT_QOS = QoSProfile(depth=100, reliability=ReliabilityPolicy.RELIABLE,
                       durability=DurabilityPolicy.TRANSIENT_LOCAL)


def _float_param(description, low, high):
    """Return a read-only descriptor for a floating-point parameter."""
    return ParameterDescriptor(
        description=description, read_only=True,
        floating_point_range=[FloatingPointRange(from_value=low, to_value=high)])


class SurveyNode(Node):
    """Drives the survey route and publishes its progress."""

    def __init__(self):
        super().__init__('survey')
        self.declare_parameter(
            'route_xy', Parameter.Type.DOUBLE_ARRAY,
            ParameterDescriptor(
                description='Route in the map frame as [x0, y0, x1, y1, ...], metres. '
                            'The robot starts at the first point.',
                read_only=True))
        self.declare_parameter(
            'stop_spacing_m', 6.096,
            _float_param('Distance between stops along the route, metres (6.096 m = 20 ft)',
                         0.5, 100.0))
        self.declare_parameter(
            'dwell_s', 30.0,
            _float_param('Time to stay at each stop reached, simulation seconds', 0.0, 600.0))
        self.declare_parameter(
            'goal_timeout_s', 180.0,
            _float_param('Wall-clock seconds allowed to reach one stop before giving up',
                         10.0, 1800.0))
        self.declare_parameter(
            'max_attempts', 2,
            ParameterDescriptor(
                description='Goals sent to one stop before it counts as failed (1 = no retry)',
                read_only=True,
                integer_range=[IntegerRange(from_value=1, to_value=5, step=1)]))
        self.declare_parameter(
            'nav2_timeout_s', 300.0,
            _float_param('Wall-clock seconds to wait for Nav2 to become active', 10.0, 1800.0))

        self._events = self.create_publisher(SurveyEvent, 'bird_nose/survey_events', EVENT_QOS)
        self._navigate = ActionClient(self, NavigateToPose, 'navigate_to_pose')
        self._bt_state = self.create_client(GetState, 'bt_navigator/get_state')
        # SLAM publishes the map with transient local durability, so this gets
        # the latest map even if it was published before the subscription.
        self._have_map = False
        self.create_subscription(
            OccupancyGrid, 'map', self._on_map,
            QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE,
                       durability=DurabilityPolicy.TRANSIENT_LOCAL))

    def _on_map(self, _msg):
        self._have_map = True

    def _param(self, name):
        return self.get_parameter(name).value

    def _publish(self, event, stop_index=0, stop_count=0, target=None, detail=''):
        msg = SurveyEvent()
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.header.frame_id = 'map'
        msg.event = event
        msg.stop_index = stop_index
        msg.stop_count = stop_count
        msg.target = target or Pose()
        msg.detail = detail
        self._events.publish(msg)
        self.get_logger().info(
            f'{event} stop {stop_index + 1}/{stop_count} {detail}'.strip()
            if event not in (SurveyEvent.STARTED, SurveyEvent.FINISHED)
            else f'{event}: {stop_count} stops {detail}'.strip())

    def _wait(self, future, timeout_s):
        """Spin until future completes or timeout_s wall seconds pass; return whether it did."""
        rclpy.spin_until_future_complete(self, future, timeout_sec=timeout_s)
        return future.done()

    def wait_for_nav2(self):
        """Return True once bt_navigator is active and SLAM has published a map."""
        deadline = time.monotonic() + self._param('nav2_timeout_s')
        active = False
        while time.monotonic() < deadline:
            if not active and self._bt_state.wait_for_service(timeout_sec=2.0):
                future = self._bt_state.call_async(GetState.Request())
                active = (self._wait(future, 5.0)
                          and future.result().current_state.label == 'active'
                          and self._navigate.wait_for_server(timeout_sec=10.0))
            if active and self._have_map:
                return True
            rclpy.spin_once(self, timeout_sec=1.0)
        return False

    def _goto(self, pose):
        """Send one NavigateToPose goal; return Nav2's final status name."""
        goal = NavigateToPose.Goal()
        goal.pose.header.frame_id = 'map'
        goal.pose.header.stamp = self.get_clock().now().to_msg()
        goal.pose.pose = pose
        sent = self._navigate.send_goal_async(goal)
        if not self._wait(sent, 10.0) or not sent.result().accepted:
            return 'REJECTED'
        handle = sent.result()
        result = handle.get_result_async()
        if not self._wait(result, self._param('goal_timeout_s')):
            cancel = handle.cancel_goal_async()
            self._wait(cancel, 10.0)
            return 'TIMEOUT'
        return STATUS_NAMES.get(result.result().status, f'STATUS_{result.result().status}')

    def _dwell(self, seconds):
        """Stay put for seconds of node time (simulation time when use_sim_time is set)."""
        end = self.get_clock().now() + Duration(seconds=seconds)
        while rclpy.ok() and self.get_clock().now() < end:
            rclpy.spin_once(self, timeout_sec=0.1)

    def run(self):
        """Run the whole survey; return the process exit code."""
        flat = list(self._param('route_xy'))
        if len(flat) < 4 or len(flat) % 2:
            self.get_logger().error('route_xy needs at least two x, y pairs')
            return 2
        points = list(zip(flat[0::2], flat[1::2]))
        stops = stops_along_route(points, self._param('stop_spacing_m'))
        count = len(stops)

        self.get_logger().info('waiting for Nav2 to become active and for a SLAM map')
        if not self.wait_for_nav2():
            self._publish(SurveyEvent.FINISHED, stop_count=count,
                          detail='Nav2 never became active, or no map arrived')
            return 1

        self._publish(SurveyEvent.STARTED, stop_count=count)
        reached = 0
        for index, (x, y, yaw) in enumerate(stops):
            pose = Pose()
            pose.position.x, pose.position.y = x, y
            pose.orientation.z, pose.orientation.w = yaw_to_quaternion(yaw)
            attempts = []
            while len(attempts) < self._param('max_attempts'):
                attempts.append(self._goto(pose))
                if attempts[-1] == 'SUCCEEDED':
                    break
            history = ', '.join(attempts)
            if attempts[-1] != 'SUCCEEDED':
                self._publish(SurveyEvent.FAILED, index, count, pose, history)
                continue
            reached += 1
            self._publish(SurveyEvent.ARRIVED, index, count, pose,
                          f'attempts: {history}' if len(attempts) > 1 else '')
            dwell = self._param('dwell_s')
            self._dwell(dwell)
            self._publish(SurveyEvent.RECORDED, index, count, pose, f'waited {dwell:g} s')
        self._publish(SurveyEvent.FINISHED, stop_count=count,
                      detail=f'{reached} of {count} stops reached')
        # Give the last events a second to reach subscribers before exiting.
        flush_until = time.monotonic() + 1.0
        while rclpy.ok() and time.monotonic() < flush_until:
            rclpy.spin_once(self, timeout_sec=0.1)
        return 0


def main(args=None):
    """Run the survey node until the survey ends."""
    rclpy.init(args=args)
    node = SurveyNode()
    code = 1
    try:
        code = node.run()
    except KeyboardInterrupt:
        code = 130
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
    sys.exit(code)


if __name__ == '__main__':
    main()
