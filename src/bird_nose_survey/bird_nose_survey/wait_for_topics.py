"""
Wait until messages arrive on topics, then exit.

    ros2 run bird_nose_survey wait_for_topics [--timeout S] TOPIC [TOPIC ...]

Exits with status 0 once at least one message has arrived on every topic,
or 1 after the timeout (wall-clock seconds). scenario.launch.py uses it to
start Nav2 only after the simulation is publishing its clock and odometry,
the same check the Compose health check makes.
"""
import argparse
import os
import sys
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from rclpy.utilities import remove_ros_args
from rosidl_runtime_py.utilities import get_message


def wait_for_topics(node, topics, timeout_s):
    """Return the topics that produced no message within timeout_s seconds."""
    pending = set(topics)
    subscriptions = {}
    deadline = time.monotonic() + timeout_s

    def received(topic):
        return lambda _msg: pending.discard(topic)

    while pending and time.monotonic() < deadline:
        types = dict(node.get_topic_names_and_types())
        for topic in pending - subscriptions.keys():
            if topic in types:
                # Best effort matches both reliable and best-effort publishers.
                subscriptions[topic] = node.create_subscription(
                    get_message(types[topic][0]), topic, received(topic),
                    qos_profile_sensor_data)
        rclpy.spin_once(node, timeout_sec=0.5)
    return sorted(pending)


def main(args=None):
    """Parse arguments, wait, and exit 0 when every topic has published."""
    parser = argparse.ArgumentParser(description=__doc__.split('\n\n')[0])
    parser.add_argument('topics', nargs='+', help='fully qualified topic names')
    parser.add_argument('--timeout', type=float, default=300.0,
                        help='seconds to wait before giving up (default 300)')
    options = parser.parse_args(remove_ros_args(args or sys.argv)[1:])

    rclpy.init(args=args)
    node = Node(f'wait_for_topics_{os.getpid()}')
    start = time.monotonic()
    try:
        missing = wait_for_topics(node, options.topics, options.timeout)
    except KeyboardInterrupt:
        missing = options.topics
    finally:
        node.destroy_node()
        rclpy.try_shutdown()
    if missing:
        print(f'No message within {options.timeout:g} s on: {", ".join(missing)}', file=sys.stderr)
        sys.exit(1)
    print(f'Messages arrived on all {len(options.topics)} topics after '
          f'{time.monotonic() - start:.0f} s')
    sys.exit(0)


if __name__ == '__main__':
    main()
