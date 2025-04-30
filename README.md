# IoT Light Scheduler with WebSocket and MQTT

A web-based light scheduler that uses WebSocket and MQTT to control an Arduino-connected light.

## Overview

This project creates a complete system for scheduling when a light turns on and off:

1. **Web Interface** - HTML/CSS/JS browser interface to set scheduling times
2. **WebSocket Server** - Python server to handle communication between the web interface and MQTT
3. **MQTT Subscriber** - Python script that listens for commands and controls the Arduino
4. **Arduino** - Receives commands to control the relay and light

## System Architecture

```
+----------------+        +------------------+        +------------------+        +------------------+
|  Web Browser   | <----> | WebSocket Server | <----> |  MQTT Broker     | <----> | MQTT Subscriber  |
| (HTML/CSS/JS)  |        | (Python)         |        | (Mosquitto)      |        | (Python)         |
+----------------+        +------------------+        +------------------+        +------------------+
                                                                                         |
                                                                                         v
                                                                                  +------------------+
                                                                                  |     Arduino      |
                                                                                  | (with Relay)     |
                                                                                  +------------------+
                                                                                         |
                                                                                         v
                                                                                  +------------------+
                                                                                  |      Light       |
                                                                                  +------------------+
```

## Prerequisites

- Python 3.6 or higher
- pip (Python package manager)
- Node.js and npm (optional, for serving frontend files)
- Mosquitto MQTT broker installed
- Arduino IDE (for uploading code to Arduino)
- Arduino UNO with relay module

## Setup Instructions

### 1. Install Dependencies

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install Mosquitto MQTT broker (if not already installed)
# For Ubuntu/Debian:
sudo apt-get install mosquitto mosquitto-clients

# For macOS:
brew install mosquitto

# For Windows: Download from https://mosquitto.org/download/
```

### 2. Arduino Setup

1. Connect the relay module to your Arduino:

   - VCC to 5V
   - GND to GND
   - IN to Digital Pin 7 (or adjust in Arduino code)

2. Upload the following code to your Arduino:

```cpp
const int relayPin = 7;  // Pin connected to the relay

void setup() {
  Serial.begin(9600);
  pinMode(relayPin, OUTPUT);
  digitalWrite(relayPin, LOW);  // Ensure light is off at startup
  Serial.println("Arduino Ready");
}

void loop() {
  if (Serial.available() > 0) {
    char command = Serial.read();

    if (command == '1') {
      digitalWrite(relayPin, HIGH);  // Turn ON
      Serial.println("Light ON");
    }
    else if (command == '0') {
      digitalWrite(relayPin, LOW);   // Turn OFF
      Serial.println("Light OFF");
    }

    // Clear remaining buffer
    while (Serial.available() > 0) {
      Serial.read();
    }
  }
}
```

### 3. Start the System

Open three separate terminal windows:

#### Terminal 1: Start the Mosquitto MQTT broker

```bash
# Start Mosquitto
mosquitto -v
```

#### Terminal 2: Start the WebSocket Server

```bash
# Navigate to server directory
cd server

# Start the WebSocket server
./websocket_server.py
```

#### Terminal 3: Start the MQTT Subscriber

```bash
# Navigate to subscriber directory
cd subscriber

# Start the MQTT subscriber
./mqtt_subscriber.py
```

#### Serve the Frontend

You can use any web server to serve the frontend files. Here's an example using Python's built-in HTTP server:

```bash
# Navigate to frontend directory
cd frontend

# Start a simple HTTP server
python -m http.server 8000
```

Then open your browser and navigate to `http://localhost:8000`.

(or Go Live using the LIve Server extension)

## Usage

1. Open the web interface in your browser
2. Set the desired ON and OFF times using the time picker inputs
3. Click "Set Schedule" to send the schedule to the system
4. The light will automatically turn on and off according to the set schedule

## Troubleshooting

### WebSocket Connection Issues

- Ensure the WebSocket server is running on the correct port (8765)
- Check for any firewall issues blocking the WebSocket connection
- Verify the correct WebSocket URL in the frontend JavaScript

### MQTT Connection Issues

- Make sure the Mosquitto broker is running
- Check that the topics match between publisher and subscriber
- Verify the host settings in both WebSocket server and MQTT subscriber

### Arduino Connection Issues

- Check the USB connection to the Arduino
- Verify the correct serial port is being detected
- Ensure the baud rate matches (9600) between Arduino and subscriber


