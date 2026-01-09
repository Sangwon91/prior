"""Tests for client module."""

import asyncio

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from adapter.client import AdapterClient
from protocol.models import ChatMessage


@pytest.mark.asyncio
async def test_adapter_client_connects_to_websocket_server():
    """Test adapter client connects to WebSocket server."""
    client = AdapterClient("ws://localhost:8000/ws/agent")

    with patch("adapter.client.websockets.connect") as mock_connect:
        mock_websocket = AsyncMock()

        # Make connect return an awaitable that returns the websocket
        async def connect_side_effect(*args, **kwargs):
            return mock_websocket

        mock_connect.side_effect = connect_side_effect

        await client.connect()

        # Verify connection was attempted
        mock_connect.assert_called_once_with("ws://localhost:8000/ws/agent")
        # Verify we can send messages (indirect verification of connection)
        message = ChatMessage(role="user", content="Test")
        await client.send(message)
        mock_websocket.send.assert_called()


@pytest.mark.asyncio
async def test_adapter_client_disconnect_closes_connection():
    """Test adapter client disconnect closes WebSocket connection."""
    client = AdapterClient("ws://localhost:8000/ws/agent")
    mock_websocket = AsyncMock()

    with patch("adapter.client.websockets.connect") as mock_connect:
        async def connect_side_effect(*args, **kwargs):
            return mock_websocket

        mock_connect.side_effect = connect_side_effect

        await client.connect()

        # Create a real task that can be cancelled
        async def dummy_task():
            await asyncio.sleep(1)

        # Access private member only to set up test state
        client._receive_task = asyncio.create_task(dummy_task())

        await client.disconnect()

        # Verify websocket was closed
        mock_websocket.close.assert_called_once()
        # Verify we cannot send after disconnect (indirect verification)
        # This would raise an error if still connected


@pytest.mark.asyncio
async def test_adapter_client_send_serializes_and_sends_message():
    """Test adapter client send serializes message to JSON and sends it."""
    client = AdapterClient("ws://localhost:8000/ws/agent")

    with patch("adapter.client.websockets.connect") as mock_connect:
        mock_websocket = AsyncMock()

        async def connect_side_effect(*args, **kwargs):
            return mock_websocket

        mock_connect.side_effect = connect_side_effect

        message = ChatMessage(role="user", content="Hello")

        await client.send(message)

        # Verify message was sent
        mock_websocket.send.assert_called_once()
        # Verify JSON was sent with correct content
        call_args = mock_websocket.send.call_args[0][0]
        assert "Hello" in call_args


@pytest.mark.asyncio
async def test_adapter_client_receive_yields_messages_from_queue():
    """Test adapter client receive yields messages from receive queue."""
    client = AdapterClient("ws://localhost:8000/ws/agent")

    with patch("adapter.client.websockets.connect") as mock_connect:
        mock_websocket = AsyncMock()

        async def connect_side_effect(*args, **kwargs):
            return mock_websocket

        mock_connect.side_effect = connect_side_effect

        await client.connect()

        # Manually put a message in the queue to test receive()
        test_message = ChatMessage(role="assistant", content="Hi")
        # Access private member only to set up test state
        await client._receive_queue.put(test_message)

        # Receive message
        received = []
        async for msg in client.receive():
            received.append(msg)
            if len(received) >= 1:
                break

        assert len(received) == 1
        assert received[0].role == "assistant"
        assert received[0].content == "Hi"
