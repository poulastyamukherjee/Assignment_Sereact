from flask import Flask, jsonify, request, Response
import threading
import time
import random  # For simulating variations
import json
import queue
from urdfpy import URDF

class RobotArm:
    """Represents the robot arm, managing its joints."""
    def __init__(self, urdf_file):
        """Initializes the robot arm from a URDF file."""
        self.robot = URDF.load(urdf_file)
        self.joint_states = {joint.name: 0 for joint in self.robot.joints if joint.joint_type != 'fixed'}

    def get_joint_state(self, joint_name):
        """
        Retrieves the state of a specific joint.
        Args:
            joint_name (str): The name of the joint.
        Returns:
            dict or None: The joint's state if found, otherwise None.
        """
        for joint in self.robot.joints:
            if joint.name == joint_name:
                return {
                    "name": joint.name,
                    "min_angle": joint.limit.lower if joint.limit else None,
                    "max_angle": joint.limit.upper if joint.limit else None,
                    "current_angle": self.joint_states.get(joint.name)
                }
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
        joint_info = self.get_joint_state(joint_name)
        if joint_info:
            min_angle = joint_info["min_angle"]
            max_angle = joint_info["max_angle"]
            if (min_angle is None or angle >= min_angle) and \
               (max_angle is None or angle <= max_angle):
                self.joint_states[joint_name] = angle
                return True
        return False

    def get_all_joint_states(self):
        """
        Retrieves the state of all joints.
        Returns:
            list: A list of dictionaries, each representing a joint's state.
        """
        states = []
        for joint in self.robot.joints:
            if joint.joint_type != 'fixed':
                states.append(self.get_joint_state(joint.name))
        return states

# Create a single instance of the robot arm
robot_model_file_path = "/home/pouri/workspace/Assignment_Sereact/urdfpy/tests/data/ur5/ur5.urdf"
robot_arm = URDF.load(robot_model_file_path)

for link in robot_arm.links:
    print(f"Link Name: {link.name}")