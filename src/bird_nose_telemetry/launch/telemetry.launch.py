"""
Foxglove Bridge for live dashboards.

Listens on 127.0.0.1 by default so it is never exposed on a network. From
another computer, use an SSH tunnel:
    ssh -L 8765:localhost:8765 <user>@<this-computer>
then open Foxglove and connect to ws://localhost:8765.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription
from launch.launch_description_sources import AnyLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def generate_launch_description():
    bridge = os.path.join(get_package_share_directory('foxglove_bridge'), 'launch',
                          'foxglove_bridge_launch.xml')
    return LaunchDescription([
        DeclareLaunchArgument('address', default_value='127.0.0.1',
                              description='Listen address; keep 127.0.0.1, use SSH'),
        DeclareLaunchArgument('port', default_value='8765',
                              description='WebSocket port for Foxglove'),
        IncludeLaunchDescription(
            AnyLaunchDescriptionSource(bridge),
            launch_arguments={
                'address': LaunchConfiguration('address'),
                'port': LaunchConfiguration('port'),
            }.items()),
    ])
