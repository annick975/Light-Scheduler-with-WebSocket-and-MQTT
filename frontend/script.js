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
    const connectionStatus = document.getElementById('connectionStatus');
    
    // WebSocket setup
    let socket;
    let isConnected = false;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;
    
    function connectWebSocket() {
        // Update with your WebSocket server address
        socket = new WebSocket('ws://localhost:8765');
        
        socket.onopen = () => {
            isConnected = true;
            reconnectAttempts = 0;
            console.log('Connected to WebSocket server');
            submitBtn.disabled = false;
            
            // Update connection status indicator
            updateConnectionStatus(true);
            
            // Flash the button to indicate it's ready
            submitBtn.classList.add('ready');
            setTimeout(() => {
                submitBtn.classList.remove('ready');
            }, 1000);
        };
        
        socket.onclose = () => {
            if (isConnected) {
                console.log('Disconnected from WebSocket server');
                // Only show the disconnection message if we were previously connected
                showStatus('Connection lost. Attempting to reconnect...', 'error');
            }
            
            isConnected = false;
            submitBtn.disabled = true;
            updateConnectionStatus(false);
            
            // Try to reconnect with exponential backoff
            if (reconnectAttempts < maxReconnectAttempts) {
                const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000);
                reconnectAttempts++;
                console.log(`Attempting to reconnect in ${delay/1000} seconds...`);
                setTimeout(connectWebSocket, delay);
            } else {
                showStatus('Could not reconnect to server. Please refresh the page.', 'error');
            }
        };
        
        socket.onerror = (error) => {
            console.error('WebSocket error:', error);
            showStatus('Connection error. Please try again later.', 'error');
        };
        
        socket.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                
                if (data.type === 'status_update') {
                    // Update light status with animation
                    updateLightStatus(data.status === 'on');
                    
                    // Update schedule display
                    if (data.onTime) currentOnTime.textContent = formatTime(data.onTime);
                    if (data.offTime) currentOffTime.textContent = formatTime(data.offTime);
                    
                    // Show success message
                    showStatus('Schedule updated successfully!', 'success');
                    
                    // Quick highlight of the updated values
                    highlightElement(currentOnTime);
                    highlightElement(currentOffTime);
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
            shakeElement(!onTime ? onTimeInput : offTimeInput);
            return;
        }
        
        if (!isConnected) {
            showStatus('Not connected to server. Please try again.', 'error');
            return;
        }
        
        // Add loading state to button
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
        submitBtn.disabled = true;
        
        // Send schedule to server
        const schedule = {
            type: 'schedule',
            onTime: onTime,
            offTime: offTime
        };
        
        socket.send(JSON.stringify(schedule));
        showStatus('Sending schedule...', 'success');
        
        // Reset button after 2 seconds
        setTimeout(() => {
            submitBtn.innerHTML = '<i class="fas fa-save"></i> Set Schedule';
            submitBtn.disabled = false;
        }, 2000);
    });
    
    // Helper Functions
    function updateLightStatus(isOn) {
        // First remove both classes
        lightIndicator.classList.remove('light-on', 'light-off');
        
        // Add the appropriate class with a slight delay for animation effect
        setTimeout(() => {
            if (isOn) {
                lightIndicator.classList.add('light-on');
                lightState.textContent = 'Light is ON';
            } else {
                lightIndicator.classList.add('light-off');
                lightState.textContent = 'Light is OFF';
            }
        }, 100);
    }
    
    function updateConnectionStatus(connected) {
        connectionStatus.className = connected 
            ? 'connection-status connected' 
            : 'connection-status disconnected';
        
        connectionStatus.innerHTML = connected 
            ? '<i class="fas fa-plug"></i> <span>Connected</span>' 
            : '<i class="fas fa-plug"></i> <span>Disconnected</span>';
    }
    
    function showStatus(message, type) {
        statusDiv.textContent = message;
        statusDiv.className = 'status ' + type;
        
        // Fade in effect
        statusDiv.style.opacity = '0';
        statusDiv.style.display = 'block';
        
        setTimeout(() => {
            statusDiv.style.opacity = '1';
        }, 10);
        
        // Clear the status after 5 seconds
        setTimeout(() => {
            statusDiv.style.opacity = '0';
            setTimeout(() => {
                statusDiv.className = 'status';
            }, 300);
        }, 5000);
    }
    
    function formatTime(timeString) {
        // You can enhance this function to format time as needed
        // For example, convert from 24-hour to 12-hour format
        return timeString;
    }
    
    function highlightElement(element) {
        element.classList.add('highlight');
        setTimeout(() => {
            element.classList.remove('highlight');
        }, 1000);
    }
    
    function shakeElement(element) {
        element.classList.add('shake');
        setTimeout(() => {
            element.classList.remove('shake');
        }, 500);
    }
    
    // Set default times to current time + 1 hour for ON and + 2 hours for OFF
    function setDefaultTimes() {
        const now = new Date();
        const onTime = new Date(now);
        onTime.setHours(onTime.getHours() + 1);
        
        const offTime = new Date(now);
        offTime.setHours(offTime.getHours() + 2);
        
        onTimeInput.value = formatTimeForInput(onTime);
        offTimeInput.value = formatTimeForInput(offTime);
    }
    
    function formatTimeForInput(date) {
        return `${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`;
    }
    
    // Set default times on page load
    setDefaultTimes();
}); 