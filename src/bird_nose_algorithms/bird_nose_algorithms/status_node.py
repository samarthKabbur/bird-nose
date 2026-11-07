"""
Placeholder autonomy node: publishes a heartbeat so the pipeline can be tested.

Real Bird Nose algorithms replace this behind stable topic and action
interfaces in Phase 4.
"""
import rclpy
from rclpy.node import Node
from std_msgs.msg import String


def status_text(count):
    """Return the heartbeat message for a given tick."""
    return f'bird_nose_algorithms alive ({count})'


class StatusNode(Node):
    """Publish a heartbeat on ~/status once per second."""

    def __init__(self):
        super().__init__('bird_nose_status')
        self._count = 0
        self._pub = self.create_publisher(String, '~/status', 10)
        self.create_timer(1.0, self._tick)

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
