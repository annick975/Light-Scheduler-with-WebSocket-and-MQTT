#!/usr/bin/env python3
import asyncio
import json
import logging
import os
import signal
import subprocess
import websockets
import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('websocket_server')

# Global state
CLIENTS = set()
CURRENT_STATE = {
    'status': 'off',
    'onTime': None,
    'offTime': None
}

async def publish_to_mqtt(topic, message):
    """Publish message to MQTT broker using mosquitto_pub"""
    try:
        cmd = ['mosquitto_pub', '-h', 'localhost', '-t', topic, '-m', message]
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        
        if process.returncode != 0:
            logger.error(f"MQTT publish error: {stderr.decode()}")
            return False
        
        logger.info(f"Published to MQTT: {topic} = {message}")
        return True
    except Exception as e:
        logger.error(f"Failed to publish to MQTT: {e}")
        return False

async def handle_schedule(schedule_data):
    """Process new schedule data and publish to MQTT"""
    on_time = schedule_data.get('onTime')
    off_time = schedule_data.get('offTime')
    
    if not on_time or not off_time:
        return False, "Missing on or off time"
    
    # Update current state
    CURRENT_STATE['onTime'] = on_time
    CURRENT_STATE['offTime'] = off_time
    
    # Create message for MQTT
    message = json.dumps({
        'onTime': on_time,
        'offTime': off_time
    })
    
    # Publish to MQTT
    success = await publish_to_mqtt('light/schedule', message)
    
    if success:
        # Notify all clients about the new schedule
        if CLIENTS:
            status_update = {
                'type': 'status_update',
                'status': CURRENT_STATE['status'],
                'onTime': on_time, 
                'offTime': off_time
            }
            await broadcast(json.dumps(status_update))
    
    return success, "Schedule updated" if success else "Failed to update schedule"

async def handle_message(websocket, message):
    """Handle incoming WebSocket messages"""
    try:
        data = json.loads(message)
        msg_type = data.get('type')
        
        if msg_type == 'schedule':
            success, message = await handle_schedule(data)
            return success, message
        else:
            return False, f"Unknown message type: {msg_type}"
    except json.JSONDecodeError:
        return False, "Invalid JSON format"
    except Exception as e:
        logger.error(f"Error handling message: {e}")
        return False, f"Internal error: {str(e)}"

async def broadcast(message):
    """Broadcast message to all connected clients"""
    if CLIENTS:
        await asyncio.gather(
            *[client.send(message) for client in CLIENTS],
            return_exceptions=True
        )

async def handler(websocket):
    """Handle WebSocket connection"""
    CLIENTS.add(websocket)
    client_ip = websocket.remote_address[0] if websocket.remote_address else "Unknown"
    logger.info(f"Client connected: {client_ip}")
    
    try:
        # Send current state to the new client
        status_update = {
            'type': 'status_update',
            'status': CURRENT_STATE['status'],
            'onTime': CURRENT_STATE['onTime'],
            'offTime': CURRENT_STATE['offTime']
        }
        await websocket.send(json.dumps(status_update))
        
        # Process messages
        async for message in websocket:
            logger.info(f"Received message from {client_ip}: {message}")
            success, response_msg = await handle_message(websocket, message)
            logger.info(f"Processed message: success={success}, response={response_msg}")
    except websockets.exceptions.ConnectionClosed:
        pass
    except Exception as e:
        logger.error(f"Error in handler: {e}")
    finally:
        CLIENTS.remove(websocket)
        logger.info(f"Client disconnected: {client_ip}")

async def check_time_schedule():
    """Periodically check schedule and update light status"""
    while True:
        try:
            if CURRENT_STATE['onTime'] and CURRENT_STATE['offTime']:
                current_time = datetime.datetime.now().strftime('%H:%M')
                on_time = CURRENT_STATE['onTime']
                off_time = CURRENT_STATE['offTime']
                
                # Determine if light should be on or off based on schedule
                new_status = 'off'
                if on_time <= off_time:  # Same day schedule
                    if on_time <= current_time < off_time:
                        new_status = 'on'
                else:  # Overnight schedule
                    if current_time >= on_time or current_time < off_time:
                        new_status = 'on'
                
                # If status changed, update and notify
                if new_status != CURRENT_STATE['status']:
                    CURRENT_STATE['status'] = new_status
                    command = '1' if new_status == 'on' else '0'
                    
                    # Publish light command to MQTT
                    await publish_to_mqtt('light/command', command)
                    
                    # Notify all clients
                    status_update = {
                        'type': 'status_update',
                        'status': new_status,
                        'onTime': on_time,
                        'offTime': off_time
                    }
                    await broadcast(json.dumps(status_update))
                    
                    logger.info(f"Light status changed to {new_status}")
        except Exception as e:
            logger.error(f"Error in schedule checker: {e}")
        
        # Check every minute
        await asyncio.sleep(60)

async def main():
    """Start WebSocket server"""
    # Start schedule checker
    asyncio.create_task(check_time_schedule())
    
    # Start WebSocket server
    async with websockets.serve(handler, "0.0.0.0", 8765):
        logger.info("WebSocket server started on ws://0.0.0.0:8765")
        
        # Keep server running until interrupted
        stop = asyncio.Future()
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop.set_result, None)
        
        await stop

if __name__ == "__main__":
    asyncio.run(main()) 