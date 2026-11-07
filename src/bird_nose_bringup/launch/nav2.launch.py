"""
Nav2 with SLAM for the simulated robot.

Uses Clearpath's Nav2 demos against the setup folder written by
sim.launch.py, with simulation time.

Clearpath's demos default to a 2D lidar scan (sensors/lidar2d_0/scan). Bird
Nose has only a 3D lidar, so when robot.yaml lists no 2D lidar this file
points Nav2 and SLAM at the Ouster's scan (sensors/lidar3d_0/scan) instead.
"""
import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
import yaml


def default_setup_path():
    path = os.environ.get('BIRD_NOSE_SIM_SETUP', os.path.expanduser('~/.bird_nose/sim_setup/'))
    return path if path.endswith('/') else path + '/'


def default_scan_topic(robot_yaml):
    """Return the scan topic Nav2 should use, or '' to keep Clearpath's default."""
    with open(robot_yaml) as f:
        config = yaml.safe_load(f)
    namespace = config['system']['ros2']['namespace']
    sensors = config.get('sensors') or {}
    if sensors.get('lidar2d'):
        return ''
    if sensors.get('lidar3d'):
        return f'/{namespace}/sensors/lidar3d_0/scan'
    return ''


def _launch_nav(context):
    share = get_package_share_directory('clearpath_nav2_demos')
    setup_path = LaunchConfiguration('setup_path').perform(context)
    robot_yaml = os.path.join(setup_path, 'robot.yaml')
    if not os.path.isfile(robot_yaml):
        raise RuntimeError(
            f'{robot_yaml} not found. Start the simulation first: '
            'sim.launch.py copies robot.yaml there.')
    args = {
        'setup_path': setup_path,
        'use_sim_time': LaunchConfiguration('use_sim_time').perform(context),
    }
    scan_topic = LaunchConfiguration('scan_topic').perform(context)
    scan_topic = scan_topic or default_scan_topic(robot_yaml)
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
        DeclareLaunchArgument('setup_path', default_value=default_setup_path(),
                              description='Folder sim.launch.py writes generated files to'),
        DeclareLaunchArgument('use_sim_time', default_value='true',
                              description='Use the /clock topic instead of wall time'),
        DeclareLaunchArgument('slam', default_value='true',
                              description='Build a map with SLAM while navigating'),
        DeclareLaunchArgument('scan_topic', default_value='',
                              description='Scan topic; empty picks one from robot.yaml'),
        OpaqueFunction(function=_launch_nav),
    ])
