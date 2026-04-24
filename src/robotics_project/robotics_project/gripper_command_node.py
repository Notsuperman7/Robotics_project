#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node

from std_msgs.msg import Float64
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration


class GripperCommandNode(Node):
    def __init__(self):
        super().__init__('gripper_command_node')

        self.declare_parameter('max_open', 0.5)
        self.declare_parameter('min_open', -0.7)
        self.declare_parameter('inner_ratio', 0.82)
        self.declare_parameter('move_time_sec', 1.0)

        self.max_open = float(self.get_parameter('max_open').value)
        self.min_open = float(self.get_parameter('min_open').value)
        self.inner_ratio = float(self.get_parameter('inner_ratio').value)
        self.move_time_sec = float(self.get_parameter('move_time_sec').value)

        self.pub = self.create_publisher(
            JointTrajectory,
            '/hand_group_controller/joint_trajectory',
            10
        )

        self.sub = self.create_subscription(
            Float64,
            '/gripper_command',
            self.command_callback,
            10
        )

        self.get_logger().info('Gripper command node started. Listen on /gripper_command')

    def command_callback(self, msg: Float64):
        x = float(msg.data)-0.7

        # clamp
        x = max(self.min_open, min(x, self.max_open))

        r1 = x
        r2 = self.inner_ratio * x
        l1 = x
        l2 = self.inner_ratio * x

        traj = JointTrajectory()
        traj.joint_names = [
            'geared_r_joint',
            'finger_r_joint',
            'geared_l_joint',
            'finger_l_joint',
        ]

        point = JointTrajectoryPoint()
        point.positions = [r1, r2, l1, l2]

        sec = int(self.move_time_sec)
        nanosec = int((self.move_time_sec - sec) * 1e9)
        point.time_from_start = Duration(sec=sec, nanosec=nanosec)

        traj.points.append(point)
        self.pub.publish(traj)

        self.get_logger().info(
            f'Published gripper command x={x:.3f} -> '
            f'R1={r1:.3f}, R2={r2:.3f}, L1={l1:.3f}, L2={l2:.3f}'
        )


def main(args=None):
    rclpy.init(args=args)
    node = GripperCommandNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()