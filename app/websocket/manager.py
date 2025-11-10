"""WebSocket Manager for Real-Time Updates

Handles real-time communication for:
- Alert notifications
- Personnel location updates
- Incident reports
- Intelligence updates
"""

from fastapi import WebSocket
from typing import List, Dict, Set
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages WebSocket connections"""

    def __init__(self):
        # Active connections by user_id
        self.active_connections: Dict[int, List[WebSocket]] = {}

        # Subscriptions by topic
        self.subscriptions: Dict[str, Set[int]] = {
            'alerts': set(),
            'intelligence': set(),
            'incidents': set(),
            'personnel_tracking': set(),
            'system_status': set()
        }

    async def connect(self, websocket: WebSocket, user_id: int):
        """Accept new WebSocket connection"""
        await websocket.accept()

        if user_id not in self.active_connections:
            self.active_connections[user_id] = []

        self.active_connections[user_id].append(websocket)
        logger.info(f"User {user_id} connected via WebSocket")

        # Send welcome message
        await websocket.send_json({
            'type': 'connection_established',
            'user_id': user_id,
            'timestamp': datetime.utcnow().isoformat(),
            'available_topics': list(self.subscriptions.keys())
        })

    def disconnect(self, websocket: WebSocket, user_id: int):
        """Remove WebSocket connection"""
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)

            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

                # Remove from all subscriptions
                for topic in self.subscriptions.values():
                    topic.discard(user_id)

        logger.info(f"User {user_id} disconnected from WebSocket")

    async def subscribe(self, user_id: int, topic: str):
        """Subscribe user to a topic"""
        if topic in self.subscriptions:
            self.subscriptions[topic].add(user_id)
            logger.info(f"User {user_id} subscribed to {topic}")
            return True
        return False

    async def unsubscribe(self, user_id: int, topic: str):
        """Unsubscribe user from a topic"""
        if topic in self.subscriptions:
            self.subscriptions[topic].discard(user_id)
            logger.info(f"User {user_id} unsubscribed from {topic}")
            return True
        return False

    async def send_personal_message(self, message: dict, user_id: int):
        """Send message to specific user"""
        if user_id in self.active_connections:
            message['timestamp'] = datetime.utcnow().isoformat()

            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")

    async def broadcast_to_topic(self, topic: str, message: dict):
        """Broadcast message to all subscribers of a topic"""
        if topic not in self.subscriptions:
            return

        message['topic'] = topic
        message['timestamp'] = datetime.utcnow().isoformat()

        subscribers = self.subscriptions[topic]

        for user_id in subscribers:
            await self.send_personal_message(message, user_id)

        logger.info(f"Broadcast to {len(subscribers)} subscribers on topic '{topic}'")

    async def broadcast_alert(self, alert: dict):
        """Broadcast new alert"""
        await self.broadcast_to_topic('alerts', {
            'type': 'new_alert',
            'alert': alert
        })

    async def broadcast_intelligence(self, intelligence: dict):
        """Broadcast new intelligence item"""
        await self.broadcast_to_topic('intelligence', {
            'type': 'new_intelligence',
            'intelligence': intelligence
        })

    async def broadcast_incident(self, incident: dict):
        """Broadcast new incident"""
        await self.broadcast_to_topic('incidents', {
            'type': 'new_incident',
            'incident': incident
        })

    async def broadcast_location_update(self, personnel_id: int, location: dict):
        """Broadcast personnel location update"""
        await self.broadcast_to_topic('personnel_tracking', {
            'type': 'location_update',
            'personnel_id': personnel_id,
            'location': location
        })

    async def broadcast_system_status(self, status: dict):
        """Broadcast system status update"""
        await self.broadcast_to_topic('system_status', {
            'type': 'system_status',
            'status': status
        })


# Singleton instance
manager = ConnectionManager()
