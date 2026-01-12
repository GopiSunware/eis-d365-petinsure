"""
WebSocket Manager - Native WebSocket support for real-time updates
Replaces Socket.IO with FastAPI's built-in WebSocket
"""

from fastapi import WebSocket
from typing import Dict, Set
import logging
import json

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections and broadcasting."""

    def __init__(self):
        # Store active connections: {connection_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, connection_id: str):
        """Accept and store a new WebSocket connection."""
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        logger.info(f"WebSocket connected: {connection_id}. Total connections: {len(self.active_connections)}")

    def disconnect(self, connection_id: str):
        """Remove a WebSocket connection."""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            logger.info(f"WebSocket disconnected: {connection_id}. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, connection_id: str):
        """Send a message to a specific connection."""
        if connection_id in self.active_connections:
            try:
                await self.active_connections[connection_id].send_json(message)
                logger.debug(f"Sent message to {connection_id}: {message.get('type')}")
            except Exception as e:
                logger.error(f"Error sending to {connection_id}: {e}")
                self.disconnect(connection_id)

    async def broadcast(self, message: dict):
        """Broadcast a message to all connected clients."""
        disconnected = []
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_json(message)
                logger.debug(f"Broadcast to {connection_id}: {message.get('type')}")
            except Exception as e:
                logger.error(f"Error broadcasting to {connection_id}: {e}")
                disconnected.append(connection_id)

        # Clean up disconnected clients
        for connection_id in disconnected:
            self.disconnect(connection_id)

    async def emit(self, event: str, data: dict, room: str = None):
        """
        Emit an event to all connected clients.
        Mimics Socket.IO's emit() API for easier migration.
        Note: room parameter is accepted but ignored (broadcasts to all)
        """
        message = {
            "type": event,
            "data": data
        }
        await self.broadcast(message)

    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)
