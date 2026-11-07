"""
Nav2 with SLAM for the simulated robot (finalized in Phase 2).

Uses Clearpath's Nav2 demos against the setup folder written by
sim.launch.py, with simulation time.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def default_setup_path():
    path = os.environ.get('BIRD_NOSE_SIM_SETUP', os.path.expanduser('~/.bird_nose/sim_setup/'))
    return path if path.endswith('/') else path + '/'


def _launch_nav(context):
    share = get_package_share_directory('clearpath_nav2_demos')
    args = {
        'setup_path': LaunchConfiguration('setup_path').perform(context),
        'use_sim_time': LaunchConfiguration('use_sim_time').perform(context),
    }
    scan_topic = LaunchConfiguration('scan_topic').perform(context)
    if scan_topic:
        args['scan_topic'] = scan_topic
    actions = []
    if LaunchConfiguration('slam').perform(context).lower() == 'true':
        actions.append(IncludeLaunchDescription(
            PythonLaunchDescriptionSource(os.path.join(share, 'launch', 'slam.launch.py')),
            launch_arguments=args.items()))
    actions.append(IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(share, 'launch', 'nav2.launch.py')),
        launch_arguments=args.items()))
    return actions


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('setup_path', default_value=default_setup_path()),
        DeclareLaunchArgument('use_sim_time', default_value='true'),
        DeclareLaunchArgument('slam', default_value='true',
                              description='Build a map while navigating'),
        DeclareLaunchArgument('scan_topic', default_value='',
                              description='Override the laser scan topic'),
        OpaqueFunction(function=_launch_nav),
    ])
