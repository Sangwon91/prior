"""Adapter client for sending and receiving chat messages."""

import asyncio
import json
from collections.abc import AsyncIterator

import websockets
from websockets.client import WebSocketClientProtocol

from protocol.models import ChatMessage


class AdapterClient:
    """Simple adapter client for sending and receiving messages."""

    def __init__(self, uri: str):
        """
        Initialize adapter client.

        Args:
            uri: WebSocket server URI
        """
        self.uri = uri
        self._websocket: WebSocketClientProtocol | None = None
        self._connected = False
        self._receive_queue: asyncio.Queue[ChatMessage] = asyncio.Queue()
        self._receive_task: asyncio.Task | None = None

    async def connect(self) -> None:
        """Connect to WebSocket server."""
        if not self._connected:
            self._websocket = await websockets.connect(self.uri)
            self._connected = True
            # Start receiving messages in background
            self._receive_task = asyncio.create_task(self._receive_loop())

    async def disconnect(self) -> None:
        """Disconnect from WebSocket server."""
        if self._receive_task:
            self._receive_task.cancel()
            try:
                await self._receive_task
            except asyncio.CancelledError:
                pass
            self._receive_task = None

        if self._websocket:
            await self._websocket.close()
            self._connected = False
            self._websocket = None

    async def _receive_loop(self) -> None:
        """Background task to receive messages."""
        if not self._websocket:
            return

        try:
            async for message in self._websocket:
                try:
                    chat_message = ChatMessage.model_validate_json(message)
                    await self._receive_queue.put(chat_message)
                except Exception:
                    pass  # Ignore invalid messages
        except Exception:
            pass  # Connection closed

    async def send(self, message: ChatMessage) -> None:
        """
        Send a chat message.

        Args:
            message: Chat message to send
        """
        if not self._connected:
            await self.connect()

        if self._websocket:
            json_data = message.model_dump_json()
            await self._websocket.send(json_data)

    async def receive(self) -> AsyncIterator[ChatMessage]:
        """
        Receive chat messages.

        Yields:
            Chat messages as they arrive
        """
        if not self._connected:
            await self.connect()

        while True:
            try:
                message = await self._receive_queue.get()
                yield message
            except asyncio.CancelledError:
                break
            except Exception:
                break
