"""RViz for the Bird Nose robot, using Clearpath's navigation view."""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
import yaml


def default_robot_yaml():
    ws = os.environ.get('BIRD_NOSE_WS', '/workspaces/bird-nose')
    return os.path.join(ws, 'config', 'robots', 'husky-a200', 'robot.yaml')


def robot_namespace(robot_yaml):
    with open(robot_yaml) as f:
        return yaml.safe_load(f)['system']['ros2']['namespace']


def _launch_rviz(context):
    namespace = LaunchConfiguration('namespace').perform(context) or robot_namespace(
        LaunchConfiguration('robot_yaml').perform(context))
    view = os.path.join(get_package_share_directory('clearpath_viz'), 'launch',
                        'view_navigation.launch.py')
    return [IncludeLaunchDescription(
        PythonLaunchDescriptionSource(view),
        launch_arguments={
            'namespace': namespace,
            'use_sim_time': LaunchConfiguration('use_sim_time').perform(context),
        }.items())]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('robot_yaml', default_value=default_robot_yaml()),
        DeclareLaunchArgument('namespace', default_value='',
                              description='Defaults to the namespace in robot.yaml'),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        OpaqueFunction(function=_launch_rviz),
    ])
