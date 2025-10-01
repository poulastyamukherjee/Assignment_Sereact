#!/bin/bash

# Robot Arm Docker Build and Run Script

set -e

echo "🤖 Robot Arm Control Application - Docker Setup"
echo "================================================"

# Function to display usage
usage() {
    echo "Usage: $0 [build|up|up-dev|down|logs|restart|clean|status]"
    echo ""
    echo "Commands:"
    echo "  build    - Build Docker images"
    echo "  up       - Build and start all services (production)"
    echo "  up-dev   - Build and start all services (development mode)"
    echo "  down     - Stop and remove all services"
    echo "  logs     - Show logs for all services"
    echo "  restart  - Restart all services"
    echo "  status   - Show status of all services"
    echo "  clean    - Remove all containers, images, and volumes"
    echo ""
    exit 1
}

# Check if docker-compose is available
COMPOSE_CMD=""
if command -v docker-compose &> /dev/null; then
    COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
else
    echo "❌ Error: Docker Compose is not installed"
    echo "Please install Docker Compose first. See DOCKER_INSTALL.md for instructions."
    exit 1
fi

# Check if Docker is running
if ! docker info &> /dev/null; then
    echo "❌ Error: Docker is not running"
    echo "Please start Docker first"
    exit 1
fi

case "${1:-}" in
    "build")
        echo "🔨 Building Docker images..."
        $COMPOSE_CMD build --no-cache
        echo "✅ Build completed successfully!"
        ;;
    
    "up")
        echo "🚀 Starting Robot Arm Control Application (Production)..."
        $COMPOSE_CMD up --build -d
        echo ""
        echo "✅ Application started successfully!"
        echo ""
        echo "🌐 Access the application at: http://localhost"
        echo "📡 Backend API: http://localhost:5000"
        echo "🔌 WebSocket: ws://localhost:8765"
        echo ""
        echo "📋 To view logs: ./docker-build.sh logs"
        echo "🛑 To stop: ./docker-build.sh down"
        ;;
    
    "up-dev")
        echo "🚀 Starting Robot Arm Control Application (Development)..."
        $COMPOSE_CMD -f docker-compose.yml -f docker-compose.dev.yml up --build -d
        echo ""
        echo "✅ Application started in development mode!"
        echo ""
        echo "🌐 Access the application at: http://localhost"
        echo "📡 Backend API: http://localhost:5000"
        echo "🔌 WebSocket: ws://localhost:8765"
        echo "🔧 Development mode: Hot reloading enabled"
        echo ""
        echo "📋 To view logs: ./docker-build.sh logs"
        echo "🛑 To stop: ./docker-build.sh down"
        ;;
    
    "down")
        echo "🛑 Stopping all services..."
        $COMPOSE_CMD down
        echo "✅ All services stopped!"
        ;;
    
    "logs")
        echo "📋 Showing application logs..."
        $COMPOSE_CMD logs -f
        ;;
    
    "status")
        echo "📊 Service Status:"
        $COMPOSE_CMD ps
        echo ""
        echo "🔍 Health Status:"
        $COMPOSE_CMD exec backend curl -s http://localhost:5000/health || echo "❌ Backend unhealthy"
        $COMPOSE_CMD exec frontend curl -s http://localhost:80 > /dev/null && echo "✅ Frontend healthy" || echo "❌ Frontend unhealthy"
        ;;
    
    "restart")
        echo "🔄 Restarting all services..."
        $COMPOSE_CMD restart
        echo "✅ Services restarted!"
        ;;
    
    "clean")
        echo "🧹 Cleaning up Docker resources..."
        read -p "⚠️  This will remove all containers, images, and volumes. Continue? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            $COMPOSE_CMD down -v --rmi all --remove-orphans
            echo "✅ Cleanup completed!"
        else
            echo "❌ Cleanup cancelled"
        fi
        ;;
    
    *)
        usage
        ;;
esac