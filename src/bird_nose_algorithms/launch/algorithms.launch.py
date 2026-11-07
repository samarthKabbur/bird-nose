"""Start the Bird Nose autonomy nodes."""
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        Node(
            package='bird_nose_algorithms',
            executable='status_node',
            name='bird_nose_status',
            parameters=[{'use_sim_time': LaunchConfiguration('use_sim_time')}],
            output='screen',
        ),
    ])
