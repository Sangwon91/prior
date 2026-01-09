"""WebSocket client implementations for Agent and TUI."""

import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any

import websockets
from websockets.client import WebSocketClientProtocol

from protocol.interfaces import EventPublisher, EventSubscriber
from protocol.models import ControlCommand, WorkflowEvent


class WebSocketEventPublisher:
    """WebSocket-based event publisher for Agent."""

    def __init__(self, uri: str):
        """
        Initialize WebSocket event publisher.

        Args:
            uri: WebSocket server URI (e.g., ws://localhost:8000/ws/agent)
        """
        self.uri = uri
        self._websocket: WebSocketClientProtocol | None = None
        self._connected = False

    async def connect(self) -> None:
        """Connect to WebSocket server."""
        if not self._connected:
            self._websocket = await websockets.connect(self.uri)
            self._connected = True

    async def disconnect(self) -> None:
        """Disconnect from WebSocket server."""
        if self._websocket:
            await self._websocket.close()
            self._connected = False
            self._websocket = None

    async def publish_workflow_event(self, event: WorkflowEvent) -> None:
        """
        Publish a workflow event.

        Args:
            event: Workflow event to publish
        """
        if not self._connected:
            await self.connect()

        if self._websocket:
            json_data = event.model_dump_json()
            await self._websocket.send(json_data)

    async def receive_commands(
        self,
    ) -> AsyncIterator[ControlCommand]:
        """
        Receive control commands.

        Yields:
            Control commands as they arrive
        """
        if not self._connected:
            await self.connect()

        if self._websocket:
            async for message in self._websocket:
                try:
                    # Check if message is a command or event
                    data = json.loads(message)
                    if "command" in data:
                        command = ControlCommand.model_validate_json(message)
                        yield command
                except Exception:
                    pass  # Ignore invalid messages


class WebSocketEventSubscriber:
    """WebSocket-based event subscriber for TUI."""

    def __init__(self, uri: str):
        """
        Initialize WebSocket event subscriber.

        Args:
            uri: WebSocket server URI (e.g., ws://localhost:8000/ws/tui)
        """
        self.uri = uri
        self._websocket: WebSocketClientProtocol | None = None
        self._connected = False

    async def connect(self) -> None:
        """Connect to WebSocket server."""
        if not self._connected:
            self._websocket = await websockets.connect(self.uri)
            self._connected = True

    async def disconnect(self) -> None:
        """Disconnect from WebSocket server."""
        if self._websocket:
            await self._websocket.close()
            self._connected = False
            self._websocket = None

    async def subscribe_workflow_events(
        self,
    ) -> AsyncIterator[WorkflowEvent]:
        """
        Subscribe to workflow events.

        Yields:
            Workflow events as they arrive
        """
        if not self._connected:
            await self.connect()

        if self._websocket:
            async for message in self._websocket:
                try:
                    event = WorkflowEvent.model_validate_json(message)
                    yield event
                except Exception:
                    pass  # Ignore invalid messages

    async def send_command(self, command: ControlCommand) -> None:
        """
        Send a control command.

        Args:
            command: Control command to send
        """
        if not self._connected:
            await self.connect()

        if self._websocket:
            json_data = command.model_dump_json()
            await self._websocket.send(json_data)
