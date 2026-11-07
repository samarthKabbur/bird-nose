"""
Placeholder autonomy node: publishes a heartbeat so the pipeline can be tested.

Real Bird Nose algorithms replace this behind stable topic and action
interfaces in Phase 4.
"""
from rcl_interfaces.msg import FloatingPointRange, ParameterDescriptor
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


def status_text(count):
    """Return the heartbeat message for a given tick."""
    return f'bird_nose_algorithms alive ({count})'


class StatusNode(Node):
    """
    Publish a heartbeat on ~/status (std_msgs/String).

    Parameters are self-describing: run
    ``ros2 param describe /bird_nose_status period_s`` to see the description
    and valid range below.
    """

    def __init__(self):
        super().__init__('bird_nose_status')
        period_s = self.declare_parameter(
            'period_s', 1.0,
            ParameterDescriptor(
                description='Seconds between heartbeat messages',
                floating_point_range=[FloatingPointRange(from_value=0.1, to_value=60.0)],
                read_only=True)).value
        self._count = 0
        self._pub = self.create_publisher(String, '~/status', 10)
        self.create_timer(period_s, self._tick)

    def _tick(self):
        self._count += 1
        self._pub.publish(String(data=status_text(self._count)))


def main(args=None):
    """Run the node until interrupted."""
    rclpy.init(args=args)
    node = StatusNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.try_shutdown()


if __name__ == '__main__':
    main()
