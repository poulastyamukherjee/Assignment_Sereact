# 6-Axis Robot Arm Control & Visualization Application

A comprehensive web-based application for controlling and visualizing a 6-axis robot arm with real-time kinematics, smooth motion planning, and WebSocket communication.

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Prerequisites](#prerequisites)
- [Quick Start](#quick-start)
- [Development](#development)
- [Testing](#testing)
- [Docker Setup](#docker-setup)
- [API Documentation](#api-documentation)
- [Project Structure](#project-structure)
- [Contributing](#contributing)

## Overview

This application provides a complete solution for robot arm control featuring:

- **Real-time 3D visualization** of robot arm movements
- **Forward kinematics** calculations with end-effector pose tracking
- **Smooth motion planning** with trapezoidal velocity profiles
- **WebSocket communication** for real-time updates
- **RESTful API** for robot control and state management
- **Comprehensive test suite** with pytest framework
- **Containerized deployment** with Docker

## Architecture

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Robot Arm Control System                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │  Frontend   │    │   Backend   │    │   Robot     │     │
│  │             │    │             │    │   Model     │     │
│  │ • HTML/CSS  │◄──►│ • Flask API │◄──►│ • URDF      │     │
│  │ • JavaScript│    │ • WebSocket │    │ • Kinematics│     │
│  │ • 3D Render │    │ • Threading │    │ • Joints    │     │
│  └─────────────┘    └─────────────┘    └─────────────┘     │
│         │                    │                    │         │
│         └────────────────────┼────────────────────┘         │
│                              │                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                Docker Network                       │   │
│  │                                                     │   │
│  │  ┌─────────────┐         ┌─────────────────────┐   │   │
│  │  │   Nginx     │         │      Python         │   │   │
│  │  │   (Port 80) │◄───────►│   (Ports 5000,8765) │   │   │
│  │  └─────────────┘         └─────────────────────┘   │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Component Breakdown

#### Frontend (Nginx Container)
- **Static file serving** for HTML, CSS, JavaScript
- **Reverse proxy** for API and WebSocket routing
- **3D visualization** using JavaScript libraries
- **Real-time updates** via WebSocket connection

#### Backend (Python Flask Container)
- **Flask REST API** for robot control endpoints
- **WebSocket server** for real-time communication
- **URDF parser** for robot model loading
- **Forward kinematics** engine
- **Motion planning** algorithms

#### Robot Model
- **URDF representation** of UR5 robot arm
- **6 degrees of freedom** (shoulder, elbow, wrist joints)
- **Collision and visual meshes**
- **Joint limits and constraints**

## Features

### Core Functionality
- **Interactive robot control** with joint-by-joint movement
- **Real-time kinematics** with end-effector pose calculation
- **Smooth motion planning** using trapezoidal velocity profiles
- **WebSocket communication** for live updates
- **Automatic state synchronization** between frontend and backend

### Advanced Features
- **Comprehensive testing** with 40+ test cases
- **Docker containerization** for easy deployment
- **Health monitoring** and status checks
- **Development mode** with hot reloading
- **Detailed logging** and error handling

### Movement Types
- **Sinusoidal movement** - Smooth oscillating motion
- **Trapezoidal movement** - Realistic acceleration/deceleration profiles
- **Individual joint control** - Precise single-joint movements
- **Coordinated motion** - Multi-joint synchronized movement

## Prerequisites

### Required Software
- **Docker** (v20.10 or higher)
- **Docker Compose** (v2.0 or higher)
- **Git** for cloning the repository

### Optional for Development
- **Python 3.8+** for local development
- **Node.js** for frontend development
- **VS Code** or preferred IDE

### Docker Installation

#### Ubuntu/Debian
```bash
# Update package index
sudo apt update

# Install required packages
sudo apt install apt-transport-https ca-certificates curl gnupg lsb-release

# Add Docker's GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt update
sudo apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add user to docker group (optional)
sudo usermod -aG docker $USER
newgrp docker
```

#### Alternative: Install via Snap
```bash
sudo snap install docker
```

## Quick Start

### 1. Clone the Repository
```bash
git clone https://github.com/poulastyamukherjee/Assignment_Sereact.git
cd Assignment_Sereact
```

### 2. Start the Application
```bash
# Make the script executable
chmod +x docker-build.sh

# Build and start all services
./docker-build.sh up
```

### 3. Access the Application
- **Web Interface**: http://localhost
- **Backend API**: http://localhost:5000
- **WebSocket**: ws://localhost:8765
- **Health Check**: http://localhost:5000/health

### 4. Stop the Application
```bash
./docker-build.sh down
```

## Development

### Development Mode
For development with hot reloading:
```bash
./docker-build.sh up-dev
```

### Local Development Setup
```bash
# Navigate to backend
cd backend

# Install dependencies
pip install -r requirements.txt

# Run backend locally
python app.py

# In another terminal, serve frontend
cd ../frontend
python -m http.server 8080
```

### Docker Build Script Commands

The `docker-build.sh` script provides various commands for managing the application:

```bash
# Build Docker images
./docker-build.sh build

# Start services (production)
./docker-build.sh up

# Start services (development with hot reload)
./docker-build.sh up-dev

# Stop all services
./docker-build.sh down

# View logs
./docker-build.sh logs

# Check service status
./docker-build.sh status

# Restart services
./docker-build.sh restart

# Clean up all Docker resources
./docker-build.sh clean
```

## Testing

### Test Architecture

The application includes a comprehensive test suite with organized structure:

```
backend/
├── tests/                    # Test directory
│   ├── __init__.py          # Test package initialization
│   ├── test_app.py          # Main app.py function tests (22 tests)
│   ├── test_websocket.py    # WebSocket functionality tests (8 tests)
│   ├── conftest.py          # Shared fixtures and configuration
│   └── pytest.ini          # Pytest configuration for tests
├── pytest.ini              # Root pytest configuration
└── run_tests.py             # Test runner script
```

### Test Coverage

#### App.py Functions (22 Tests)
- `send_to_websocket()` - WebSocket communication
- `generate_movement_sequence()` - Movement generation
- `trapezoidal_profile()` - Velocity profiles
- `generate_trapezoidal_movement_sequence()` - Trapezoidal movement
- `calculate_end_effector_pose()` - Forward kinematics
- `execute_movement_sequence()` - Movement execution
- `set_joint_angles()` - Joint angle setting

#### Flask Endpoints (11 Tests)
- `GET /` - Index page
- `GET /health` - Health check
- `GET /robot_state` - Robot state
- `POST /set_joints` - Set joint angles
- `POST /move` - Start movement
- `POST /move_joint_smooth` - Smooth joint movement
- `GET /urdf/<filename>` - URDF file serving

#### WebSocket Functions (8 Tests)
- `send_to_all()` - Broadcast to clients
- `has_connected_clients()` - Client connection status
- `websocket_handler()` - Connection management
- `run_server()` - Server startup

### Running Tests

#### Using the Test Runner Script
```bash
# Navigate to backend directory
cd backend

# Check test file status
python run_tests.py --check

# Install test dependencies
python run_tests.py --install

# Run all tests
python run_tests.py --all

# Run with coverage report
python run_tests.py --coverage

# Run specific test categories
python run_tests.py --unit          # Unit tests
python run_tests.py --integration   # Integration tests
python run_tests.py --flask         # Flask endpoint tests
python run_tests.py --websocket     # WebSocket tests

# Run specific test file
python run_tests.py --file test_app.py

# Run code linting
python run_tests.py --lint
```

#### Using pytest Directly
```bash
# Navigate to backend directory
cd backend

# Run all tests
pytest -v

# Run specific test file
pytest tests/test_app.py -v

# Run specific test class
pytest tests/test_app.py::TestUtilityFunctions -v

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term-missing tests/

# Run tests matching a pattern
pytest -k "websocket" -v tests/
```

#### Test Dependencies
- `pytest>=7.0.0` - Testing framework
- `pytest-mock>=3.10.0` - Mocking utilities
- `pytest-flask>=1.2.0` - Flask testing utilities
- `pytest-asyncio>=0.21.0` - Async testing support

## Docker Setup

### Docker Architecture

The application uses a multi-container setup:

```
┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │    Backend      │
│   (Nginx)       │    │   (Flask +      │
│   Port: 80      │◄──►│   WebSocket)    │
│                 │    │   Ports: 5000,  │
│                 │    │          8765   │
└─────────────────┘    └─────────────────┘
        │                       │
        └───────────────────────┘
             Docker Network
```

### Services

#### Backend Service
- **Container name**: `robot-backend`
- **Base image**: `python:3.8-slim`
- **Ports**: 
  - `5000`: Flask API server
  - `8765`: WebSocket server
- **Health check**: `GET /health`
- **Volumes**: Robot data and source code

#### Frontend Service
- **Container name**: `robot-frontend`
- **Base image**: `nginx:alpine`
- **Port**: `80`: Nginx web server
- **Nginx proxy configuration**:
  - `/api/*` → Backend Flask API (`http://backend:5000`)
  - `/ws/*` → Backend WebSocket server (`http://backend:8765`)

### Environment Variables

Create a `.env` file for custom configuration:
```bash
# Backend configuration
FLASK_ENV=production
FLASK_DEBUG=false
BACKEND_PORT=5000
WEBSOCKET_PORT=8765

# Frontend configuration
FRONTEND_PORT=80

# Robot configuration
ROBOT_MODEL=ur5
```

### Docker Compose Files

- **`docker-compose.yml`** - Production configuration
- **`docker-compose.dev.yml`** - Development overrides with volume mounting

### Build Optimization

- **`.dockerignore`** files minimize build context
- **Multi-stage builds** for smaller images
- **Health checks** ensure service reliability
- **Restart policies** for automatic recovery

## API Documentation

### REST Endpoints

#### Robot State Management
```http
GET /robot_state
```
Returns current joint angles and end-effector pose.

```http
POST /set_joints
Content-Type: application/json

{
  "joints": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
}
```
Set all joint angles simultaneously.

#### Movement Control
```http
POST /move
Content-Type: application/json

{
  "movement_type": "trapezoidal"
}
```
Start predefined movement sequence.

```http
POST /move_joint_smooth
Content-Type: application/json

{
  "joint_index": 0,
  "target_angle": 1.5,
  "movement_time": 2.0,
  "accel_time": 0.5
}
```
Smoothly move individual joint.

#### System Health
```http
GET /health
```
Returns service health status.

#### Static Files
```http
GET /urdf/<filename>
```
Serve URDF robot model files.

### WebSocket Protocol

#### Connection
```javascript
const ws = new WebSocket('ws://localhost:8765');
```

#### Message Format
```json
{
  "joint_angles": {
    "shoulder_pan_joint": 0.1,
    "shoulder_lift_joint": 0.2,
    "elbow_joint": 0.3,
    "wrist_1_joint": 0.4,
    "wrist_2_joint": 0.5,
    "wrist_3_joint": 0.6
  },
  "end_effector": {
    "position": [1.5, 2.0, 3.0],
    "orientation": [0.1, 0.2, 0.3]
  },
  "timestamp": 1696234567.123
}
```

## Project Structure

```
Assignment_Sereact/
├── README.md                     # This comprehensive guide
├── LICENSE                       # Project license
├── docker-compose.yml            # Production Docker setup
├── docker-compose.dev.yml        # Development Docker overrides
├── docker-build.sh               # Docker management script
├── validate-docker.sh            # Docker setup validation
├── DOCKER_INSTALL.md             # Docker installation guide
├── DOCKER_README.md              # Docker-specific documentation
├── DOCKERIZATION_SUMMARY.md      # Dockerization overview
│
├── backend/                      # Python Flask backend
│   ├── app.py                    # Main Flask application
│   ├── app_websocket.py          # WebSocket server
│   ├── robot_controller.py       # Robot control logic
│   ├── requirements.txt          # Python dependencies
│   ├── Dockerfile                # Backend container definition
│   ├── .dockerignore             # Docker build optimization
│   ├── run_tests.py              # Test runner script
│   ├── pytest.ini               # Pytest configuration
│   ├── TESTING_README.md         # Testing documentation
│   ├── robot_ur5.urdf            # Robot model file
│   └── tests/                    # Test suite
│       ├── __init__.py           # Test package init
│       ├── test_app.py           # Main application tests
│       ├── test_websocket.py     # WebSocket tests
│       ├── conftest.py           # Test fixtures
│       └── pytest.ini           # Test configuration
│
├── frontend/                     # HTML/CSS/JS frontend
│   ├── index.html                # Main web interface
│   ├── diagnostics.html          # System diagnostics page
│   ├── robot-visualizer.js       # 3D visualization logic
│   ├── nginx.conf                # Nginx configuration
│   ├── Dockerfile                # Frontend container definition
│   └── .dockerignore             # Docker build optimization
│
└── robot_data/                   # Robot model assets
    └── ur5/                      # UR5 robot model
        ├── ur5.urdf              # Robot description
        ├── collision/            # Collision meshes
        └── visual/               # Visual meshes
```

## Contributing

### Development Workflow

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Run tests**
   ```bash
   cd backend
   python run_tests.py --all
   ```
5. **Test with Docker**
   ```bash
   ./docker-build.sh up-dev
   ```
6. **Commit and push**
   ```bash
   git add .
   git commit -m "Add your feature description"
   git push origin feature/your-feature-name
   ```
7. **Create a Pull Request**

### Code Style

- **Python**: Follow PEP 8 standards
- **JavaScript**: Use ES6+ features
- **Documentation**: Update README for new features
- **Testing**: Maintain test coverage above 90%

### Adding New Features

1. **Backend changes**: Update `app.py` and add tests
2. **Frontend changes**: Update HTML/CSS/JS files
3. **Docker changes**: Update Dockerfiles and docker-compose
4. **Documentation**: Update relevant README sections

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- **URDFpy** for robot model parsing
- **Flask** for the web framework
- **Docker** for containerization
- **Nginx** for reverse proxy capabilities
- **Pytest** for testing framework

---

**Happy Robot Controlling!**

For questions or support, please open an issue on the GitHub repository.
