# Robot Arm Control Application - Docker Setup

This is a containerized version of the 6-axis robot arm control and visualization application using Docker and Docker Compose.

## Architecture

The application consists of two main services:

- **Backend**: Python Flask API with WebSocket server for real-time robot control
- **Frontend**: Nginx server serving static HTML/CSS/JavaScript files with API proxying

## Prerequisites

- Docker
- Docker Compose

## Quick Start

1. **Build and run the application:**
   ```bash
   docker-compose up --build
   ```

2. **Access the application:**
   - Open your browser and navigate to `http://localhost`
   - The frontend will automatically connect to the backend services

3. **Stop the application:**
   ```bash
   docker-compose down
   ```

## Services

### Backend Service
- **Container name**: `robot-backend`
- **Ports**: 
  - `5000`: Flask API server
  - `8765`: WebSocket server
- **Health check**: `GET /health`

### Frontend Service
- **Container name**: `robot-frontend`
- **Port**: `80`: Nginx web server
- **Nginx proxy**:
  - `/api/*` → Backend Flask API
  - `/ws/*` → Backend WebSocket server

## Development

### Building individual services

**Backend only:**
```bash
cd backend
docker build -t robot-backend .
```

**Frontend only:**
```bash
cd frontend  
docker build -t robot-frontend .
```

### Running individual containers

**Backend:**
```bash
docker run -p 5000:5000 -p 8765:8765 robot-backend
```

**Frontend:**
```bash
docker run -p 80:80 robot-frontend
```

## Configuration

### Environment Variables

The backend service supports the following environment variables:
- `FLASK_ENV`: Flask environment (default: production)
- `PYTHONPATH`: Python path (default: /app)

### Volumes

The application mounts the URDF files as read-only volumes to ensure the robot model data is available to the backend service.

## API Endpoints

- `GET /health` - Health check endpoint
- `POST /move` - Start robot movement sequence
- `POST /move_joint_smooth` - Smooth joint movement
- `POST /set_joints` - Set joint angles manually
- `GET /robot_state` - Get current robot state
- `WebSocket /ws/` - Real-time robot data updates

## Troubleshooting

### Container logs
```bash
# View backend logs
docker-compose logs backend

# View frontend logs  
docker-compose logs frontend

# Follow logs in real-time
docker-compose logs -f
```

### Health checks
```bash
# Check backend health
curl http://localhost:5000/health

# Check frontend
curl http://localhost/
```

### Restart services
```bash
# Restart backend only
docker-compose restart backend

# Restart frontend only
docker-compose restart frontend
```

## Network Architecture

The services communicate through a custom Docker network (`robot-network`) which allows:
- Frontend nginx to proxy requests to backend
- Isolated network communication between containers
- External access only through exposed ports

## Data Persistence

Currently, the application doesn't require persistent data storage. All robot state is maintained in memory during runtime.