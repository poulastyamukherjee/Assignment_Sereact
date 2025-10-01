import threading
import time
import json
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
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

# Enable CORS for all routes
CORS(app, origins=["http://localhost:5001", "http://127.0.0.1:5001", "*"])
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

def trapezoidal_profile(start_pos, end_pos, total_time, accel_time, max_velocity=None):
    """
    Generate a trapezoidal velocity profile for smooth motion.
    
    Args:
        start_pos: Starting position
        end_pos: Ending position  
        total_time: Total time for the movement
        accel_time: Time spent accelerating/decelerating
        max_velocity: Maximum velocity (calculated if None)
    
    Returns:
        A function that takes time t and returns position
    """
    distance = end_pos - start_pos
    
    # Calculate max velocity if not provided
    if max_velocity is None:
        # For trapezoidal profile: distance = 0.5 * accel_time * max_vel + (total_time - 2*accel_time) * max_vel + 0.5 * accel_time * max_vel
        # Simplifying: distance = max_vel * (total_time - accel_time)
        max_velocity = distance / (total_time - accel_time) if (total_time - accel_time) > 0 else distance / total_time
    
    acceleration = max_velocity / accel_time if accel_time > 0 else 0
    
    def position_at_time(t):
        if t <= 0:
            return start_pos
        elif t >= total_time:
            return end_pos
        elif t <= accel_time:
            # Acceleration phase
            return start_pos + 0.5 * acceleration * t * t
        elif t <= (total_time - accel_time):
            # Constant velocity phase
            accel_distance = 0.5 * acceleration * accel_time * accel_time
            const_distance = max_velocity * (t - accel_time)
            return start_pos + accel_distance + const_distance
        else:
            # Deceleration phase
            decel_start_time = total_time - accel_time
            time_in_decel = t - decel_start_time
            
            accel_distance = 0.5 * acceleration * accel_time * accel_time
            const_distance = max_velocity * (decel_start_time - accel_time)
            decel_distance = max_velocity * time_in_decel - 0.5 * acceleration * time_in_decel * time_in_decel
            
            return start_pos + accel_distance + const_distance + decel_distance
    
    return position_at_time

def generate_trapezoidal_movement_sequence():
    """
    Generates a smooth trapezoidal movement sequence for the robot arm.
    Each joint moves from 0 to a target position and back using trapezoidal interpolation.
    """
    sequence = []
    total_time = 10.0  # Total time for movement in seconds
    accel_time = 2.0   # Time for acceleration/deceleration
    time_step = 0.1    # Time step for discretization
    num_steps = int(total_time / time_step)
    
    # Define target positions for each joint (in radians)
    target_positions = {
        'shoulder_pan_joint': math.pi / 3,      # 60 degrees
        'shoulder_lift_joint': -math.pi / 6,    # -30 degrees  
        'elbow_joint': math.pi / 2,             # 90 degrees
        'wrist_1_joint': -math.pi / 4,          # -45 degrees
        'wrist_2_joint': math.pi / 6,           # 30 degrees
        'wrist_3_joint': math.pi / 4            # 45 degrees
    }
    
    # Create trapezoidal profiles for each joint
    joint_profiles = {}
    for joint in robot_arm.joints:
        if joint.joint_type != 'fixed':
            start_pos = 0.0
            end_pos = target_positions.get(joint.name, 0.0)
            joint_profiles[joint.name] = trapezoidal_profile(start_pos, end_pos, total_time, accel_time)
    
    # Generate the sequence
    for i in range(num_steps):
        t = i * time_step
        joint_angles = {}
        for joint_name, profile_func in joint_profiles.items():
            joint_angles[joint_name] = profile_func(t)
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
    from flask import request
    
    # Get movement type from request (default to sinusoidal)
    data = request.get_json() if request.is_json else {}
    movement_type = data.get('movement_type', 'sinusoidal')
    
    def movement_task():
        if movement_type == 'trapezoidal':
            sequence = generate_trapezoidal_movement_sequence()
        else:
            sequence = generate_movement_sequence()
        execute_movement_sequence(sequence)

    # Run the movement in a background thread to not block the API response
    thread = threading.Thread(target=movement_task)
    thread.start()

    return jsonify({
        "message": f"Movement sequence started with {movement_type} interpolation."
    })

if __name__ == '__main__':
    # Start the WebSocket server in a background thread
    websocket_thread = threading.Thread(target=run_websocket_server)
    websocket_thread.daemon = True
    websocket_thread.start()
    
    # Start the Flask app
    app.run(debug=True, port=5001, use_reloader=False)
