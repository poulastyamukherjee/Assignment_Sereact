# Docker Installation and Setup Guide

## Prerequisites Installation

### Installing Docker on Ubuntu/Debian

1. **Update your package index:**
   ```bash
   sudo apt update
   ```

2. **Install required packages:**
   ```bash
   sudo apt install apt-transport-https ca-certificates curl gnupg lsb-release
   ```

3. **Add Docker's official GPG key:**
   ```bash
   curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
   ```

4. **Add Docker repository:**
   ```bash
   echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
   ```

5. **Install Docker Engine:**
   ```bash
   sudo apt update
   sudo apt install docker-ce docker-ce-cli containerd.io docker-compose-plugin
   ```

6. **Add your user to docker group (optional, to run without sudo):**
   ```bash
   sudo usermod -aG docker $USER
   newgrp docker
   ```

### Alternative: Install via Snap
```bash
sudo snap install docker
```

### Installing Docker Compose

Docker Compose is now included with Docker Engine, but if you need the standalone version:

```bash
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

## Quick Start After Installation

1. **Verify Docker installation:**
   ```bash
   docker --version
   docker compose version
   ```

2. **Build and run the robot application:**
   ```bash
   cd Assignment_Sereact
   ./docker-build.sh up
   ```

3. **Access the application:**
   - Open browser to `http://localhost`
   - Backend API: `http://localhost:5000`
   - WebSocket: `ws://localhost:8765`

## Development Mode

For development with hot reloading:
```bash
./docker-build.sh up-dev
```

## Troubleshooting

### Permission Denied
If you get permission denied errors:
```bash
sudo usermod -aG docker $USER
newgrp docker
```

### Port Conflicts
If ports are already in use, you can modify them in `.env`:
```bash
cp .env.example .env
# Edit .env to change ports
```

### Build Issues
Clean up and rebuild:
```bash
./docker-build.sh clean
./docker-build.sh build
```