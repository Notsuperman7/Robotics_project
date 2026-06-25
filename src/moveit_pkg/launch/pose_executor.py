#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from threading import Thread
from pymoveit2 import MoveIt2


class NamedPoseExecutor(Node):
    def __init__(self):
        super().__init__("named_pose_executor")

        self.moveit2 = MoveIt2(
            node=self,
            joint_names=[
                "arm_1_joint",
                "arm_2_joint",
                "shoulder_joint",
                "wrist_1_joint",
                "wrist_2_joint",
            ],
            base_link_name="base_link",
            end_effector_name="wrist_2_link",
            group_name="arm_group",
        )
        self.moveit2.max_velocity = 0.1
        self.moveit2.max_acceleration = 0.1
        
        self.hand_moveit2 = MoveIt2(
            node=self,
            joint_names=[
                "geared_l_joint",
                "finger_l_joint",
                "geared_r_joint",
                "finger_r_joint",
            ],
            base_link_name="base_link",
            end_effector_name="finger_l_link",
            group_name="hand_group",
        )
        self.hand_moveit2.max_velocity = 0.1
        self.hand_moveit2.max_acceleration = 0.1

        self.poses = {
            "Home_pose": [0.0, 0.0, 0.0, 0.0, 0.0],
            "pick_right_pose": [-1.51, -0.2307, 0.0, 1.4919, 0.755],
            "pick_mid_pose": [0.0, -0.863, 0.0, 0.0, 0.0],
            "left_side_pick": [1.51, 2.259, 0.0, -1.51, 0.039],
        }
        self.hand_poses = {
            "opened_hand_pose": [-0.5, -0.41, -0.5, -0.41],
            "closed_hand_pose": [0.3449, 0.3449, 0.3449, 0.3449],
        }

    def run(self):
        while rclpy.ok():
            print("\nAvailable arm poses:")
            for pose_name in self.poses:
                print(f"- {pose_name}")
            for pose_name in self.hand_poses:
                print(f"- {pose_name}")

            pose = input("\nEnter the pose: ").strip()

            if pose in ["exit", "quit"]:
                break

            if pose in self.poses:
                self.get_logger().info(f"Moving arm to {pose}...")

                self.moveit2.max_velocity = 0.1
                self.moveit2.max_acceleration = 0.1

                self.moveit2.move_to_configuration(
                    joint_positions=self.poses[pose]
                )
                success = self.moveit2.wait_until_executed()

            elif pose in self.hand_poses:
                self.get_logger().info(f"Moving gripper to {pose}...")

                self.hand_moveit2.move_to_configuration(
                    joint_positions=self.hand_poses[pose]
                )
                success = self.hand_moveit2.wait_until_executed()

            else:
                print("Pose not found. Check spelling.")
                continue

            if success:
                self.get_logger().info(f"Done moving to {pose}")
            else:
                self.get_logger().error(f"Failed to execute {pose}")


def main():
    rclpy.init()
    node = NamedPoseExecutor()

    executor = rclpy.executors.MultiThreadedExecutor(2)
    executor.add_node(node)

    executor_thread = Thread(target=executor.spin, daemon=True)
    executor_thread.start()

    try:
        node.run()
    finally:
        executor.shutdown()
        node.destroy_node()
        rclpy.shutdown()
    

if __name__ == "__main__":
    main()