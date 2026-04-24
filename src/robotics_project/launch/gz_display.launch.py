from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable
from launch.substitutions import PathJoinSubstitution
from launch_ros.actions import Node
from launch.launch_description_sources import PythonLaunchDescriptionSource
from ament_index_python.packages import get_package_share_directory
import xacro
import os
from ament_index_python.packages import get_package_prefix

def generate_launch_description():
    pkg_ros_gz_sim = get_package_share_directory('ros_gz_sim')
    pkg_lab_gazebo = get_package_share_directory('robotics_project')

    # Fix Ignition Gazebo mesh resolving (model://robotics_project/meshes/...) by adding package parent to resource path
    gazebo_resource_root = os.path.dirname(pkg_lab_gazebo)
    set_gz_sim_resource_path = SetEnvironmentVariable(name='GZ_SIM_RESOURCE_PATH', value=gazebo_resource_root)

    # Process the Xacro file to generate URDF
    xacro_file = os.path.join(pkg_lab_gazebo, 'urdf', 'arm_assembly.urdf')
    doc = xacro.parse(open(xacro_file))
    robot_description = doc.toxml()

    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_ros_gz_sim, 'launch', 'gz_sim.launch.py')
        ),
        launch_arguments={'gz_args': '-r empty.sdf'}.items(),
    )
    #Robot State Publisher node
    robot_state_publisher_node = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        parameters=[{'robot_description': robot_description}],
        output="screen"
    )
    # Joint State Publisher node
    joint_state_publisher_node = Node(
        package='joint_state_publisher',
        executable='joint_state_publisher',
        name='joint_state_publisher',
        output='screen'
    )
    # add the bridge node for mapping the topics between ROS and GZ sim
    bridge = Node(
        package='ros_gz_bridge',
        executable='parameter_bridge',
        arguments=[
            # Clock (IGN -> ROS2)
            '/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock',
            # Joint states (IGN -> ROS2)
            '/world/empty/arm_assembly/rrbot/joint_state@sensor_msgs/msg/JointState[gz.msgs.Model',
        ],
        remappings=[
            ('/world/empty/model/arm_assembly/joint_state','joint_states'),
        ],
        output='screen'
    )
    # Spawn Entity node
    spawn_entity = Node(
        package='ros_gz_sim',
        executable='create',
        arguments=['-name', 'arm_assembly', '-topic','/robot_description'],
        parameters=[{"use_sim_time": True}],

        output='screen',

    )
    # add the robot controllers for joint trajectory, armgroup and hand group controllers
    robot_controller = PathJoinSubstitution(
        [   
            pkg_lab_gazebo,
            "config",
            "joint_controller.yaml",
        ] 
    )
    # Controller Manager Spawner node to launch the joint state broadcaster
    joint_state_broadcaster_spawner = Node(
        package="controller_manager",
        executable="spawner",
        arguments=["joint_state_broadcaster", "--param-file", robot_controller, "--controller-manager-timeout", "10"],
    )
    # Controller Manager Spawner node to launch the arm group controller
    arm_controller_manager_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['arm_group_controller',"--param-file",robot_controller, "--controller-manager-timeout", "10"],
        output='screen'
    )
# Controller Manager Spawner node to launch the hand group controller
    hand_controller_manager_spawner = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['hand_group_controller', "--param-file", robot_controller, "--controller-manager-timeout", "10"],
        output='screen'
    )
        
    gripper_command_node = Node(
        package='robotics_project',
        executable='gripper_command_node.py',
        name='gripper_command_node',
        output='screen'
    )

    return LaunchDescription([
        set_gz_sim_resource_path,
        gazebo,
        spawn_entity,
        bridge,
        robot_state_publisher_node,
        joint_state_publisher_node,
        arm_controller_manager_spawner,
        hand_controller_manager_spawner,
        joint_state_broadcaster_spawner,
        gripper_command_node
    ])