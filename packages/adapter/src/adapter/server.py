"""FastAPI WebSocket server for adapter."""

import asyncio
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .bridge import Bridge
from .connection_manager import ConnectionManager
from protocol.models import ControlCommand, WorkflowEvent


def create_app(bridge: Bridge | None = None) -> FastAPI:
    """
    Create FastAPI application with WebSocket endpoints.

    Args:
        bridge: Bridge instance (creates new if None)

    Returns:
        FastAPI application
    """
    if bridge is None:
        bridge = Bridge()

    app = FastAPI(title="Prior Adapter")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    manager = ConnectionManager()

    @app.websocket("/ws/agent")
    async def websocket_agent(websocket: WebSocket) -> None:
        """
        WebSocket endpoint for Agent connections.

        Agent publishes events and receives commands.

        Args:
            websocket: WebSocket connection
        """
        await manager.connect(websocket)
        try:
            # Handle both events and commands from Agent
            async for message in manager.receive_messages(websocket):
                try:
                    # Try to parse as event first
                    try:
                        event = WorkflowEvent.model_validate_json(message)
                        await bridge.publish_event(event)
                        continue
                    except Exception:
                        pass

                    # Try to parse as command
                    try:
                        command = ControlCommand.model_validate_json(message)
                        await bridge.handle_command(command)
                    except Exception:
                        pass  # Ignore invalid messages
                except Exception:
                    pass  # Ignore invalid messages
        except WebSocketDisconnect:
            manager.disconnect(websocket)

    @app.websocket("/ws/tui")
    async def websocket_tui(websocket: WebSocket) -> None:
        """
        WebSocket endpoint for TUI connections.

        TUI receives events and sends commands.

        Args:
            websocket: WebSocket connection
        """
        await manager.connect(websocket)
        try:
            # TUI receives events from Agent
            async def send_events():
                async for event in bridge.create_event_subscriber():
                    json_data = event.model_dump_json()
                    await manager.send_personal_message(json_data, websocket)

            # TUI sends commands to Agent
            async def receive_commands():
                async for message in manager.receive_messages(websocket):
                    try:
                        command = ControlCommand.model_validate_json(message)
                        await bridge.handle_command(command)
                    except Exception:
                        pass  # Ignore invalid messages

            await asyncio.gather(
                send_events(),
                receive_commands(),
            )
        except WebSocketDisconnect:
            manager.disconnect(websocket)

    return app
