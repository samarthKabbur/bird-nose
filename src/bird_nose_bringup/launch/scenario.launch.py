"""
Run one scenario end to end: simulation, Nav2, survey, and recording.

    ros2 launch bird_nose_bringup scenario.launch.py scenario:=orchard_nav_survey

Order of events:

1. Start the simulation in the scenario's world, with the robot at its
   start pose (sim.launch.py), and start recording if record is true.
2. Wait until /clock and the robot's odometry publish (wait_for_topics).
3. Start Nav2 with SLAM (nav2.launch.py) and the survey node, with the
   scenario's route converted to the map frame.
4. When the survey node exits, shut everything down; the recorder then
   finishes its file. The scenario's timeout_s also shuts the run down.

Judge the recording afterwards with
`ros2 run bird_nose_evaluation evaluate_run <recording>`, or use
tools/ci/run_scenario.sh, which does both.

Refuses to run on ROS domain 0, the physical robot's domain.
"""
import os

from ament_index_python.packages import get_package_prefix, get_package_share_directory
from bird_nose_evaluation.scenario import find_scenario, load_scenario, route_in_map
from launch import LaunchDescription
from launch.actions import (DeclareLaunchArgument, EmitEvent, ExecuteProcess,
                            IncludeLaunchDescription, LogInfo, OpaqueFunction,
                            RegisterEventHandler, TimerAction)
from launch.event_handlers import OnProcessExit
from launch.events import Shutdown
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
import yaml


def workspace():
    return os.environ.get('BIRD_NOSE_WS', '/workspaces/bird-nose')


def default_robot_yaml():
    return os.path.join(workspace(), 'config', 'robots', 'husky-a200', 'robot.yaml')


def _shutdown(reason):
    return [LogInfo(msg=f'Scenario ending: {reason}'), EmitEvent(event=Shutdown(reason=reason))]


def _launch_scenario(context):
    if os.environ.get('ROS_DOMAIN_ID', '0') in ('', '0'):
        raise RuntimeError('ROS_DOMAIN_ID is 0 (the physical robot) or unset; '
                           'scenarios run only on a simulation domain such as 42.')
    scenario = load_scenario(find_scenario(
        LaunchConfiguration('scenario').perform(context), workspace()))
    seed = LaunchConfiguration('seed').perform(context) or str(scenario['seed'])
    headless = LaunchConfiguration('headless').perform(context)
    record = LaunchConfiguration('record').perform(context).lower() == 'true'
    robot_yaml = default_robot_yaml()
    with open(robot_yaml, encoding='utf-8') as f:
        namespace = yaml.safe_load(f)['system']['ros2']['namespace']
    bringup = get_package_share_directory('bird_nose_bringup')
    start = scenario['robot_start']

    sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(bringup, 'launch', 'sim.launch.py')),
        launch_arguments={
            'robot_yaml': robot_yaml, 'world': scenario['world'], 'headless': headless,
            'rviz': LaunchConfiguration('rviz').perform(context),
            'x': str(start['x']), 'y': str(start['y']), 'yaw': str(start['yaw']),
        }.items())

    wait_for_sim = Node(
        package='bird_nose_survey', executable='wait_for_topics', output='screen',
        arguments=['--timeout', '600', '/clock', f'/{namespace}/platform/odom/filtered'])

    nav2 = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(os.path.join(bringup, 'launch', 'nav2.launch.py')))

    route = [value for point in route_in_map(scenario) for value in point]
    survey = Node(
        package='bird_nose_survey', executable='survey', namespace=namespace, output='screen',
        parameters=[{
            'use_sim_time': True,
            'route_xy': route,
            'stop_spacing_m': scenario['survey']['stop_spacing_m'],
            'dwell_s': float(scenario['survey']['record_s']),
            'max_attempts': 2,
        }])

    def after_sim_ready(event, _context):
        if event.returncode != 0:
            return _shutdown('the simulation did not start (no /clock or odometry)')
        return [LogInfo(msg='Simulation ready; starting Nav2 and the survey'), nav2, survey]

    actions = [
        LogInfo(msg=f"Scenario {scenario['name']} (seed {seed}) from {scenario['path']}"),
        sim,
        wait_for_sim,
        RegisterEventHandler(OnProcessExit(target_action=wait_for_sim,
                                           on_exit=after_sim_ready)),
        RegisterEventHandler(OnProcessExit(
            target_action=survey, on_exit=lambda *_: _shutdown('survey finished'))),
        TimerAction(period=float(scenario['timeout_s']),
                    actions=_shutdown(f"timeout_s ({scenario['timeout_s']} s) reached")),
    ]
    if record:
        # record_run stops ros2 bag cleanly when the launch sends it SIGINT, then
        # writes run_metadata.yaml; allow time for both before escalating. It is
        # started directly rather than through `ros2 run`, which would not pass
        # the launch's SIGINT on to it.
        record_run = os.path.join(get_package_prefix('bird_nose_telemetry'), 'lib',
                                  'bird_nose_telemetry', 'record_run')
        actions.append(ExecuteProcess(
            cmd=[record_run, f"scenario-{scenario['name']}"],
            additional_env={'SCENARIO': scenario['name'], 'SEED': seed,
                            'NOTES': 'scenario.launch.py'},
            output='screen', sigterm_timeout='30', sigkill_timeout='30'))
    return actions


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('scenario', default_value='orchard_nav_survey',
                              description='Scenario name in config/scenarios/, or a file path'),
        DeclareLaunchArgument('seed', default_value='',
                              description="Random seed; empty uses the scenario's seed"),
        DeclareLaunchArgument('headless', default_value='false',
                              description='Run Gazebo without its window'),
        DeclareLaunchArgument('rviz', default_value='false',
                              description="Also open Clearpath's RViz view"),
        DeclareLaunchArgument('record', default_value='true',
                              description='Record the run to MCAP with record_run'),
        OpaqueFunction(function=_launch_scenario),
    ])
