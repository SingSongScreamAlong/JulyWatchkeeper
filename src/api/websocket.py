"""
WebSocket API for WATCHKEEPER

This module provides WebSocket endpoints for real-time updates from the WATCHKEEPER intelligence platform.
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, Any, List, Set

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, Query
from pydantic import BaseModel

from src.utils.logger import get_logger

# Initialize logger
logger = get_logger("watchkeeper.api.websocket")

class ConnectionManager:
    """
    WebSocket connection manager
    
    Manages active WebSocket connections and broadcasts messages to connected clients.
    """
    
    def __init__(self):
        """Initialize the connection manager"""
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.client_subscriptions: Dict[WebSocket, Set[str]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """
        Connect a new WebSocket client
        
        Args:
            websocket: WebSocket connection
            client_id: Client identifier
        """
        await websocket.accept()
        
        if client_id not in self.active_connections:
            self.active_connections[client_id] = []
        
        self.active_connections[client_id].append(websocket)
        self.client_subscriptions[websocket] = set()
        
        logger.info(f"Client {client_id} connected")
    
    def disconnect(self, websocket: WebSocket, client_id: str):
        """
        Disconnect a WebSocket client
        
        Args:
            websocket: WebSocket connection
            client_id: Client identifier
        """
        if client_id in self.active_connections:
            if websocket in self.active_connections[client_id]:
                self.active_connections[client_id].remove(websocket)
                
                if not self.active_connections[client_id]:
                    del self.active_connections[client_id]
        
        if websocket in self.client_subscriptions:
            del self.client_subscriptions[websocket]
        
        logger.info(f"Client {client_id} disconnected")
    
    async def subscribe(self, websocket: WebSocket, topic: str):
        """
        Subscribe a client to a topic
        
        Args:
            websocket: WebSocket connection
            topic: Topic to subscribe to
        """
        if websocket in self.client_subscriptions:
            self.client_subscriptions[websocket].add(topic)
            await websocket.send_json({
                "type": "subscription",
                "status": "success",
                "topic": topic,
                "message": f"Subscribed to {topic}"
            })
            
            logger.debug(f"Client subscribed to {topic}")
    
    async def unsubscribe(self, websocket: WebSocket, topic: str):
        """
        Unsubscribe a client from a topic
        
        Args:
            websocket: WebSocket connection
            topic: Topic to unsubscribe from
        """
        if websocket in self.client_subscriptions and topic in self.client_subscriptions[websocket]:
            self.client_subscriptions[websocket].remove(topic)
            await websocket.send_json({
                "type": "subscription",
                "status": "success",
                "topic": topic,
                "message": f"Unsubscribed from {topic}"
            })
            
            logger.debug(f"Client unsubscribed from {topic}")
    
    async def broadcast(self, topic: str, message: Dict[str, Any]):
        """
        Broadcast a message to all clients subscribed to a topic
        
        Args:
            topic: Topic to broadcast to
            message: Message to broadcast
        """
        # Add metadata to the message
        message["topic"] = topic
        message["timestamp"] = datetime.now().isoformat()
        
        # Broadcast to all subscribed clients
        for websocket, subscriptions in self.client_subscriptions.items():
            if topic in subscriptions:
                try:
                    await websocket.send_json(message)
                except Exception as e:
                    logger.error(f"Error broadcasting message: {e}", exc_info=True)
        
        logger.debug(f"Broadcast message to topic {topic}")

# Create connection manager
manager = ConnectionManager()

def setup_websocket_routes(app: FastAPI):
    """
    Set up WebSocket routes for the FastAPI application
    
    Args:
        app: FastAPI application
    """
    
    @app.websocket("/ws/{client_id}")
    async def websocket_endpoint(websocket: WebSocket, client_id: str):
        """
        WebSocket endpoint for real-time updates
        
        Args:
            websocket: WebSocket connection
            client_id: Client identifier
        """
        await manager.connect(websocket, client_id)
        
        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()
                
                try:
                    # Parse message as JSON
                    message = json.loads(data)
                    
                    # Handle message based on type
                    if message.get("type") == "subscribe" and "topic" in message:
                        await manager.subscribe(websocket, message["topic"])
                    
                    elif message.get("type") == "unsubscribe" and "topic" in message:
                        await manager.unsubscribe(websocket, message["topic"])
                    
                    elif message.get("type") == "ping":
                        # Respond to ping
                        await websocket.send_json({
                            "type": "pong",
                            "timestamp": datetime.now().isoformat()
                        })
                    
                    else:
                        # Unknown message type
                        await websocket.send_json({
                            "type": "error",
                            "message": "Unknown message type or missing required fields"
                        })
                
                except json.JSONDecodeError:
                    # Invalid JSON
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid JSON message"
                    })
                
                except Exception as e:
                    # Other error
                    logger.error(f"Error handling WebSocket message: {e}", exc_info=True)
                    await websocket.send_json({
                        "type": "error",
                        "message": "Error processing message"
                    })
        
        except WebSocketDisconnect:
            # Client disconnected
            manager.disconnect(websocket, client_id)
        
        except Exception as e:
            # Other error
            logger.error(f"WebSocket error: {e}", exc_info=True)
            manager.disconnect(websocket, client_id)

# Function to broadcast intelligence updates
async def broadcast_intelligence_update(item_id: str, item_data: Dict[str, Any]):
    """
    Broadcast an intelligence update to subscribed clients
    
    Args:
        item_id: ID of the intelligence item
        item_data: Intelligence item data
    """
    # Broadcast to all clients subscribed to intelligence updates
    await manager.broadcast("intelligence", {
        "type": "intelligence_update",
        "item_id": item_id,
        "title": item_data.get("title", ""),
        "source": item_data.get("source", {}),
        "severity": item_data.get("severity_assessment", {}).get("score", 0),
        "relevance": item_data.get("relevance_assessment", {}).get("score", 0),
        "summary": item_data.get("ai_analysis", {}).get("summary", ""),
        "url": item_data.get("url", "")
    })

# Function to broadcast system status updates
async def broadcast_system_status(status: Dict[str, Any]):
    """
    Broadcast a system status update to subscribed clients
    
    Args:
        status: System status information
    """
    # Broadcast to all clients subscribed to system status updates
    await manager.broadcast("system", {
        "type": "system_status",
        "status": status
    })

# Function to broadcast alerts
async def broadcast_alert(alert_type: str, message: str, data: Dict[str, Any] = None):
    """
    Broadcast an alert to subscribed clients
    
    Args:
        alert_type: Type of alert (info, warning, error)
        message: Alert message
        data: Additional alert data
    """
    # Broadcast to all clients subscribed to alerts
    await manager.broadcast("alerts", {
        "type": "alert",
        "alert_type": alert_type,
        "message": message,
        "data": data or {}
    })
