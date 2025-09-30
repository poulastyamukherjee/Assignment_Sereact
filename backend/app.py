import threading
import time
import json
from flask import Flask, jsonify, send_from_directory
from urdfpy import URDF
import math
import asyncio
import os
from app_websocket import send_to_all, run_server as run_websocket_server

# Get the absolute path of the directory where this script is located
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Construct paths relative to the script's location
FRONTEND_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'frontend'))
URDF_DIR = os.path.abspath(os.path.join(BASE_DIR, '..', 'urdfpy', 'tests', 'data'))

app = Flask(__name__, static_folder=FRONTEND_DIR, static_url_path='')

# Load the robot model
robot_model_file_path = os.path.join(URDF_DIR, 'ur5', 'ur5.urdf')
robot_arm = URDF.load(robot_model_file_path)

# Initialize the current position of the robot arm
current_joint_angles = {joint.name: 0.0 for joint in robot_arm.joints if joint.joint_type != 'fixed'}

def send_to_websocket(data):
    """
    Sends data to all connected WebSocket clients.
    """
    # Since the WebSocket server runs in a different event loop,
    # we need to run the async send_to_all function in a new event loop.
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(send_to_all(data))
        loop.close()
    except Exception as e:
        print(f"Error sending to WebSocket: {e}")

def generate_movement_sequence():
    """
    Generates a smooth movement sequence for the robot arm.
    This is a placeholder and can be replaced with more complex logic.
    """
    sequence = []
    num_steps = 100
    amplitude = math.pi / 4  # 45 degrees

    for i in range(num_steps):
        joint_angles = {}
        for joint in robot_arm.joints:
            if joint.joint_type != 'fixed':
                # Simple sinusoidal movement for demonstration
                angle = amplitude * math.sin(2 * math.pi * i / num_steps)
                joint_angles[joint.name] = angle
        sequence.append(joint_angles)
    return sequence

def execute_movement_sequence(sequence):
    """
    Executes the generated movement sequence.
    """
    for joint_angles in sequence:
        set_joint_angles(joint_angles)
        # In a real scenario, you'd also calculate FK and send to frontend
        fk_results = robot_arm.link_fk(cfg=joint_angles)
        
        # Prepare data for the frontend
        # Convert numpy arrays to lists for JSON serialization
        fk_data = {link.name: pose.tolist() for link, pose in fk_results.items()}
        
        frontend_data = {
            'joint_angles': joint_angles,
            'fk': fk_data
        }
        
        send_to_websocket(json.dumps(frontend_data))
        time.sleep(0.1)  # Control the speed of the movement

def set_joint_angles(joint_angles):
    """
    Sets the angles for each joint of the robot arm.
    """
    global current_joint_angles
    for joint_name, angle in joint_angles.items():
        current_joint_angles[joint_name] = angle

@app.route('/')
def index():
    return send_from_directory(FRONTEND_DIR, 'index.html')

@app.route('/urdf/<path:filename>')
def serve_urdf(filename):
    return send_from_directory(os.path.join(URDF_DIR, 'ur5'), filename)

@app.route('/move', methods=['POST'])
def move_robot():
    """
    API endpoint to start the robot's movement sequence.
    """
    def movement_task():
        sequence = generate_movement_sequence()
        execute_movement_sequence(sequence)

    # Run the movement in a background thread to not block the API response
    thread = threading.Thread(target=movement_task)
    thread.start()

    return jsonify({"message": "Movement sequence started."})

if __name__ == '__main__':
    # Start the WebSocket server in a background thread
    websocket_thread = threading.Thread(target=run_websocket_server)
    websocket_thread.daemon = True
    websocket_thread.start()
    
    # Start the Flask app
    app.run(debug=True, port=5001, use_reloader=False)
