#!/usr/bin/env python3
"""
WebSocket Client Test Script

This script tests the WebSocket connection to the WATCHKEEPER API.
"""

import asyncio
import json
import os
import sys
import logging
from datetime import datetime
from dotenv import load_dotenv
import websockets

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

# Configuration
WEBSOCKET_HOST = os.getenv("WEBSOCKET_HOST", "localhost")
WEBSOCKET_PORT = os.getenv("WEBSOCKET_PORT", "8000")

async def test_websocket_connection():
    """Test WebSocket connection to the WATCHKEEPER API"""
    uri = f"ws://{WEBSOCKET_HOST}:{WEBSOCKET_PORT}/ws/test_client"
    
    logger.info(f"Connecting to WebSocket server at {uri}...")
    
    try:
        # Set a 10-second timeout for the connection
        async with websockets.connect(uri, close_timeout=10, ping_timeout=10) as websocket:
            logger.info("✅ Connected to WebSocket server")
            
            # Subscribe to topics
            for topic in ["intelligence", "system", "alerts"]:
                logger.info(f"Subscribing to {topic}...")
                await websocket.send(json.dumps({
                    "type": "subscribe",
                    "topic": topic
                }))
                
                try:
                    # Set a 5-second timeout for receiving the response
                    response = await asyncio.wait_for(websocket.recv(), timeout=5)
                    response_data = json.loads(response)
                    
                    if response_data.get("status") == "success":
                        logger.info(f"✅ Successfully subscribed to {topic}")
                    else:
                        logger.warning(f"⚠️ Failed to subscribe to {topic}: {response_data}")
                except asyncio.TimeoutError:
                    logger.error(f"❌ Timeout waiting for subscription response for {topic}")
            
            # Send ping
            logger.info("Sending ping...")
            await websocket.send(json.dumps({
                "type": "ping",
                "timestamp": datetime.now().isoformat()
            }))
            
            try:
                # Set a 5-second timeout for receiving the pong response
                response = await asyncio.wait_for(websocket.recv(), timeout=5)
                response_data = json.loads(response)
                
                if response_data.get("type") == "pong":
                    logger.info("✅ Received pong response")
                else:
                    logger.warning(f"⚠️ Unexpected response to ping: {response_data}")
            except asyncio.TimeoutError:
                logger.error("❌ Timeout waiting for pong response")
            
            # Wait for messages with a timeout
            logger.info("Waiting for messages for 10 seconds...")
            
            try:
                # Wait for messages for 10 seconds, then exit
                end_time = datetime.now().timestamp() + 10
                while datetime.now().timestamp() < end_time:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=1)
                        response_data = json.loads(response)
                        logger.info(f"Received message: {response_data}")
                    except asyncio.TimeoutError:
                        # Just continue the loop if no message received in 1 second
                        continue
                logger.info("Test completed successfully")
            except KeyboardInterrupt:
                logger.info("Exiting due to user interrupt...")
    
    except Exception as e:
        logger.error(f"❌ WebSocket connection failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    asyncio.run(test_websocket_connection())
