"""Connection manager for WebSocket connections."""

from collections.abc import AsyncIterator
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    """Manages WebSocket connections."""

    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """
        Accept and register a WebSocket connection.

        Args:
            websocket: WebSocket connection to register
        """
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket) -> None:
        """
        Unregister a WebSocket connection.

        Args:
            websocket: WebSocket connection to unregister
        """
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(
        self, message: str, websocket: WebSocket
    ) -> None:
        """
        Send a message to a specific WebSocket connection.

        Args:
            message: Message to send
            websocket: Target WebSocket connection
        """
        await websocket.send_text(message)

    async def broadcast(self, message: str) -> None:
        """
        Broadcast a message to all active connections.

        Args:
            message: Message to broadcast
        """
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception:
                disconnected.append(connection)

        for connection in disconnected:
            self.disconnect(connection)

    async def receive_messages(
        self, websocket: WebSocket
    ) -> AsyncIterator[str]:
        """
        Receive messages from a WebSocket connection.

        Args:
            websocket: WebSocket connection to receive from

        Yields:
            Received messages as text
        """
        while True:
            try:
                data = await websocket.receive_text()
                yield data
            except Exception:
                break
