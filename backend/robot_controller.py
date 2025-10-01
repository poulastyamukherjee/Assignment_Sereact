from flask import Flask, jsonify, request, Response
import threading
import time
import random  # For simulating variations
import json
import queue
from urdfpy import URDF
import pyrender
from PIL import Image
import os

# Create a single instance of the robot arm
robot_model_file_path = "/home/pouri/workspace/Assignment_Sereact/urdfpy/tests/data/ur5/ur5.urdf"
robot_arm = URDF.load(robot_model_file_path)

# Initialize the current position of the robot arm
current_joint_angles = {joint.name: 0.0 for joint in robot_arm.joints if joint.joint_type != 'fixed'}


def set_joint_angles(joint_angles):
    """
    Sets the angles for each joint of the robot arm.

    Args:
        joint_angles (dict): A dictionary where keys are joint names and
                             values are the desired angles in radians.
    """
    global current_joint_angles
    # You can now use the 'joint_angles' dictionary to control the robot arm
    # (e.g., send the angles to the robot's controller)
    print("\nSetting joint angles:")
    for joint_name, angle in joint_angles.items():
        print(f"- {joint_name}: {angle} radians")
        current_joint_angles[joint_name] = angle
    # In a real application, you would now update the robot's state
    # robot_arm.show(cfg=current_joint_angles) # Example of how you might use it
    print("\nCurrent robot position (joint angles):")
    print(current_joint_angles)


def calculate_and_display_fk(joint_angles):
    """
    Calculates and displays the forward kinematics for the given joint angles
    and saves an offscreen rendering of the robot's pose.

    Args:
        joint_angles (dict): A dictionary of joint angles.
    """
    # Calculate forward kinematics for all links
    fk_results = robot_arm.link_fk(cfg=joint_angles)

    print("\nForward Kinematics (Cartesian Positions):")
    for link in robot_arm.links:
        pose_matrix = fk_results.get(link)
        if pose_matrix is not None:
            # The position is in the last column of the 4x4 matrix
            position = pose_matrix[:3, 3]
            print(f"- {link.name}: (x={position[0]:.4f}, y={position[1]:.4f}, z={position[2]:.4f})")

    # Offscreen rendering
    try:
        # Create a scene with the specified joint configuration
        scene = pyrender.Scene.from_trimesh(robot_arm.visual_trimesh(cfg=joint_angles))

        # Create an offscreen renderer
        renderer = pyrender.OffscreenRenderer(viewport_width=640, viewport_height=480)
        
        # Render the scene
        color, depth = renderer.render(scene)
        
        # Save the image
        img = Image.fromarray(color)
        image_path = os.path.join(os.path.dirname(__file__), 'robot_pose.png')
        img.save(image_path)
        
        print(f"\nRobot visualization saved to: {image_path}")

        # Clean up the renderer
        renderer.delete()

    except Exception as e:
        print(f"\nCould not generate visualization. Error: {e}")
        print("This might be due to a missing display environment. The forward kinematics data is still correct.")


def get_joint_angles_from_user():
    """
    Allows the user to set the angles for each joint of the robot arm via CLI,
    with validation against joint limits.
    """
    # Create a dictionary to store the desired joint angles
    joint_angles = {}

    # Iterate through the joints and get user input for each one
    for joint in robot_arm.joints:
        if joint.joint_type != 'fixed':
            while True:
                try:
                    limit_info = ""
                    if joint.limit is not None:
                        limit_info = f" (limits: {joint.limit.lower:.2f} to {joint.limit.upper:.2f})"
                    
                    angle_str = input(f"Enter the desired angle for joint '{joint.name}' in radians{limit_info}: ")
                    angle = float(angle_str)

                    if joint.limit is not None:
                        if not (joint.limit.lower <= angle <= joint.limit.upper):
                            print(f"Error: Angle for joint '{joint.name}' is outside its limits. Please enter a value between {joint.limit.lower:.2f} and {joint.limit.upper:.2f}.")
                            continue
                    
                    joint_angles[joint.name] = angle
                    break
                except ValueError:
                    print("Invalid input. Please enter a valid number.")
    return joint_angles


# Example usage:
if __name__ == '__main__':
    print("Starting robot controller script...")
    
    # Get angles from user and set them
    user_joint_angles = get_joint_angles_from_user()
    set_joint_angles(user_joint_angles)

    # Calculate and display forward kinematics
    calculate_and_display_fk(current_joint_angles)
