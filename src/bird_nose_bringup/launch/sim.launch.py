"""
Simulated Husky A200 in Gazebo Harmonic.

Copies the repository's robot.yaml into a scratch setup folder (Clearpath's
generators write files next to robot.yaml, which must not land in Git), then
starts Clearpath's simulation from that folder.

For example, to start the warehouse world with RViz, run
ros2 launch bird_nose_bringup sim.launch.py world:=warehouse rviz:=true
"""
import os
import shutil

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration


def default_robot_yaml():
    ws = os.environ.get('BIRD_NOSE_WS', '/workspaces/bird-nose')
    return os.path.join(ws, 'config', 'robots', 'husky-a200', 'robot.yaml')


def default_setup_path():
    path = os.environ.get('BIRD_NOSE_SIM_SETUP', os.path.expanduser('~/.bird_nose/sim_setup/'))
    return path if path.endswith('/') else path + '/'


def _launch_sim(context):
    robot_yaml = LaunchConfiguration('robot_yaml').perform(context)
    setup_path = LaunchConfiguration('setup_path').perform(context)
    if not setup_path.endswith('/'):
        setup_path += '/'
    os.makedirs(setup_path, exist_ok=True)
    shutil.copyfile(robot_yaml, os.path.join(setup_path, 'robot.yaml'))

    sim_launch = os.path.join(
        get_package_share_directory('clearpath_gz'), 'launch', 'simulation.launch.py')
    args = {'setup_path': setup_path}
    for name in ('world', 'rviz', 'headless', 'x', 'y', 'yaw'):
        args[name] = LaunchConfiguration(name).perform(context)
    return [IncludeLaunchDescription(
        PythonLaunchDescriptionSource(sim_launch), launch_arguments=args.items())]


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('robot_yaml', default_value=default_robot_yaml(),
                              description='Clearpath robot.yaml to simulate'),
        DeclareLaunchArgument('setup_path', default_value=default_setup_path(),
                              description='Scratch folder for generated files'),
        DeclareLaunchArgument('world', default_value='warehouse',
                              description='Gazebo world name from clearpath_gz'),
        DeclareLaunchArgument('rviz', default_value='false',
                              description='Also open the Clearpath RViz view'),
        DeclareLaunchArgument('headless', default_value='false',
                              description='Run Gazebo without its window (true/false)'),
        DeclareLaunchArgument('x', default_value='0.0',
                              description='Spawn position along the world x axis, metres'),
        DeclareLaunchArgument('y', default_value='0.0',
                              description='Spawn position along the world y axis, metres'),
        DeclareLaunchArgument('yaw', default_value='0.0',
                              description='Spawn heading about the z axis, radians'),
        OpaqueFunction(function=_launch_sim),
    ])
