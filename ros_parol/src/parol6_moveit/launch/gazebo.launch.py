import os

import xacro
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, RegisterEventHandler
from launch.event_handlers import OnProcessExit
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node


def generate_launch_description():
    # 1. Expand the xacro -> URDF (sim_mode=gz selects gz_ros2_control hardware)
    moveit_pkg_share = get_package_share_directory('parol6_moveit')
    xacro_file = os.path.join(moveit_pkg_share, 'config', 'parol6.urdf.xacro')
    initial_positions_file = os.path.join(
        moveit_pkg_share, 'config', 'initial_positions.yaml'
    )
    robot_description_xml = xacro.process_file(
        xacro_file,
        mappings={
            'sim_mode': 'gz',
            'initial_positions_file': initial_positions_file,
        },
    ).toxml()
    robot_description = {'robot_description': robot_description_xml}

    # 2. Start Gazebo Sim (Harmonic) with an empty world
    gz_sim_share = get_package_share_directory('ros_gz_sim')
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gz_sim_share, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': '-r empty.sdf'}.items(),
    )

    # 3. Publish /robot_description and TF from joint states
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[robot_description, {'use_sim_time': True}],
    )

    # 4. Spawn the robot in Gazebo from /robot_description
    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-name', 'parol6', '-topic', 'robot_description'],
        output='screen',
    )

    # 5. ros2_control spawners (must run after the model is in Gazebo so the
    #    gz_ros2_control plugin has loaded the controller_manager).
    joint_state_broadcaster_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'joint_state_broadcaster',
            '--controller-manager', '/controller_manager',
        ],
        output='screen',
    )
    arm_group_controller_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=[
            'arm_group_controller',
            '--controller-manager', '/controller_manager',
        ],
        output='screen',
    )

    # 6. Bridge the simulation clock from Gazebo to ROS
    clock_bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock'],
        output='screen',
    )

    return LaunchDescription([
        gazebo_launch,
        robot_state_publisher,
        spawn_entity,
        clock_bridge,
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=spawn_entity,
                on_exit=[joint_state_broadcaster_spawner],
            )
        ),
        RegisterEventHandler(
            event_handler=OnProcessExit(
                target_action=joint_state_broadcaster_spawner,
                on_exit=[arm_group_controller_spawner],
            )
        ),
    ])
