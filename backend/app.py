import threading
import time
import json
from flask import Flask, jsonify, send_from_directory
from flask_cors import CORS
from urdfpy import URDF
import math
import asyncio
import os
from app_websocket import send_to_all, run_server as run_websocket_server, has_connected_clients

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
    # Only try to send if there are connected clients
    if not has_connected_clients():
        return
        
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(send_to_all(data))
        loop.close()
    except Exception as e:
        # Silently handle WebSocket errors to not spam the console
        pass

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

def calculate_end_effector_pose(joint_angles):
    """
    Calculate end effector position and orientation from joint angles.
    """
    try:
        # Calculate forward kinematics
        fk_results = robot_arm.link_fk(cfg=joint_angles)
        
        # Extract end effector pose (assuming the last link is the end effector)
        end_effector_pose = None
        
        # Find the end effector link (typically the last link in the chain)
        for link, pose in fk_results.items():
            if 'wrist_3_link' in link.name or 'tool0' in link.name or 'ee_link' in link.name:
                end_effector_pose = pose
                break
        
        # If no specific end effector link found, use the last link
        if end_effector_pose is None and fk_results:
            end_effector_pose = list(fk_results.values())[-1]
        
        # Extract position and orientation from the pose matrix
        end_effector_position = [0, 0, 0]
        end_effector_orientation = [0, 0, 0]
        
        if end_effector_pose is not None:
            # Position is the translation part (last column, first 3 rows)
            end_effector_position = [
                float(end_effector_pose[0, 3]),
                float(end_effector_pose[1, 3]), 
                float(end_effector_pose[2, 3])
            ]
            
            # Convert rotation matrix to Euler angles (simplified)
            import numpy as np
            # Extract rotation matrix
            R = end_effector_pose[:3, :3]
            
            # Convert to Euler angles (ZYX convention)
            sy = np.sqrt(R[0,0] * R[0,0] + R[1,0] * R[1,0])
            singular = sy < 1e-6
            
            if not singular:
                x = np.arctan2(R[2,1], R[2,2])
                y = np.arctan2(-R[2,0], sy)
                z = np.arctan2(R[1,0], R[0,0])
            else:
                x = np.arctan2(-R[1,2], R[1,1])
                y = np.arctan2(-R[2,0], sy)
                z = 0
                
            end_effector_orientation = [float(x), float(y), float(z)]
        
        return {
            'position': end_effector_position,
            'orientation': end_effector_orientation
        }
    except Exception as e:
        print(f"Error calculating end effector pose: {e}")
        return {
            'position': [0, 0, 0],
            'orientation': [0, 0, 0]
        }

def execute_movement_sequence(sequence):
    """
    Executes the generated movement sequence.
    """
    for joint_angles in sequence:
        set_joint_angles(joint_angles)
        # Calculate forward kinematics
        fk_results = robot_arm.link_fk(cfg=joint_angles)
        
        # Extract end effector pose (assuming the last link is the end effector)
        end_effector_link = None
        end_effector_pose = None
        
        # Find the end effector link (typically the last link in the chain)
        for link, pose in fk_results.items():
            if 'wrist_3_link' in link.name or 'tool0' in link.name or 'ee_link' in link.name:
                end_effector_link = link
                end_effector_pose = pose
                break
        
        # If no specific end effector link found, use the last link
        if end_effector_pose is None and fk_results:
            end_effector_link, end_effector_pose = list(fk_results.items())[-1]
        
        # Extract position and orientation from the pose matrix
        end_effector_position = [0, 0, 0]
        end_effector_orientation = [0, 0, 0]
        
        if end_effector_pose is not None:
            # Position is the translation part (last column, first 3 rows)
            end_effector_position = [
                float(end_effector_pose[0, 3]),
                float(end_effector_pose[1, 3]), 
                float(end_effector_pose[2, 3])
            ]
            
            # Convert rotation matrix to Euler angles (simplified)
            import numpy as np
            # Extract rotation matrix
            R = end_effector_pose[:3, :3]
            
            # Convert to Euler angles (ZYX convention)
            sy = np.sqrt(R[0,0] * R[0,0] + R[1,0] * R[1,0])
            singular = sy < 1e-6
            
            if not singular:
                x = np.arctan2(R[2,1], R[2,2])
                y = np.arctan2(-R[2,0], sy)
                z = np.arctan2(R[1,0], R[0,0])
            else:
                x = np.arctan2(-R[1,2], R[1,1])
                y = np.arctan2(-R[2,0], sy)
                z = 0
                
            end_effector_orientation = [float(x), float(y), float(z)]
        
        # Prepare data for the frontend
        # Convert numpy arrays to lists for JSON serialization
        fk_data = {link.name: pose.tolist() for link, pose in fk_results.items()}
        
        frontend_data = {
            'joint_angles': joint_angles,
            'end_effector': {
                'position': end_effector_position,
                'orientation': end_effector_orientation
            },
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

@app.route('/move_joint_smooth', methods=['POST'])
def move_joint_smooth():
    """
    API endpoint to smoothly move a single joint using trapezoidal interpolation.
    """
    global current_joint_angles
    from flask import request
    
    data = request.get_json()
    if not data or 'joint_index' not in data or 'target_angle' not in data:
        return jsonify({"error": "Invalid request data. Need joint_index and target_angle"}), 400
    
    joint_index = data['joint_index']
    target_angle = float(data['target_angle'])
    movement_time = data.get('movement_time', 1.0)  # Default 1 second
    accel_time = data.get('accel_time', 0.3)  # Default 0.3 seconds
    
    if joint_index < 0 or joint_index >= 6:
        return jsonify({"error": "Invalid joint index. Must be 0-5"}), 400
    
    # Map joint index to joint name
    joint_names = [
        'shoulder_pan_joint',
        'shoulder_lift_joint', 
        'elbow_joint',
        'wrist_1_joint',
        'wrist_2_joint',
        'wrist_3_joint'
    ]
    
    joint_name = joint_names[joint_index]
    start_angle = current_joint_angles.get(joint_name, 0.0)
    
    def smooth_movement_task():
        # Create trapezoidal profile for this joint
        profile = trapezoidal_profile(start_angle, target_angle, movement_time, accel_time)
        
        # Generate movement sequence
        time_step = 0.05  # 20 Hz update rate
        num_steps = int(movement_time / time_step)
        
        for i in range(num_steps + 1):
            t = i * time_step
            if t > movement_time:
                t = movement_time
                
            # Calculate new angle for this joint
            new_angle = profile(t)
            
            # Update only this joint while keeping others at current positions
            new_joint_angles = current_joint_angles.copy()
            new_joint_angles[joint_name] = new_angle
            
            # Update current state
            set_joint_angles(new_joint_angles)
            
            # Calculate end effector pose
            end_effector = calculate_end_effector_pose(current_joint_angles)
            
            # Prepare data for frontend
            frontend_data = {
                'joint_angles': current_joint_angles,
                'end_effector': end_effector,
                'movement_progress': {
                    'joint_index': joint_index,
                    'current_step': i,
                    'total_steps': num_steps,
                    'is_moving': i < num_steps
                }
            }
            
            send_to_websocket(json.dumps(frontend_data))
            time.sleep(time_step)
        
        # Send final completion message
        final_data = {
            'joint_angles': current_joint_angles,
            'end_effector': calculate_end_effector_pose(current_joint_angles),
            'movement_complete': True,
            'joint_index': joint_index
        }
        send_to_websocket(json.dumps(final_data))
    
    # Run the movement in a background thread
    thread = threading.Thread(target=smooth_movement_task)
    thread.start()
    
    return jsonify({
        "message": f"Smooth movement started for joint {joint_index} to {target_angle:.3f} radians",
        "movement_time": movement_time,
        "joint_name": joint_name
    })

@app.route('/set_joints', methods=['POST'])
def set_joints_endpoint():
    """
    API endpoint to set joint angles manually.
    """
    global current_joint_angles
    from flask import request
    
    data = request.get_json()
    if not data or 'joints' not in data:
        return jsonify({"error": "Invalid request data"}), 400
    
    joints = data['joints']
    if len(joints) != 6:
        return jsonify({"error": "Expected 6 joint angles"}), 400
    
    # Map joint angles to joint names
    joint_names = [
        'shoulder_pan_joint',
        'shoulder_lift_joint', 
        'elbow_joint',
        'wrist_1_joint',
        'wrist_2_joint',
        'wrist_3_joint'
    ]
    
    joint_angles = {}
    for i, angle in enumerate(joints):
        joint_angles[joint_names[i]] = float(angle)
    
    # Update current joint angles
    set_joint_angles(joint_angles)
    
    # Calculate end effector pose
    end_effector = calculate_end_effector_pose(current_joint_angles)
    
    robot_state = {
        'joint_angles': current_joint_angles,
        'end_effector': end_effector,
        'timestamp': time.time()
    }
    
    return jsonify(robot_state)

@app.route('/robot_state', methods=['GET'])
def get_robot_state():
    """
    API endpoint to get the current robot state including end effector pose.
    """
    global current_joint_angles
    
    # Calculate end effector pose
    end_effector = calculate_end_effector_pose(current_joint_angles)
    
    robot_state = {
        'joint_angles': current_joint_angles,
        'end_effector': end_effector,
        'timestamp': time.time()
    }
    
    return jsonify(robot_state)

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
