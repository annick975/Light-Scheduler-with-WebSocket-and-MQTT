document.addEventListener('DOMContentLoaded', () => {
    // DOM Elements
    const onTimeInput = document.getElementById('onTime');
    const offTimeInput = document.getElementById('offTime');
    const submitBtn = document.getElementById('submitBtn');
    const statusDiv = document.getElementById('status');
    const lightIndicator = document.getElementById('lightIndicator');
    const lightState = document.getElementById('lightState');
    const currentOnTime = document.getElementById('currentOnTime');
    const currentOffTime = document.getElementById('currentOffTime');
    
    // WebSocket setup
    let socket;
    let isConnected = false;
    
    function connectWebSocket() {
        // Update with your WebSocket server address
        socket = new WebSocket('ws://localhost:8765');
        
        socket.onopen = () => {
            isConnected = true;
            console.log('Connected to WebSocket server');
            submitBtn.disabled = false;
        };
        
        socket.onclose = () => {
            isConnected = false;
            console.log('Disconnected from WebSocket server');
            submitBtn.disabled = true;
            
            // Try to reconnect after 5 seconds
            setTimeout(connectWebSocket, 5000);
        };
        
        socket.onerror = (error) => {
            console.error('WebSocket error:', error);
            showStatus('Connection error. Please try again later.', 'error');
        };
        
        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                
                if (data.type === 'status_update') {
                    // Update light status
                    updateLightStatus(data.status === 'on');
                    
                    // Update schedule display
                    if (data.onTime) currentOnTime.textContent = formatTime(data.onTime);
                    if (data.offTime) currentOffTime.textContent = formatTime(data.offTime);
                    
                    showStatus('Schedule updated successfully!', 'success');
                }
            } catch (error) {
                console.error('Error parsing message:', error);
            }
        };
    }
    
    // Initial connection
    connectWebSocket();
    
    // Event Listeners
    submitBtn.addEventListener('click', () => {
        const onTime = onTimeInput.value;
        const offTime = offTimeInput.value;
        
        if (!onTime || !offTime) {
            showStatus('Please set both ON and OFF times', 'error');
            return;
        }
        
        if (!isConnected) {
            showStatus('Not connected to server. Please try again.', 'error');
            return;
        }
        
        // Send schedule to server
        const schedule = {
            type: 'schedule',
            onTime: onTime,
            offTime: offTime
        };
        
        socket.send(JSON.stringify(schedule));
        showStatus('Sending schedule...', 'success');
    });
    
    // Helper Functions
    function updateLightStatus(isOn) {
        if (isOn) {
            lightIndicator.className = 'light-on';
            lightState.textContent = 'Light is ON';
        } else {
            lightIndicator.className = 'light-off';
            lightState.textContent = 'Light is OFF';
        }
    }
    
    function showStatus(message, type) {
        statusDiv.textContent = message;
        statusDiv.className = 'status ' + type;
        
        // Clear the status after 5 seconds
        setTimeout(() => {
            statusDiv.className = 'status';
        }, 5000);
    }
    
    function formatTime(timeString) {
        return timeString;
    }
}); 