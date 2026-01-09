"""FastAPI WebSocket server for adapter."""

import asyncio

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from .bridge import Bridge
from .connection_manager import ConnectionManager
from protocol.models import ChatMessage


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

        Agent sends and receives chat messages.

        Args:
            websocket: WebSocket connection
        """
        await manager.connect(websocket)
        try:
            # Agent sends messages
            async def receive_from_agent():
                async for message in manager.receive_messages(websocket):
                    try:
                        chat_message = ChatMessage.model_validate_json(message)
                        await bridge.send(chat_message)
                    except Exception:
                        pass  # Ignore invalid messages

            # Agent receives messages
            async def send_to_agent():
                async for message in bridge.create_subscriber():
                    json_data = message.model_dump_json()
                    await manager.send_personal_message(json_data, websocket)

            await asyncio.gather(
                receive_from_agent(),
                send_to_agent(),
            )
        except WebSocketDisconnect:
            manager.disconnect(websocket)

    @app.websocket("/ws/tui")
    async def websocket_tui(websocket: WebSocket) -> None:
        """
        WebSocket endpoint for TUI connections.

        TUI sends and receives chat messages.

        Args:
            websocket: WebSocket connection
        """
        await manager.connect(websocket)
        try:
            # TUI receives messages from Agent
            async def send_to_tui():
                async for message in bridge.create_subscriber():
                    json_data = message.model_dump_json()
                    await manager.send_personal_message(json_data, websocket)

            # TUI sends messages to Agent
            async def receive_from_tui():
                async for message in manager.receive_messages(websocket):
                    try:
                        chat_message = ChatMessage.model_validate_json(message)
                        await bridge.send(chat_message)
                    except Exception:
                        pass  # Ignore invalid messages

            await asyncio.gather(
                send_to_tui(),
                receive_from_tui(),
            )
        except WebSocketDisconnect:
            manager.disconnect(websocket)

    return app
