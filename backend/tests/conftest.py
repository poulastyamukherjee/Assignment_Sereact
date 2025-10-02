"""
Shared pytest fixtures and configuration for the robot backend tests.
"""

import pytest
import sys
import os
from unittest.mock import Mock, patch
import numpy as np

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session", autouse=True)
def mock_urdf_loading():
    """
    Mock URDF loading for all tests to avoid dependency issues.
    This fixture runs automatically for all tests.
    """
    with patch('urdfpy.URDF') as mock_urdf_class:
        # Create a mock URDF instance
        mock_urdf_instance = Mock()
        
        # Mock robot joints
        mock_joints = []
        joint_names = [
            'shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint',
            'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint'
        ]
        
        for name in joint_names:
            mock_joint = Mock()
            mock_joint.name = name
            mock_joint.joint_type = "revolute"
            mock_joints.append(mock_joint)
        
        # Add a fixed joint for testing
        fixed_joint = Mock()
        fixed_joint.name = "base_link_joint"
        fixed_joint.joint_type = "fixed"
        mock_joints.append(fixed_joint)
        
        mock_urdf_instance.joints = mock_joints
        
        # Mock forward kinematics
        def mock_link_fk(cfg=None):
            """Mock forward kinematics function."""
            mock_pose = np.array([
                [1.0, 0.0, 0.0, 1.5],
                [0.0, 1.0, 0.0, 2.0],
                [0.0, 0.0, 1.0, 3.0],
                [0.0, 0.0, 0.0, 1.0]
            ])
            
            mock_link = Mock()
            mock_link.name = "wrist_3_link"
            
            return {mock_link: mock_pose}
        
        mock_urdf_instance.link_fk = mock_link_fk
        
        # Configure the URDF class to return our mock instance
        mock_urdf_class.load.return_value = mock_urdf_instance
        
        yield mock_urdf_instance


@pytest.fixture
def mock_robot_joints():
    """
    Provide mock robot joints for testing.
    """
    joints = []
    joint_names = [
        'shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint',
        'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint'
    ]
    
    for name in joint_names:
        mock_joint = Mock()
        mock_joint.name = name
        mock_joint.joint_type = "revolute"
        joints.append(mock_joint)
    
    return joints


@pytest.fixture
def sample_joint_angles():
    """
    Provide sample joint angles for testing.
    """
    return {
        'shoulder_pan_joint': 0.1,
        'shoulder_lift_joint': -0.2,
        'elbow_joint': 0.3,
        'wrist_1_joint': -0.4,
        'wrist_2_joint': 0.5,
        'wrist_3_joint': -0.6
    }


@pytest.fixture
def mock_end_effector_pose():
    """
    Provide a mock end effector pose for testing.
    """
    return {
        'position': [1.5, 2.0, 3.0],
        'orientation': [0.1, 0.2, 0.3]
    }


@pytest.fixture
def mock_websocket_functions():
    """
    Mock WebSocket related functions.
    """
    with patch('app.send_to_all') as mock_send_all, \
         patch('app.has_connected_clients') as mock_has_clients, \
         patch('app.run_websocket_server') as mock_run_server:
        
        mock_has_clients.return_value = True
        yield {
            'send_to_all': mock_send_all,
            'has_connected_clients': mock_has_clients,
            'run_websocket_server': mock_run_server
        }


@pytest.fixture
def flask_app():
    """
    Create and configure a Flask app for testing.
    """
    # This will be imported after the URDF mocking is in place
    import app
    
    # Configure app for testing
    app.app.config['TESTING'] = True
    app.app.config['WTF_CSRF_ENABLED'] = False
    
    # Initialize test joint angles
    app.current_joint_angles = {
        'shoulder_pan_joint': 0.0,
        'shoulder_lift_joint': 0.0,
        'elbow_joint': 0.0,
        'wrist_1_joint': 0.0,
        'wrist_2_joint': 0.0,
        'wrist_3_joint': 0.0
    }
    
    return app.app


@pytest.fixture
def client(flask_app):
    """
    Create a test client for the Flask app.
    """
    with flask_app.test_client() as client:
        yield client


@pytest.fixture(autouse=True)
def reset_joint_angles():
    """
    Reset joint angles before each test.
    This fixture runs automatically before each test.
    """
    # Import app here to ensure mocking is in place
    import app
    
    app.current_joint_angles = {
        'shoulder_pan_joint': 0.0,
        'shoulder_lift_joint': 0.0,
        'elbow_joint': 0.0,
        'wrist_1_joint': 0.0,
        'wrist_2_joint': 0.0,
        'wrist_3_joint': 0.0
    }
    
    yield
    
    # Cleanup after test if needed
    pass