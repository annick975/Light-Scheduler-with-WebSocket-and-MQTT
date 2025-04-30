#!/usr/bin/env python3
import json
import logging
import signal
import subprocess
import sys
import time
import serial
import serial.tools.list_ports

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('mqtt_subscriber')

# Global variables
running = True
serial_port = None

def find_arduino_port():
    """Find Arduino device by looking for common identifiers"""
    ports = list(serial.tools.list_ports.comports())
    
    for port in ports:
        # Look for Arduino or USB device identifiers
        if "Arduino" in port.description or "CH340" in port.description or "USB" in port.description:
            logger.info(f"Found potential Arduino at {port.device}: {port.description}")
            return port.device
    
    logger.warning("No Arduino found. Available ports:")
    for port in ports:
        logger.warning(f"  {port.device}: {port.description}")
    
    return None

def setup_serial():
    """Connect to Arduino via serial"""
    global serial_port
    
    if serial_port and serial_port.is_open:
        return True
    
    # Find Arduino port
    port = find_arduino_port()
    if not port:
        logger.error("Could not find Arduino device. Please connect Arduino and try again.")
        return False
    
    try:
        # Connect with 9600 baud rate 
        serial_port = serial.Serial(port, 9600, timeout=2)
        time.sleep(2)  # Wait for Arduino to reset after connection
        logger.info(f"Connected to Arduino on {port}")
        return True
    except serial.SerialException as e:
        logger.error(f"Failed to connect to Arduino: {e}")
        serial_port = None
        return False

def send_command_to_arduino(command):
    """Send command to Arduino via serial"""
    if not setup_serial():
        logger.error("Cannot send command - no serial connection")
        return False
    
    try:
        
        cmd_bytes = (str(command) + '\n').encode('utf-8')
        serial_port.write(cmd_bytes)
        serial_port.flush()
        
    
        response = serial_port.readline().decode('utf-8').strip()
        if response:
            logger.info(f"Arduino response: {response}")
        
        return True
    except Exception as e:
        logger.error(f"Error sending command to Arduino: {e}")
        
        serial_port.close()
        serial_port = None
        return False

def on_mqtt_message(topic, message):
    """Process MQTT message and send to Arduino if needed"""
    logger.info(f"MQTT message received: {topic} = {message}")
    
    try:
        if topic == "light/command":
            
            command = message.strip()
            if command in ['0', '1']:
                logger.info(f"Sending command to Arduino: {command}")
                send_command_to_arduino(command)
            else:
                logger.warning(f"Invalid light command: {command}. Expected 0 or 1.")
                
        elif topic == "light/schedule":
            
            logger.info(f"Schedule update received: {message}")
            try:
                schedule = json.loads(message)
                logger.info(f"New schedule: ON at {schedule.get('onTime')}, OFF at {schedule.get('offTime')}")
            except json.JSONDecodeError:
                logger.error(f"Invalid schedule JSON: {message}")
    except Exception as e:
        logger.error(f"Error processing MQTT message: {e}")

def mqtt_subscribe():
    """Subscribe to MQTT topics using mosquitto_sub"""
    cmd = [
        'mosquitto_sub',
        '-h', 'localhost',
        '-v',  # Verbose to see topics
        '-t', 'light/command',
        '-t', 'light/schedule'
    ]
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1  
        )
        
        logger.info(f"MQTT subscriber started, subscribed to topics: light/command, light/schedule")
        
        while running:
            
            output = process.stdout.readline().strip()
            if output:
            
                parts = output.split(' ', 1)
                if len(parts) == 2:
                    topic, message = parts
                    on_mqtt_message(topic, message)
            
            
            if process.poll() is not None:
                stderr = process.stderr.read()
                if stderr:
                    logger.error(f"MQTT subscriber error: {stderr}")
                logger.error("MQTT subscriber process terminated unexpectedly")
                break
                
        # Clean up
        if process.poll() is None:
            process.terminate()
            process.wait()
    
    except Exception as e:
        logger.error(f"Error in MQTT subscriber: {e}")
    finally:
        if serial_port and serial_port.is_open:
            serial_port.close()
            logger.info("Serial connection closed")

def signal_handler(sig, frame):
    """Handle exit signals"""
    global running
    logger.info("Exit signal received, shutting down...")
    running = False
    if serial_port and serial_port.is_open:
        serial_port.close()
    sys.exit(0)

if __name__ == "__main__":

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run MQTT subscriber
    mqtt_subscribe()
