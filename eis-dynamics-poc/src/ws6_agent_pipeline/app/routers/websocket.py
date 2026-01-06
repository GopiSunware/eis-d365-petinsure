"""
WebSocket router for real-time pipeline event streaming.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from ..orchestration import event_publisher

logger = logging.getLogger(__name__)

router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept and register a WebSocket connection."""
        await websocket.accept()
        self.active_connections[client_id] = websocket
        logger.info(f"WebSocket connected: {client_id}")

    def disconnect(self, client_id: str):
        """Remove a WebSocket connection."""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            logger.info(f"WebSocket disconnected: {client_id}")

    async def send_personal_message(self, message: str, client_id: str):
        """Send a message to a specific client."""
        if client_id in self.active_connections:
            try:
                await self.active_connections[client_id].send_text(message)
            except Exception as e:
                logger.error(f"Error sending to {client_id}: {e}")
                self.disconnect(client_id)

    async def broadcast(self, message: str):
        """Broadcast a message to all connected clients."""
        disconnected = []
        for client_id, connection in self.active_connections.items():
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                disconnected.append(client_id)

        # Clean up disconnected clients
        for client_id in disconnected:
            self.disconnect(client_id)


manager = ConnectionManager()


@router.websocket("/ws/events")
async def websocket_events(websocket: WebSocket, run_id: Optional[str] = None):
    """
    WebSocket endpoint for streaming pipeline events.

    Query params:
        run_id: Optional run ID to filter events (if not provided, receives all events)
    """
    # Generate client ID
    client_id = f"ws-{datetime.utcnow().strftime('%Y%m%d%H%M%S%f')}"

    await manager.connect(websocket, client_id)

    # Subscribe to events
    subscriber_id, event_queue = event_publisher.subscribe(client_id)

    try:
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "connected",
            "client_id": client_id,
            "run_id_filter": run_id,
            "timestamp": datetime.utcnow().isoformat(),
        }))

        # Stream events
        while True:
            try:
                # Wait for events with timeout
                event = await asyncio.wait_for(event_queue.get(), timeout=30.0)

                if event is None:
                    # Publisher closed
                    break

                # Filter by run_id if specified
                if run_id and event.run_id != run_id:
                    continue

                # Send event to client
                message = json.dumps({
                    "type": "event",
                    "event": event.model_dump(),
                    "timestamp": datetime.utcnow().isoformat(),
                }, default=str)

                await websocket.send_text(message)

            except asyncio.TimeoutError:
                # Send heartbeat
                await websocket.send_text(json.dumps({
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat(),
                }))

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {client_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        event_publisher.unsubscribe(subscriber_id)
        manager.disconnect(client_id)


@router.websocket("/ws/run/{run_id}")
async def websocket_run_events(websocket: WebSocket, run_id: str):
    """
    WebSocket endpoint for streaming events for a specific pipeline run.
    """
    # Use the general events endpoint with run_id filter
    await websocket_events(websocket, run_id=run_id)


@router.get("/ws/connections")
async def get_active_connections():
    """
    Get count of active WebSocket connections.
    """
    return {
        "active_connections": len(manager.active_connections),
        "client_ids": list(manager.active_connections.keys()),
    }
