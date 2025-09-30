from flask import Flask, jsonify, request, Response
import threading
import time
import random  # For simulating variations
import json
import queue

class RobotArm:
    """Represents the robot arm, managing its joints."""
    def __init__(self):
        """Initializes the robot arm with a predefined set of joints."""
        self.joints = [
            {"name": "base", "min_angle": -180, "max_angle": 180, "current_angle": 0},
            {"name": "shoulder", "min_angle": -90, "max_angle": 90, "current_angle": 0},
            {"name": "elbow", "min_angle": 0, "max_angle": 180, "current_angle": 0},
            {"name": "wrist_pitch", "min_angle": -90, "max_angle": 90, "current_angle": 0},
            {"name": "wrist_roll", "min_angle": -180, "max_angle": 180, "current_angle": 0},
            {"name": "gripper", "min_angle": 0, "max_angle": 1, "current_angle": 0},  # 0 for open, 1 for closed
        ]

    def get_joint_state(self, joint_name):
        """
        Retrieves the state of a specific joint.
        Args:
            joint_name (str): The name of the joint.
        Returns:
            dict or None: The joint's state if found, otherwise None.
        """
        for joint in self.joints:
            if joint["name"] == joint_name:
                return joint
        return None

    def set_joint_angle(self, joint_name, angle):
        """
        Sets the angle of a specific joint, within its range of motion.
        Args:
            joint_name (str): The name of the joint.
            angle (float): The new angle for the joint.
        Returns:
            bool: True if the angle was set successfully, otherwise False.
        """
        joint = self.get_joint_state(joint_name)
        if joint:
            if joint["min_angle"] <= angle <= joint["max_angle"]:
                joint["current_angle"] = angle
                return True
        return False

    def get_all_joint_states(self):
        """
        Retrieves the state of all joints.
        Returns:
            list: A list of dictionaries, each representing a joint's state.
        """
        return self.joints

# Create a single instance of the robot arm
robot_arm = RobotArm()