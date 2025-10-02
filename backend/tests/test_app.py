import pytest
import json
import time
import math
import threading
from unittest.mock import Mock, patch, MagicMock
import numpy as np
from flask import Flask

# Import the app and its functions
import sys
import os

# Add the backend directory to the path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock the urdfpy module before importing app
with patch('urdfpy.URDF'):
    import app


class TestUtilityFunctions:
    """Test utility functions that don't depend on Flask app context."""

    def test_send_to_websocket_no_clients(self):
        """Test send_to_websocket when no clients are connected."""
        with patch('app.has_connected_clients', return_value=False):
            # Should not raise an error and should return None
            result = app.send_to_websocket({"test": "data"})
            assert result is None

    def test_send_to_websocket_with_clients(self):
        """Test send_to_websocket when clients are connected."""
        mock_data = {"test": "data"}
        
        with patch('app.has_connected_clients', return_value=True), \
             patch('asyncio.new_event_loop') as mock_loop_create, \
             patch('asyncio.set_event_loop') as mock_set_loop, \
             patch('app.send_to_all') as mock_send_all:
            
            mock_loop = Mock()
            mock_loop_create.return_value = mock_loop
            
            # Should not raise an error
            app.send_to_websocket(mock_data)
            
            mock_loop_create.assert_called_once()
            mock_set_loop.assert_called_once_with(mock_loop)
            mock_loop.run_until_complete.assert_called_once()
            mock_loop.close.assert_called_once()

    def test_send_to_websocket_exception_handling(self):
        """Test send_to_websocket handles exceptions gracefully."""
        with patch('app.has_connected_clients', return_value=True), \
             patch('asyncio.new_event_loop', side_effect=Exception("Test error")):
            
            # Should not raise an error even when exception occurs
            result = app.send_to_websocket({"test": "data"})
            assert result is None

    def test_generate_movement_sequence(self):
        """Test the generation of movement sequence."""
        with patch.object(app, 'robot_arm') as mock_robot_arm:
            # Mock robot joints
            mock_joint1 = Mock()
            mock_joint1.name = "joint1"
            mock_joint1.joint_type = "revolute"
            
            mock_joint2 = Mock()
            mock_joint2.name = "joint2"
            mock_joint2.joint_type = "revolute"
            
            mock_fixed_joint = Mock()
            mock_fixed_joint.name = "fixed_joint"
            mock_fixed_joint.joint_type = "fixed"
            
            mock_robot_arm.joints = [mock_joint1, mock_joint2, mock_fixed_joint]
            
            sequence = app.generate_movement_sequence()
            
            # Should return a list of 100 steps
            assert len(sequence) == 100
            
            # Each step should have joint angles for non-fixed joints
            for step in sequence:
                assert isinstance(step, dict)
                assert "joint1" in step
                assert "joint2" in step
                assert "fixed_joint" not in step
                
                # Values should be within reasonable range (-π/4 to π/4)
                assert -math.pi/4 <= step["joint1"] <= math.pi/4
                assert -math.pi/4 <= step["joint2"] <= math.pi/4

    def test_trapezoidal_profile_basic(self):
        """Test basic trapezoidal profile generation."""
        start_pos = 0.0
        end_pos = 1.0
        total_time = 2.0
        accel_time = 0.5
        
        profile_func = app.trapezoidal_profile(start_pos, end_pos, total_time, accel_time)
        
        # Test at start
        assert profile_func(0.0) == start_pos
        
        # Test at end
        assert abs(profile_func(total_time) - end_pos) < 1e-6
        
        # Test beyond end
        assert profile_func(total_time + 1.0) == end_pos
        
        # Test before start
        assert profile_func(-1.0) == start_pos
        
        # Test during acceleration phase
        pos_accel = profile_func(0.25)
        assert start_pos < pos_accel < end_pos
        
        # Test during constant velocity phase
        pos_const = profile_func(1.0)
        assert start_pos < pos_const < end_pos
        
        # Test during deceleration phase
        pos_decel = profile_func(1.75)
        assert start_pos < pos_decel < end_pos

    def test_trapezoidal_profile_with_max_velocity(self):
        """Test trapezoidal profile with custom max velocity."""
        start_pos = 0.0
        end_pos = 2.0
        total_time = 4.0
        accel_time = 1.0
        max_velocity = 1.0
        
        profile_func = app.trapezoidal_profile(start_pos, end_pos, total_time, accel_time, max_velocity)
        
        # Test basic boundaries
        assert profile_func(0.0) == start_pos
        assert abs(profile_func(total_time) - end_pos) < 1e-6

    def test_trapezoidal_profile_edge_cases(self):
        """Test trapezoidal profile edge cases."""
        # Case where accel_time equals total_time (triangular profile)
        profile_func = app.trapezoidal_profile(0.0, 1.0, 1.0, 1.0)
        assert profile_func(0.0) == 0.0
        assert abs(profile_func(1.0) - 1.0) < 1e-6
        
        # Case where accel_time is 0
        profile_func = app.trapezoidal_profile(0.0, 1.0, 1.0, 0.0)
        assert profile_func(0.0) == 0.0
        assert abs(profile_func(1.0) - 1.0) < 1e-6

    def test_generate_trapezoidal_movement_sequence(self):
        """Test the generation of trapezoidal movement sequence."""
        with patch.object(app, 'robot_arm') as mock_robot_arm:
            # Mock robot joints
            mock_joints = []
            joint_names = ['shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint', 
                          'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint']
            
            for name in joint_names:
                mock_joint = Mock()
                mock_joint.name = name
                mock_joint.joint_type = "revolute"
                mock_joints.append(mock_joint)
            
            mock_robot_arm.joints = mock_joints
            
            sequence = app.generate_trapezoidal_movement_sequence()
            
            # Should return a list of steps (100 steps for 10 seconds at 0.1 step)
            assert len(sequence) == 100
            
            # Each step should have joint angles for all joints
            for step in sequence:
                assert isinstance(step, dict)
                for joint_name in joint_names:
                    assert joint_name in step
                    assert isinstance(step[joint_name], (int, float))

    def test_calculate_end_effector_pose_success(self):
        """Test successful end effector pose calculation."""
        joint_angles = {
            'shoulder_pan_joint': 0.1,
            'shoulder_lift_joint': 0.2,
            'elbow_joint': 0.3,
            'wrist_1_joint': 0.4,
            'wrist_2_joint': 0.5,
            'wrist_3_joint': 0.6
        }
        
        # Mock the robot arm and forward kinematics
        with patch.object(app, 'robot_arm') as mock_robot_arm:
            # Create a mock pose matrix
            mock_pose = np.array([
                [1.0, 0.0, 0.0, 1.5],
                [0.0, 1.0, 0.0, 2.0],
                [0.0, 0.0, 1.0, 3.0],
                [0.0, 0.0, 0.0, 1.0]
            ])
            
            mock_link = Mock()
            mock_link.name = "wrist_3_link"
            
            mock_robot_arm.link_fk.return_value = {mock_link: mock_pose}
            
            result = app.calculate_end_effector_pose(joint_angles)
            
            assert 'position' in result
            assert 'orientation' in result
            assert len(result['position']) == 3
            assert len(result['orientation']) == 3
            
            # Check position values
            assert result['position'][0] == 1.5
            assert result['position'][1] == 2.0
            assert result['position'][2] == 3.0

    def test_calculate_end_effector_pose_exception(self):
        """Test end effector pose calculation when exception occurs."""
        joint_angles = {'test_joint': 0.1}
        
        with patch.object(app, 'robot_arm') as mock_robot_arm:
            mock_robot_arm.link_fk.side_effect = Exception("Test error")
            
            result = app.calculate_end_effector_pose(joint_angles)
            
            # Should return default values
            assert result == {
                'position': [0, 0, 0],
                'orientation': [0, 0, 0]
            }

    def test_set_joint_angles(self):
        """Test setting joint angles."""
        # Initialize current_joint_angles
        app.current_joint_angles = {}
        
        test_angles = {
            'joint1': 0.5,
            'joint2': -0.3,
            'joint3': 1.2
        }
        
        app.set_joint_angles(test_angles)
        
        # Check that current_joint_angles was updated
        for joint_name, angle in test_angles.items():
            assert app.current_joint_angles[joint_name] == angle


class TestFlaskEndpoints:
    """Test Flask endpoints using the test client."""

    @pytest.fixture
    def client(self):
        """Create a test client for the Flask app."""
        # Mock the robot arm initialization
        with patch('app.URDF.load'), \
             patch('app.robot_arm') as mock_robot_arm, \
             patch('app.run_websocket_server'):
            
            # Setup mock robot arm
            mock_joint = Mock()
            mock_joint.name = "test_joint"
            mock_joint.joint_type = "revolute"
            mock_robot_arm.joints = [mock_joint]
            
            # Initialize current_joint_angles
            app.current_joint_angles = {"test_joint": 0.0}
            
            # Configure app for testing
            app.app.config['TESTING'] = True
            with app.app.test_client() as client:
                yield client

    def test_index_route(self, client):
        """Test the index route."""
        with patch('app.send_from_directory') as mock_send:
            mock_send.return_value = "test_html_content"
            response = client.get('/')
            assert response.status_code == 200

    def test_health_check(self, client):
        """Test the health check endpoint."""
        response = client.get('/health')
        assert response.status_code == 200
        
        data = json.loads(response.data)
        assert data['status'] == 'healthy'
        assert 'timestamp' in data
        assert data['service'] == 'robot-backend'

    def test_get_robot_state(self, client):
        """Test getting robot state."""
        with patch('app.calculate_end_effector_pose') as mock_calc:
            mock_calc.return_value = {
                'position': [1.0, 2.0, 3.0],
                'orientation': [0.1, 0.2, 0.3]
            }
            
            response = client.get('/robot_state')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'joint_angles' in data
            assert 'end_effector' in data
            assert 'timestamp' in data

    def test_set_joints_endpoint_valid(self, client):
        """Test setting joints with valid data."""
        valid_data = {
            'joints': [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
        }
        
        with patch('app.calculate_end_effector_pose') as mock_calc:
            mock_calc.return_value = {
                'position': [1.0, 2.0, 3.0],
                'orientation': [0.1, 0.2, 0.3]
            }
            
            response = client.post('/set_joints', 
                                 data=json.dumps(valid_data),
                                 content_type='application/json')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'joint_angles' in data
            assert 'end_effector' in data
            assert 'timestamp' in data

    def test_set_joints_endpoint_invalid_data(self, client):
        """Test setting joints with invalid data."""
        # Test missing joints key
        response = client.post('/set_joints', 
                             data=json.dumps({}),
                             content_type='application/json')
        assert response.status_code == 400
        
        # Test wrong number of joints
        invalid_data = {'joints': [0.1, 0.2, 0.3]}  # Only 3 joints instead of 6
        response = client.post('/set_joints',
                             data=json.dumps(invalid_data),
                             content_type='application/json')
        assert response.status_code == 400

    def test_move_robot_default(self, client):
        """Test move robot with default movement type."""
        with patch('app.generate_movement_sequence') as mock_gen, \
             patch('app.execute_movement_sequence') as mock_exec, \
             patch('threading.Thread') as mock_thread:
            
            mock_gen.return_value = [{'test_joint': 0.1}]
            
            response = client.post('/move')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'sinusoidal' in data['message']

    def test_move_robot_trapezoidal(self, client):
        """Test move robot with trapezoidal movement type."""
        request_data = {'movement_type': 'trapezoidal'}
        
        with patch('app.generate_trapezoidal_movement_sequence') as mock_gen, \
             patch('app.execute_movement_sequence') as mock_exec, \
             patch('threading.Thread') as mock_thread:
            
            mock_gen.return_value = [{'test_joint': 0.1}]
            
            response = client.post('/move',
                                 data=json.dumps(request_data),
                                 content_type='application/json')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'trapezoidal' in data['message']

    def test_move_joint_smooth_valid(self, client):
        """Test smooth joint movement with valid data."""
        valid_data = {
            'joint_index': 0,
            'target_angle': 1.5,
            'movement_time': 2.0,
            'accel_time': 0.5
        }
        
        # Initialize current_joint_angles for the test
        app.current_joint_angles = {
            'shoulder_pan_joint': 0.0,
            'shoulder_lift_joint': 0.0,
            'elbow_joint': 0.0,
            'wrist_1_joint': 0.0,
            'wrist_2_joint': 0.0,
            'wrist_3_joint': 0.0
        }
        
        with patch('app.trapezoidal_profile') as mock_profile, \
             patch('app.calculate_end_effector_pose') as mock_calc, \
             patch('app.send_to_websocket') as mock_send, \
             patch('threading.Thread') as mock_thread:
            
            mock_profile.return_value = lambda t: 0.5  # Simple constant function
            mock_calc.return_value = {'position': [0, 0, 0], 'orientation': [0, 0, 0]}
            
            response = client.post('/move_joint_smooth',
                                 data=json.dumps(valid_data),
                                 content_type='application/json')
            assert response.status_code == 200
            
            data = json.loads(response.data)
            assert 'Smooth movement started' in data['message']
            assert data['movement_time'] == 2.0
            assert data['joint_name'] == 'shoulder_pan_joint'

    def test_move_joint_smooth_invalid_data(self, client):
        """Test smooth joint movement with invalid data."""
        # Test missing required fields
        response = client.post('/move_joint_smooth',
                             data=json.dumps({}),
                             content_type='application/json')
        assert response.status_code == 400
        
        # Test invalid joint index
        invalid_data = {'joint_index': 10, 'target_angle': 1.0}
        response = client.post('/move_joint_smooth',
                             data=json.dumps(invalid_data),
                             content_type='application/json')
        assert response.status_code == 400

    def test_serve_urdf(self, client):
        """Test serving URDF files."""
        with patch('app.send_from_directory') as mock_send:
            mock_send.return_value = "urdf_content"
            response = client.get('/urdf/test.urdf')
            assert response.status_code == 200


class TestExecuteMovementSequence:
    """Test the execute_movement_sequence function."""

    def test_execute_movement_sequence(self):
        """Test execution of movement sequence."""
        # Mock sequence
        test_sequence = [
            {'joint1': 0.1, 'joint2': 0.2},
            {'joint1': 0.3, 'joint2': 0.4}
        ]
        
        with patch.object(app, 'robot_arm') as mock_robot_arm, \
             patch('app.set_joint_angles') as mock_set_joints, \
             patch('app.send_to_websocket') as mock_send, \
             patch('time.sleep') as mock_sleep:
            
            # Mock forward kinematics result
            mock_pose = np.array([
                [1.0, 0.0, 0.0, 1.0],
                [0.0, 1.0, 0.0, 2.0],
                [0.0, 0.0, 1.0, 3.0],
                [0.0, 0.0, 0.0, 1.0]
            ])
            
            mock_link = Mock()
            mock_link.name = "wrist_3_link"
            
            mock_robot_arm.link_fk.return_value = {mock_link: mock_pose}
            
            app.execute_movement_sequence(test_sequence)
            
            # Verify that set_joint_angles was called for each step
            assert mock_set_joints.call_count == len(test_sequence)
            
            # Verify that websocket data was sent for each step
            assert mock_send.call_count == len(test_sequence)
            
            # Verify sleep was called for each step
            assert mock_sleep.call_count == len(test_sequence)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])