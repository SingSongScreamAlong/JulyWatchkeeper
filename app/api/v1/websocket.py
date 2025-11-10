"""WebSocket API Endpoints"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, Query
from ...websocket.manager import manager
from ...auth import get_current_user_from_token
import logging
import json

router = APIRouter()
logger = logging.getLogger(__name__)


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    """WebSocket endpoint for real-time updates"""

    # Authenticate user from token
    user = await get_current_user_from_token(token)
    if not user:
        await websocket.close(code=1008, reason="Authentication failed")
        return

    user_id = user.id if hasattr(user, 'id') else 0

    await manager.connect(websocket, user_id)

    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            message = json.loads(data)

            # Handle different message types
            msg_type = message.get('type')

            if msg_type == 'subscribe':
                topic = message.get('topic')
                await manager.subscribe(user_id, topic)
                await websocket.send_json({
                    'type': 'subscribed',
                    'topic': topic
                })

            elif msg_type == 'unsubscribe':
                topic = message.get('topic')
                await manager.unsubscribe(user_id, topic)
                await websocket.send_json({
                    'type': 'unsubscribed',
                    'topic': topic
                })

            elif msg_type == 'ping':
                await websocket.send_json({
                    'type': 'pong',
                    'timestamp': message.get('timestamp')
                })

    except WebSocketDisconnect:
        manager.disconnect(websocket, user_id)
        logger.info(f"Client {user_id} disconnected")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket, user_id)
