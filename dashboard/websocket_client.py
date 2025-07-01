#!/usr/bin/env python3
"""
WebSocket Client for the Watchkeeper Dashboard
Enables real-time updates from the API
"""

import json
import logging
import os
import threading
import time
from typing import Callable, Dict, List, Optional, Any

import websocket

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class WebSocketClient:
    """
    WebSocket client for the Watchkeeper Dashboard
    Connects to the API WebSocket server and receives real-time updates
    """
    def __init__(self, host: str = None, port: int = None):
        """
        Initialize the WebSocket client
        
        Args:
            host: WebSocket server host (default: from env or localhost)
            port: WebSocket server port (default: from env or 8000)
        """
        self.host = host or os.getenv("WEBSOCKET_HOST", "localhost")
        self.port = port or int(os.getenv("WEBSOCKET_PORT", "8000"))
        self.url = f"ws://{self.host}:{self.port}/ws"
        self.ws = None
        self.connected = False
        self.reconnect_interval = 5  # seconds
        self.topics = set()
        self.callbacks = {}
        self.thread = None
    
    def connect(self) -> bool:
        """
        Connect to the WebSocket server
        
        Returns:
            True if connection was successful, False otherwise
        """
        try:
            # Set up WebSocket connection
            self.ws = websocket.WebSocketApp(
                self.url,
                on_open=lambda ws: self._on_open(ws),
                on_message=lambda ws, msg: self._on_message(ws, msg),
                on_error=lambda ws, err: self._on_error(ws, err),
                on_close=lambda ws, close_status_code, close_msg: self._on_close(ws, close_status_code, close_msg)
            )
            
            # Start WebSocket connection in a separate thread
            self.thread = threading.Thread(target=self.ws.run_forever)
            self.thread.daemon = True
            self.thread.start()
            
            # Wait for connection to establish
            timeout = 5
            start_time = time.time()
            while not self.connected and time.time() - start_time < timeout:
                time.sleep(0.1)
            
            return self.connected
        except Exception as e:
            logger.error(f"Error connecting to WebSocket server: {e}")
            return False
    
    def _on_open(self, ws):
        """
        Called when the WebSocket connection is opened
        
        Args:
            ws: WebSocket connection
        """
        logger.info(f"Connected to WebSocket server at {self.url}")
        self.connected = True
        
        # Resubscribe to topics if reconnecting
        for topic in self.topics:
            self._subscribe_to_topic(topic)
    
    def _on_message(self, ws, message):
        """
        Called when a message is received from the WebSocket server
        
        Args:
            ws: WebSocket connection
            message: Message received
        """
        try:
            data = json.loads(message)
            topic = data.get("topic")
            payload = data.get("payload")
            
            if topic and payload:
                logger.debug(f"Received message on topic '{topic}'")
                
                # Call registered callbacks for this topic
                if topic in self.callbacks:
                    for callback in self.callbacks[topic]:
                        try:
                            callback(payload)
                        except Exception as e:
                            logger.error(f"Error in callback for topic '{topic}': {e}")
        except json.JSONDecodeError:
            logger.warning(f"Received invalid JSON: {message}")
        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")
    
    def _on_error(self, ws, error):
        """
        Called when a WebSocket error occurs
        
        Args:
            ws: WebSocket connection
            error: Error that occurred
        """
        logger.error(f"WebSocket error: {error}")
    
    def _on_close(self, ws, close_status_code, close_msg):
        """
        Called when the WebSocket connection is closed
        
        Args:
            ws: WebSocket connection
            close_status_code: Status code for the close
            close_msg: Close message
        """
        logger.info(f"WebSocket connection closed: {close_status_code} - {close_msg}")
        self.connected = False
        
        # Attempt to reconnect
        threading.Thread(target=self._reconnect).start()
    
    def _reconnect(self):
        """
        Attempt to reconnect to the WebSocket server
        """
        logger.info(f"Attempting to reconnect in {self.reconnect_interval} seconds...")
        time.sleep(self.reconnect_interval)
        self.connect()
    
    def _subscribe_to_topic(self, topic: str):
        """
        Send subscription message to the server
        
        Args:
            topic: Topic to subscribe to
        """
        if self.connected:
            try:
                subscribe_msg = json.dumps({
                    "action": "subscribe",
                    "topic": topic
                })
                self.ws.send(subscribe_msg)
                logger.info(f"Subscribed to topic: {topic}")
            except Exception as e:
                logger.error(f"Error subscribing to topic '{topic}': {e}")
    
    def subscribe(self, topic: str, callback: Callable[[Dict], None]):
        """
        Subscribe to a topic and register a callback
        
        Args:
            topic: Topic to subscribe to
            callback: Function to call when a message is received on this topic
        """
        # Add topic to set of subscribed topics
        self.topics.add(topic)
        
        # Register callback
        if topic not in self.callbacks:
            self.callbacks[topic] = []
        self.callbacks[topic].append(callback)
        
        # Send subscription message if connected
        self._subscribe_to_topic(topic)
    
    def unsubscribe(self, topic: str, callback: Optional[Callable] = None):
        """
        Unsubscribe from a topic
        
        Args:
            topic: Topic to unsubscribe from
            callback: Specific callback to remove (if None, remove all callbacks)
        """
        if topic in self.callbacks:
            if callback is None:
                # Remove all callbacks for this topic
                self.callbacks[topic] = []
                self.topics.discard(topic)
            else:
                # Remove specific callback
                self.callbacks[topic] = [cb for cb in self.callbacks[topic] if cb != callback]
                if not self.callbacks[topic]:
                    self.topics.discard(topic)
            
            # Send unsubscribe message if connected
            if self.connected:
                try:
                    unsubscribe_msg = json.dumps({
                        "action": "unsubscribe",
                        "topic": topic
                    })
                    self.ws.send(unsubscribe_msg)
                    logger.info(f"Unsubscribed from topic: {topic}")
                except Exception as e:
                    logger.error(f"Error unsubscribing from topic '{topic}': {e}")
    
    def disconnect(self):
        """
        Disconnect from the WebSocket server
        """
        if self.ws:
            self.ws.close()
            self.connected = False
            logger.info("Disconnected from WebSocket server")

# Singleton instance
_websocket_client = None

def get_websocket_client() -> WebSocketClient:
    """
    Get the WebSocket client instance (singleton)
    
    Returns:
        WebSocket client instance
    """
    global _websocket_client
    if _websocket_client is None:
        _websocket_client = WebSocketClient()
    return _websocket_client
