class RobotVisualizer {
    constructor() {
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.robotArm = null;
        this.socket = null;
        this.isRecording = false;
        this.recordedTrajectory = [];
        this.currentRobotState = {
            joints: [0, 0, 0, 0, 0, 0],
            end_effector: { position: [0, 0, 0], orientation: [0, 0, 0] },
            sensors: { torque: [0, 0, 0, 0, 0, 0] }
        };
        this.trajectories = {};
        this.isConnected = false;
        
        this.init();
    }

    init() {
        this.setupThreeJS();
        this.createRobotArm();
        this.setupControls();
        this.setupWebSocket();
        this.setupEventListeners();
        this.animate();
        
        // Hide loading screen after initialization
        setTimeout(() => {
            document.getElementById('loading').style.display = 'none';
        }, 1000);
    }

    setupThreeJS() {
        // Scene
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x1a1a1a);

        // Camera
        this.camera = new THREE.PerspectiveCamera(75, 1, 0.1, 1000);
        this.camera.position.set(3, 2, 3);
        this.camera.lookAt(0, 1, 0);

        // Renderer
        const viewport = document.getElementById('viewport');
        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(viewport.clientWidth, viewport.clientHeight);
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
        viewport.appendChild(this.renderer.domElement);

        // Lighting
        const ambientLight = new THREE.AmbientLight(0x404040, 0.4);
        this.scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.8);
        directionalLight.position.set(8, 8, 4);
        directionalLight.castShadow = true;
        directionalLight.shadow.mapSize.width = 2048;
        directionalLight.shadow.mapSize.height = 2048;
        directionalLight.shadow.camera.near = 1;
        directionalLight.shadow.camera.far = 50;
        directionalLight.shadow.camera.left = -10;
        directionalLight.shadow.camera.right = 10;
        directionalLight.shadow.camera.top = 10;
        directionalLight.shadow.camera.bottom = -10;
        this.scene.add(directionalLight);

        // Additional fill light
        const fillLight = new THREE.DirectionalLight(0x4a90e2, 0.3);
        fillLight.position.set(-5, 3, -3);
        this.scene.add(fillLight);

        // Ground plane
        const groundGeometry = new THREE.PlaneGeometry(10, 10);
        const groundMaterial = new THREE.MeshLambertMaterial({ 
            color: 0x3d4956,
            transparent: true,
            opacity: 0.8
        });
        const ground = new THREE.Mesh(groundGeometry, groundMaterial);
        ground.rotation.x = -Math.PI / 2;
        ground.receiveShadow = true;
        this.scene.add(ground);

        // Grid
        const gridHelper = new THREE.GridHelper(8, 16, 0x4a90e2, 0x2c3e50);
        gridHelper.position.y = 0.01; // Slightly above ground to prevent z-fighting
        this.scene.add(gridHelper);

        // Coordinate axes
        const axesHelper = new THREE.AxesHelper(1.5);
        axesHelper.position.y = 0.02;
        this.scene.add(axesHelper);

        // Target/Goal indicator (like in the image)
        this.createTargetIndicator();

        // Handle window resize
        window.addEventListener('resize', () => this.onWindowResize());
    }

    createRobotArm() {
        // Create a simplified but realistic robot arm
        this.robotArm = new THREE.Group();
        this.joints = [];
        this.robot = { joints: {} };
        
        // Materials for different parts
        const baseMaterial = new THREE.MeshLambertMaterial({ color: 0x2c3e50 });
        const linkMaterial = new THREE.MeshLambertMaterial({ color: 0x34495e });
        const jointMaterial = new THREE.MeshLambertMaterial({ color: 0x4a90e2 });
        
        // Create robot structure
        this.createRobotStructure();
        
        this.scene.add(this.robotArm);
        this.showMessage('Robot arm visualization loaded', 'success');
    }
    
    createRobotStructure() {
        // Base
        const baseGeometry = new THREE.CylinderGeometry(0.15, 0.2, 0.3);
        const baseMaterial = new THREE.MeshLambertMaterial({ color: 0x2c3e50 });
        const base = new THREE.Mesh(baseGeometry, baseMaterial);
        base.position.y = 0.15;
        base.castShadow = true;
        this.robotArm.add(base);
        
        // Joint 1 (Base rotation)
        const joint1 = new THREE.Group();
        joint1.position.y = 0.3;
        const j1Housing = new THREE.Mesh(
            new THREE.CylinderGeometry(0.08, 0.08, 0.2),
            new THREE.MeshLambertMaterial({ color: 0x4a90e2 })
        );
        j1Housing.castShadow = true;
        joint1.add(j1Housing);
        this.robotArm.add(joint1);
        this.joints.push(joint1);
        
        // Upper arm
        const upperArm = new THREE.Group();
        upperArm.position.set(0, 0.15, 0);
        const upperArmGeom = new THREE.BoxGeometry(0.08, 0.6, 0.08);
        const upperArmMesh = new THREE.Mesh(upperArmGeom, new THREE.MeshLambertMaterial({ color: 0x34495e }));
        upperArmMesh.position.y = 0.3;
        upperArmMesh.castShadow = true;
        upperArm.add(upperArmMesh);
        joint1.add(upperArm);
        this.joints.push(upperArm);
        
        // Forearm
        const forearm = new THREE.Group();
        forearm.position.set(0, 0.6, 0);
        const forearmGeom = new THREE.BoxGeometry(0.06, 0.5, 0.06);
        const forearmMesh = new THREE.Mesh(forearmGeom, new THREE.MeshLambertMaterial({ color: 0x34495e }));
        forearmMesh.position.y = 0.25;
        forearmMesh.castShadow = true;
        forearm.add(forearmMesh);
        upperArm.add(forearm);
        this.joints.push(forearm);
        
        // Wrist joints
        const wrist1 = new THREE.Group();
        wrist1.position.set(0, 0.5, 0);
        const wrist1Mesh = new THREE.Mesh(
            new THREE.BoxGeometry(0.1, 0.05, 0.05),
            new THREE.MeshLambertMaterial({ color: 0x4a90e2 })
        );
        wrist1Mesh.castShadow = true;
        wrist1.add(wrist1Mesh);
        forearm.add(wrist1);
        this.joints.push(wrist1);
        
        const wrist2 = new THREE.Group();
        wrist2.position.set(0, 0.08, 0);
        const wrist2Mesh = new THREE.Mesh(
            new THREE.BoxGeometry(0.05, 0.08, 0.05),
            new THREE.MeshLambertMaterial({ color: 0x4a90e2 })
        );
        wrist2Mesh.castShadow = true;
        wrist2.add(wrist2Mesh);
        wrist1.add(wrist2);
        this.joints.push(wrist2);
        
        const wrist3 = new THREE.Group();
        wrist3.position.set(0, 0.08, 0);
        const endEffector = new THREE.Mesh(
            new THREE.CylinderGeometry(0.03, 0.03, 0.08),
            new THREE.MeshLambertMaterial({ color: 0xe74c3c })
        );
        endEffector.castShadow = true;
        wrist3.add(endEffector);
        wrist2.add(wrist3);
        this.joints.push(wrist3);
    }
    


    createTargetIndicator() {
        // Target platform (like the white surface in your image)
        const platformGeometry = new THREE.CylinderGeometry(0.6, 0.6, 0.05);
        const platformMaterial = new THREE.MeshLambertMaterial({ 
            color: 0xecf0f1,
            transparent: true,
            opacity: 0.9
        });
        const platform = new THREE.Mesh(platformGeometry, platformMaterial);
        platform.position.set(1.5, 0.025, 1.5);
        platform.receiveShadow = true;
        this.scene.add(platform);

        // Target circle (red ring like in your image)
        const ringGeometry = new THREE.RingGeometry(0.15, 0.2, 32);
        const ringMaterial = new THREE.MeshBasicMaterial({ 
            color: 0xe74c3c, 
            side: THREE.DoubleSide,
            transparent: true,
            opacity: 0.8
        });
        const targetRing = new THREE.Mesh(ringGeometry, ringMaterial);
        targetRing.rotation.x = -Math.PI / 2;
        targetRing.position.set(1.5, 0.06, 1.5);
        this.scene.add(targetRing);

        // Optional: Add a glowing effect
        const glowGeometry = new THREE.RingGeometry(0.18, 0.22, 32);
        const glowMaterial = new THREE.MeshBasicMaterial({ 
            color: 0xff6b6b,
            transparent: true,
            opacity: 0.3
        });
        const glow = new THREE.Mesh(glowGeometry, glowMaterial);
        glow.rotation.x = -Math.PI / 2;
        glow.position.set(1.5, 0.055, 1.5);
        this.scene.add(glow);

        // Store target position for future use
        this.targetPosition = new THREE.Vector3(1.5, 0.1, 1.5);
    }

    demoMovement() {
        // Demo sequence showing realistic robot movements
        const demoSequence = [
            { joints: [0, 0, 0, 0, 0, 0], delay: 1000 },
            { joints: [45, -30, 60, 0, 30, 0], delay: 2000 },
            { joints: [90, -45, 90, 45, 60, 90], delay: 2000 },
            { joints: [-90, -60, 120, -45, -30, -90], delay: 2000 },
            { joints: [0, -90, 90, 0, 90, 0], delay: 2000 },
            { joints: [0, 0, 0, 0, 0, 0], delay: 1000 }
        ];

        let currentStep = 0;
        const executeStep = () => {
            if (currentStep >= demoSequence.length) return;
            
            const step = demoSequence[currentStep];
            this.setJointsDegrees(step.joints);
            
            currentStep++;
            setTimeout(executeStep, step.delay);
        };
        
        this.showMessage('Starting demo movement sequence...', 'success');
        executeStep();
    }

    setJointsDegrees(jointsDegrees) {
        // Set joints using degrees and update sliders
        for (let i = 0; i < 6; i++) {
            const degrees = jointsDegrees[i] || 0;
            const radians = degrees * Math.PI / 180;
            
            // Update visualization
            this.updateJointPosition(i, radians);
            
            // Update sliders
            const slider = document.getElementById(`joint-${i}`);
            const valueSpan = document.getElementById(`joint-value-${i}`);
            
            if (slider && valueSpan) {
                slider.value = degrees.toString();
                valueSpan.textContent = `${degrees.toFixed(1)}°`;
            }
        }
        
        // Send to robot if connected
        if (this.isConnected) {
            const joints = jointsDegrees.map(deg => deg * Math.PI / 180);
            this.socket.emit('set_joints', { joints });
        }
    }

    setupControls() {
        const controlsContainer = document.getElementById('joint-controls');
        const jointNames = [
            'Base Rotation',
            'Shoulder Pitch', 
            'Elbow Pitch',
            'Wrist 1 Roll',
            'Wrist 2 Pitch', 
            'Wrist 3 Roll'
        ];
        
        for (let i = 0; i < 6; i++) {
            const controlDiv = document.createElement('div');
            controlDiv.className = 'joint-control';
            
            const label = document.createElement('label');
            label.textContent = `J${i + 1} - ${jointNames[i]}:`;
            
            const slider = document.createElement('input');
            slider.type = 'range';
            slider.className = 'joint-slider';
            slider.min = '-180';
            slider.max = '180';
            slider.value = '0';
            slider.step = '1';
            slider.id = `joint-${i}`;
            
            const valueSpan = document.createElement('span');
            valueSpan.className = 'joint-value';
            valueSpan.textContent = '0.00°';
            valueSpan.id = `joint-value-${i}`;
            
            slider.addEventListener('input', (e) => {
                const value = parseFloat(e.target.value);
                valueSpan.textContent = `${value.toFixed(1)}°`;
                this.updateJointPosition(i, value * Math.PI / 180);
                
                // Send command to robot via WebSocket
                if (this.isConnected) {
                    const joints = this.getJointAngles();
                    this.socket.emit('set_joints', { joints });
                }
            });
            
            controlDiv.appendChild(label);
            controlDiv.appendChild(slider);
            controlDiv.appendChild(valueSpan);
            controlsContainer.appendChild(controlDiv);
        }
    }

    setupWebSocket() {
        const socketUrl = "ws://localhost:8766";
        this.socket = new WebSocket(socketUrl);

        this.socket.onopen = () => {
            console.log("WebSocket connection established.");
            this.isConnected = true;
            this.updateConnectionStatus(true);
            this.showMessage("Connected to robot controller.", "success");
        };

        this.socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                // console.log("Received data:", data);
                this.updateRobotVisualization(data);
                this.updateRobotDisplay(data);
            } catch (e) {
                console.error("Failed to parse message:", e);
            }
        };

        this.socket.onerror = (error) => {
            console.error("WebSocket error:", error);
            this.showMessage("WebSocket connection error.", "error");
        };

        this.socket.onclose = () => {
            console.log("WebSocket connection closed.");
            this.isConnected = false;
            this.updateConnectionStatus(false);
            this.showMessage("Disconnected from robot controller.", "error");
            // Optional: attempt to reconnect
            setTimeout(() => this.setupWebSocket(), 5000);
        };
    }
    
    async triggerMovement() {
        this.showMessage("Requesting robot movement...", "info");
        try {
            const response = await fetch("http://localhost:5001/move", { method: 'POST' });
            if (response.ok) {
                const result = await response.json();
                this.showMessage(result.message, "success");
            } else {
                this.showMessage(`Error: ${response.statusText}`, "error");
            }
        } catch (error) {
            console.error("Failed to trigger movement:", error);
            this.showMessage("Failed to connect to the server to trigger movement.", "error");
        }
    }


    setupEventListeners() {
        // Reset joints button
        document.getElementById('reset-joints').addEventListener('click', () => {
            this.resetJoints();
        });

        // Add demo button
        const demoButton = document.createElement('button');
        demoButton.textContent = 'Start Movement';
        demoButton.id = 'start-movement';
        document.getElementById('joint-controls').appendChild(demoButton);
        
        demoButton.addEventListener('click', () => {
            this.triggerMovement();
        });
        
        // Emergency stop button
        document.getElementById('emergency-stop').addEventListener('click', () => {
            this.showMessage("Emergency stop not implemented on backend.", "error");
        });
        
        // Recording buttons
        const recordButton = document.getElementById('record-trajectory');
        const stopRecordingButton = document.getElementById('stop-recording');
        recordButton.disabled = true;
        stopRecordingButton.disabled = true;
        recordButton.style.display = 'none';
        stopRecordingButton.style.display = 'none';


        // Camera controls with mouse
        this.setupCameraControls();
    }

    setupCameraControls() {
        let isMouseDown = false;
        let mouseX = 0, mouseY = 0;
        let cameraDistance = 5;
        let cameraAngleX = 0.7;
        let cameraAngleY = 0.3;

        const canvas = this.renderer.domElement;

        canvas.addEventListener('mousedown', (event) => {
            isMouseDown = true;
            mouseX = event.clientX;
            mouseY = event.clientY;
        });

        canvas.addEventListener('mouseup', () => {
            isMouseDown = false;
        });

        canvas.addEventListener('mousemove', (event) => {
            if (!isMouseDown) return;

            const deltaX = event.clientX - mouseX;
            const deltaY = event.clientY - mouseY;

            cameraAngleX += deltaX * 0.01;
            cameraAngleY += deltaY * 0.01;
            cameraAngleY = Math.max(-Math.PI/2, Math.min(Math.PI/2, cameraAngleY));

            this.updateCameraPosition(cameraDistance, cameraAngleX, cameraAngleY);

            mouseX = event.clientX;
            mouseY = event.clientY;
        });

        canvas.addEventListener('wheel', (event) => {
            cameraDistance += event.deltaY * 0.01;
            cameraDistance = Math.max(2, Math.min(20, cameraDistance));
            this.updateCameraPosition(cameraDistance, cameraAngleX, cameraAngleY);
            event.preventDefault();
        });
    }

    updateCameraPosition(distance, angleX, angleY) {
        const x = distance * Math.cos(angleY) * Math.cos(angleX);
        const y = distance * Math.sin(angleY);
        const z = distance * Math.cos(angleY) * Math.sin(angleX);
        
        this.camera.position.set(x, y, z);
        this.camera.lookAt(0, 1, 0);  // Look at robot base
    }

    updateJointPosition(jointIndex, angle) {
        if (this.joints && this.joints[jointIndex]) {
            // Apply rotations based on joint type
            switch(jointIndex) {
                case 0: // Base rotation
                    this.joints[jointIndex].rotation.y = angle;
                    break;
                case 1: // Shoulder
                    this.joints[jointIndex].rotation.z = -angle;
                    break;
                case 2: // Elbow
                    this.joints[jointIndex].rotation.z = -angle;
                    break;
                case 3: // Wrist 1
                    this.joints[jointIndex].rotation.x = angle;
                    break;
                case 4: // Wrist 2
                    this.joints[jointIndex].rotation.z = -angle;
                    break;
                case 5: // Wrist 3
                    this.joints[jointIndex].rotation.x = angle;
                    break;
            }
        }
    }
    
    setJointAngles(jointAngles) {
        // Convert joint angles object to array and update positions
        const jointNames = [
            'shoulder_pan_joint',
            'shoulder_lift_joint',
            'elbow_joint', 
            'wrist_1_joint',
            'wrist_2_joint',
            'wrist_3_joint'
        ];
        
        jointNames.forEach((name, index) => {
            if (jointAngles[name] !== undefined) {
                this.updateJointPosition(index, jointAngles[name]);
            }
        });
    }

    getJointAngles() {
        const angles = [];
        for (let i = 0; i < 6; i++) {
            const slider = document.getElementById(`joint-${i}`);
            angles.push(parseFloat(slider.value) * Math.PI / 180);
        }
        return angles;
    }

    updateRobotVisualization(robotState) {
        if (!robotState.joint_angles) return;

        // Map joint names to the indices used in the frontend visualization
        const jointMap = {
            'shoulder_pan_joint': 0,
            'shoulder_lift_joint': 1,
            'elbow_joint': 2,
            'wrist_1_joint': 3,
            'wrist_2_joint': 4,
            'wrist_3_joint': 5
        };

        // Update robot joint positions
        for (const jointName in robotState.joint_angles) {
            const jointIndex = jointMap[jointName];
            const angle = robotState.joint_angles[jointName];
            if (jointIndex !== undefined) {
                this.updateJointPosition(jointIndex, angle);
                
                // Update UI sliders
                const slider = document.getElementById(`joint-${jointIndex}`);
                const valueSpan = document.getElementById(`joint-value-${jointIndex}`);
                const degrees = angle * 180 / Math.PI;
                
                if (slider && valueSpan) {
                    slider.value = degrees.toFixed(1);
                    valueSpan.textContent = `${degrees.toFixed(1)}°`;
                }
            }
        }
    }

    updateRobotDisplay(robotState) {
        if (!robotState.joint_angles) return;
        const robotInfo = document.getElementById('robot-info');
        
        const jointsStr = Object.values(robotState.joint_angles).map(j => (j * 180 / Math.PI).toFixed(1)).join('°, ');
        
        // For now, we don't have this data from the backend
        const endEffectorStr = "N/A"; 
        const torqueStr = "N/A";
        
        robotInfo.innerHTML = `
            <div>Joints: [${jointsStr}°]</div>
            <div>End Effector: [${endEffectorStr}]</div>
            <div>Torque: [${torqueStr}]</div>
            <div>Timestamp: ${new Date().toLocaleTimeString()}</div>
        `;
    }

    updateConnectionStatus(connected) {
        const indicator = document.getElementById('status-indicator');
        const statusText = document.getElementById('status-text');
        
        if (connected) {
            indicator.classList.add('connected');
            statusText.textContent = 'Connected';
        } else {
            indicator.classList.remove('connected');
            statusText.textContent = 'Disconnected';
        }
    }

    resetJoints() {
        for (let i = 0; i < 6; i++) {
            const slider = document.getElementById(`joint-${i}`);
            const valueSpan = document.getElementById(`joint-value-${i}`);
            
            slider.value = '0';
            valueSpan.textContent = '0.00°';
            this.updateJointPosition(i, 0);
        }
        
        if (this.isConnected) {
            this.socket.emit('set_joints', { joints: [0, 0, 0, 0, 0, 0] });
        }
    }

    startRecording() {
        this.isRecording = true;
        this.recordedTrajectory = [];
        
        document.getElementById('record-trajectory').disabled = true;
        document.getElementById('stop-recording').disabled = false;
        
        this.showMessage('Recording trajectory...', 'success');
    }

    stopRecording() {
        this.isRecording = false;
        
        document.getElementById('record-trajectory').disabled = false;
        document.getElementById('stop-recording').disabled = true;
        
        if (this.recordedTrajectory.length > 0 && this.isConnected) {
            // Upload trajectory to server
            this.socket.emit('upload_trajectory', { trajectory: this.recordedTrajectory });
            this.showMessage(`Recorded trajectory with ${this.recordedTrajectory.length} points`, 'success');
        } else {
            this.showMessage('No trajectory recorded', 'error');
        }
    }

    updateTrajectoryList() {
        const trajectoryList = document.getElementById('trajectory-list');
        trajectoryList.innerHTML = '';
        
        Object.keys(this.trajectories).forEach(trajId => {
            const trajData = this.trajectories[trajId];
            const trajDiv = document.createElement('div');
            trajDiv.className = 'trajectory-item';
            trajDiv.innerHTML = `
                <div>${trajId} (${trajData.length} points)</div>
                <button onclick="robotVisualizer.playTrajectory('${trajId}')">Play</button>
                <button onclick="robotVisualizer.deleteTrajectory('${trajId}')">Delete</button>
            `;
            trajectoryList.appendChild(trajDiv);
        });
    }

    playTrajectory(trajId) {
        if (this.isConnected) {
            this.socket.emit('play_trajectory', { traj_id: trajId });
        }
    }

    deleteTrajectory(trajId) {
        delete this.trajectories[trajId];
        this.updateTrajectoryList();
    }

    showMessage(text, type = 'info') {
        const messagesContainer = document.getElementById('messages');
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        messageDiv.textContent = text;
        
        messagesContainer.appendChild(messageDiv);
        
        // Auto-remove message after 5 seconds
        setTimeout(() => {
            if (messageDiv.parentNode) {
                messageDiv.parentNode.removeChild(messageDiv);
            }
        }, 5000);
        
        // Keep only last 5 messages
        while (messagesContainer.children.length > 5) {
            messagesContainer.removeChild(messagesContainer.firstChild);
        }
    }

    onWindowResize() {
        const viewport = document.getElementById('viewport');
        const width = viewport.clientWidth;
        const height = viewport.clientHeight;
        
        this.camera.aspect = width / height;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(width, height);
    }

    animate() {
        requestAnimationFrame(() => this.animate());
        this.renderer.render(this.scene, this.camera);
    }
}

// Initialize the robot visualizer when page loads
let robotVisualizer;
window.addEventListener('DOMContentLoaded', () => {
    robotVisualizer = new RobotVisualizer();
});

// Make robotVisualizer globally accessible for button callbacks
window.robotVisualizer = robotVisualizer;