"""Tests for connection manager module."""

import pytest
from unittest.mock import AsyncMock, MagicMock

from adapter.connection_manager import ConnectionManager


@pytest.mark.asyncio
async def test_connection_manager_connect():
    """Test connection manager connect."""
    manager = ConnectionManager()
    mock_websocket = AsyncMock()

    await manager.connect(mock_websocket)

    assert mock_websocket in manager.active_connections
    mock_websocket.accept.assert_called_once()


@pytest.mark.asyncio
async def test_connection_manager_disconnect():
    """Test connection manager disconnect."""
    manager = ConnectionManager()
    mock_websocket = AsyncMock()

    await manager.connect(mock_websocket)
    assert len(manager.active_connections) == 1

    manager.disconnect(mock_websocket)
    assert len(manager.active_connections) == 0


@pytest.mark.asyncio
async def test_connection_manager_send_personal_message():
    """Test connection manager send personal message."""
    manager = ConnectionManager()
    mock_websocket = AsyncMock()

    await manager.connect(mock_websocket)
    await manager.send_personal_message("test message", mock_websocket)

    mock_websocket.send_text.assert_called_once_with("test message")


@pytest.mark.asyncio
async def test_connection_manager_broadcast():
    """Test connection manager broadcast."""
    manager = ConnectionManager()
    mock_websocket1 = AsyncMock()
    mock_websocket2 = AsyncMock()

    await manager.connect(mock_websocket1)
    await manager.connect(mock_websocket2)

    await manager.broadcast("test message")

    mock_websocket1.send_text.assert_called_once_with("test message")
    mock_websocket2.send_text.assert_called_once_with("test message")


@pytest.mark.asyncio
async def test_connection_manager_broadcast_removes_failed():
    """Test connection manager removes failed connections."""
    manager = ConnectionManager()
    mock_websocket1 = AsyncMock()
    mock_websocket2 = AsyncMock()

    # Make second websocket raise exception
    mock_websocket2.send_text.side_effect = Exception("Connection error")

    await manager.connect(mock_websocket1)
    await manager.connect(mock_websocket2)

    await manager.broadcast("test message")

    # First should succeed
    mock_websocket1.send_text.assert_called_once_with("test message")
    # Second should be removed
    assert mock_websocket2 not in manager.active_connections


@pytest.mark.asyncio
async def test_connection_manager_receive_messages():
    """Test connection manager receive messages."""
    manager = ConnectionManager()
    mock_websocket = AsyncMock()

    # Setup mock to yield messages then raise exception
    messages = ["message1", "message2"]

    async def receive_text():
        if messages:
            return messages.pop(0)
        raise Exception("Connection closed")

    mock_websocket.receive_text = receive_text

    received = []
    async for message in manager.receive_messages(mock_websocket):
        received.append(message)

    assert received == ["message1", "message2"]
