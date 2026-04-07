import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch_ros.actions import Node

def generate_launch_description():
    pkg_name = 'parol6'
    
    # Get the paths to the packages
    pkg_share = get_package_share_directory(pkg_name)

    # NEW: Get the Gazebo Sim (Harmonic) share directory
    gz_sim_share = get_package_share_directory('ros_gz_sim')
    
    # Path to your URDF file
    urdf_file_path = os.path.join(pkg_share, 'urdf', 'parol6.urdf')

    # 1. Start Gazebo (Empty World)
    gazebo_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(gz_sim_share, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': '-r empty.sdf'}.items(), 
    )

    # 2. Publish the Static Transform (base_footprint to base_link)
    # Note: ROS 2 uses tf2_ros, and the argument order is slightly different
    static_tf_node = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        arguments=['--x', '0', '--y', '0', '--z', '0', 
                   '--frame-id', 'base_footprint', 
                   '--child-frame-id', 'base_link'],
    )

    # 3. Spawn the URDF model in Gazebo
    # Note: spawn_model is now spawn_entity.py
    spawn_model_node = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=[
            '-name', 'parol6',
            '-file', urdf_file_path,
            '-world','empty',
            '-z', '0.1'
        ],
        output='screen'
    )
    # 4. The Bridge
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=['/clock@rosgraph_msgs/msg/Clock@gz.msgs.Clock'],
        output= 'screen'
    )

    # Note: The fake_joint_calibration rostopic hack from ROS 1 is generally 
    # not used or needed in ROS 2 control systems, so it is omitted here.

    return LaunchDescription([
        gazebo_launch,
        static_tf_node,
        spawn_model_node,
        bridge
    ])