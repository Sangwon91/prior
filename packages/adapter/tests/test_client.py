"""Tests for client module."""

import asyncio

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from adapter.client import AdapterClient
from protocol.models import ChatMessage


@pytest.mark.asyncio
async def test_adapter_client_connect():
    """Test adapter client connect."""
    client = AdapterClient("ws://localhost:8000/ws/agent")

    with patch("adapter.client.websockets.connect") as mock_connect:
        mock_websocket = AsyncMock()

        # Make connect return an awaitable that returns the websocket
        async def connect_side_effect(*args, **kwargs):
            return mock_websocket

        mock_connect.side_effect = connect_side_effect

        await client.connect()

        assert client._connected is True
        assert client._websocket == mock_websocket
        mock_connect.assert_called_once_with("ws://localhost:8000/ws/agent")


@pytest.mark.asyncio
async def test_adapter_client_disconnect():
    """Test adapter client disconnect."""
    client = AdapterClient("ws://localhost:8000/ws/agent")
    mock_websocket = AsyncMock()
    client._websocket = mock_websocket
    client._connected = True

    # Create a real task that can be cancelled
    async def dummy_task():
        await asyncio.sleep(1)

    client._receive_task = asyncio.create_task(dummy_task())

    await client.disconnect()

    assert client._connected is False
    assert client._websocket is None
    assert client._receive_task is None
    mock_websocket.close.assert_called_once()


@pytest.mark.asyncio
async def test_adapter_client_send():
    """Test adapter client send message."""
    client = AdapterClient("ws://localhost:8000/ws/agent")
    mock_websocket = AsyncMock()
    client._websocket = mock_websocket
    client._connected = True

    message = ChatMessage(role="user", content="Hello")

    await client.send(message)

    mock_websocket.send.assert_called_once()
    # Verify JSON was sent
    call_args = mock_websocket.send.call_args[0][0]
    assert "Hello" in call_args


@pytest.mark.asyncio
async def test_adapter_client_receive():
    """Test adapter client receive messages."""
    client = AdapterClient("ws://localhost:8000/ws/agent")
    client._connected = True

    # Manually put a message in the queue to test receive()
    test_message = ChatMessage(role="assistant", content="Hi")
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
