"""
Nav2 with SLAM for the simulated robot, with Bird Nose's parameters.

Starts SLAM through Clearpath's slam.launch.py, then Nav2 through Nav2's own
navigation_launch.py, both against the setup folder written by sim.launch.py
and with simulation time.

Start-up is staged so it does not depend on timing:

1. SLAM starts with its own autostart off; a Nav2 lifecycle manager
   (lifecycle_manager_slam_toolbox) configures and activates slam_toolbox
   and the map saver, waiting for each to be ready. slam_toolbox's launch
   file would otherwise send one configure request at start-up and give up
   if the node was still busy, leaving SLAM off for the whole run
   (2026-11-09, headless on hero).
2. Nav2 starts once SLAM publishes a map, so its global costmap finds the
   map frame as soon as it activates. Without SLAM, Nav2 starts at once.

Nav2's parameters are Clearpath's for this platform, plus Bird Nose's
changes in bird_nose_navigation/config/nav2_overrides.yaml (merged by
bird_nose_navigation.nav2_params). This file replaces the include of
Clearpath's nav2.launch.py, which always loads Clearpath's file unchanged;
it starts the same Nav2 nodes in the same namespace.

Clearpath's demos default to a 2D lidar scan (sensors/lidar2d_0/scan). Bird
Nose has only a 3D lidar, so when robot.yaml lists no 2D lidar this file
points Nav2 and SLAM at the Ouster's scan (sensors/lidar3d_0/scan) instead.
"""
import os

from ament_index_python.packages import get_package_share_directory
from bird_nose_navigation.nav2_params import build_params, load_yaml, write_params
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, GroupAction, IncludeLaunchDescription,
                            LogInfo, OpaqueFunction, RegisterEventHandler)
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node, PushRosNamespace


def default_setup_path():
    path = os.environ.get('BIRD_NOSE_SIM_SETUP', os.path.expanduser('~/.bird_nose/sim_setup/'))
    return path if path.endswith('/') else path + '/'


def default_overrides():
    share = get_package_share_directory('bird_nose_navigation')
    return os.path.join(share, 'config', 'nav2_overrides.yaml')


def default_scan_topic(robot):
    """Return the scan topic Nav2 and SLAM should use for this robot.yaml."""
    namespace = robot['system']['ros2']['namespace']
    sensors = robot.get('sensors') or {}
    if not sensors.get('lidar2d') and sensors.get('lidar3d'):
        return f'/{namespace}/sensors/lidar3d_0/scan'
    return f'/{namespace}/sensors/lidar2d_0/scan'  # Clearpath's default


def platform_model(robot):
    """Return the platform model, such as 'a200', from the serial number."""
    return str(robot['serial_number']).split('-')[0]


def is_diff_drive(robot):
    """Return False only for a platform configured to drive as omnidirectional."""
    drivetrain = (robot.get('platform') or {}).get('drivetrain') or {}
    return 'omni' not in str(drivetrain.get('control', '')).lower()


def _launch_nav(context):
    setup_path = LaunchConfiguration('setup_path').perform(context)
    robot_yaml = os.path.join(setup_path, 'robot.yaml')
    if not os.path.isfile(robot_yaml):
        raise RuntimeError(
            f'{robot_yaml} not found. Start the simulation first: '
            'sim.launch.py copies robot.yaml there.')
    robot = load_yaml(robot_yaml)
    namespace = robot['system']['ros2']['namespace']
    use_sim_time = LaunchConfiguration('use_sim_time').perform(context)
    slam = LaunchConfiguration('slam').perform(context).lower() == 'true'
    scan_topic = LaunchConfiguration('scan_topic').perform(context) or default_scan_topic(robot)

    clearpath_share = get_package_share_directory('clearpath_nav2_demos')
    actions = []
    if slam:
        actions.append(IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(clearpath_share, 'launch', 'slam.launch.py')),
            launch_arguments={'setup_path': setup_path, 'use_sim_time': use_sim_time,
                              'scan_topic': scan_topic, 'autostart': 'false',
                              'use_lifecycle_manager': 'false'}.items()))
        # Brings slam_toolbox and the map saver up, retrying until each is ready.
        # bond_timeout 0 turns off the heartbeat these two nodes do not provide.
        actions.append(Node(
            package='nav2_lifecycle_manager', executable='lifecycle_manager',
            name='lifecycle_manager_slam_toolbox', namespace=namespace, output='screen',
            parameters=[{'autostart': True, 'node_names': ['slam_toolbox', 'map_saver'],
                         'bond_timeout': 0.0, 'use_sim_time': use_sim_time == 'true'}]))

    clearpath_file = os.path.join(clearpath_share, 'config', platform_model(robot), 'nav2.yaml')
    overrides_file = LaunchConfiguration('nav2_overrides').perform(context)
    # With SLAM, the global costmap is Clearpath's 20 m window around the
    # robot, as Clearpath intends. A costmap sized to the SLAM map only covers
    # what the lidar has already hit; on open ground that is a few metres, so
    # every survey goal fell outside it and Nav2 rejected it at once (orchard
    # edge run, 2026-11-09). With a saved map (slam:=false), the costmap
    # covers the whole map.
    params, skipped = build_params(load_yaml(clearpath_file), load_yaml(overrides_file),
                                   scan_topic, diff_drive=is_diff_drive(robot),
                                   rolling_global_costmap=slam)
    params_file = write_params(params, namespace)
    actions.append(LogInfo(msg=f'Nav2 parameters: {clearpath_file} + {overrides_file} '
                               f'-> {params_file}'))
    for key in skipped:
        actions.append(LogInfo(msg=f'Clearpath launch setting not in {clearpath_file}, '
                                   f'skipped: {key}'))

    navigation = os.path.join(get_package_share_directory('nav2_bringup'), 'launch',
                              'navigation_launch.py')
    nav2 = GroupAction([
        PushRosNamespace(namespace),
        IncludeLaunchDescription(
            PythonLaunchDescriptionSource(navigation),
            launch_arguments={
                'namespace': namespace,
                'use_sim_time': use_sim_time,
                'params_file': params_file,
                'autostart': 'true',
                'use_composition': 'False',
                'use_respawn': 'false',
                'log_level': 'info',
            }.items()),
    ])
    if not slam:
        return actions + [nav2]

    wait_for_map = Node(
        package='bird_nose_survey', executable='wait_for_topics', output='screen',
        arguments=['--timeout', '180', f'/{namespace}/map'])

    def after_map(event, _context):
        if event.returncode != 0:
            return [LogInfo(msg='SLAM published no map within 180 s; starting Nav2 anyway, '
                                'but expect it to fail to activate'), nav2]
        return [LogInfo(msg='SLAM map received; starting Nav2'), nav2]

    return actions + [wait_for_map, RegisterEventHandler(
        OnProcessExit(target_action=wait_for_map, on_exit=after_map))]


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
        DeclareLaunchArgument('nav2_overrides', default_value=default_overrides(),
                              description="Bird Nose's changes to Clearpath's Nav2 parameters"),
        OpaqueFunction(function=_launch_nav),
    ])
