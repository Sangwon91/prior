"""Tests for client module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from adapter.client import (
    WebSocketEventPublisher,
    WebSocketEventSubscriber,
)
from protocol.models import (
    ControlCommand,
    NodeProgress,
    WorkflowEvent,
    WorkflowStarted,
)


@pytest.mark.asyncio
async def test_websocket_event_publisher_connect():
    """Test WebSocket event publisher connect."""
    publisher = WebSocketEventPublisher("ws://localhost:8000/ws/agent")

    with patch("adapter.client.websockets.connect") as mock_connect:
        mock_websocket = AsyncMock()

        # Make connect return an awaitable that returns the websocket
        async def connect_side_effect(*args, **kwargs):
            return mock_websocket

        mock_connect.side_effect = connect_side_effect

        await publisher.connect()

        assert publisher._connected is True
        assert publisher._websocket == mock_websocket
        mock_connect.assert_called_once_with("ws://localhost:8000/ws/agent")


@pytest.mark.asyncio
async def test_websocket_event_publisher_disconnect():
    """Test WebSocket event publisher disconnect."""
    publisher = WebSocketEventPublisher("ws://localhost:8000/ws/agent")
    mock_websocket = AsyncMock()
    publisher._websocket = mock_websocket
    publisher._connected = True

    await publisher.disconnect()

    assert publisher._connected is False
    assert publisher._websocket is None
    mock_websocket.close.assert_called_once()


@pytest.mark.asyncio
async def test_websocket_event_publisher_publish_event():
    """Test WebSocket event publisher publish event."""
    publisher = WebSocketEventPublisher("ws://localhost:8000/ws/agent")
    mock_websocket = AsyncMock()
    publisher._websocket = mock_websocket
    publisher._connected = True

    event = WorkflowEvent(
        workflow_id="test-123",
        event_type="started",
        data=WorkflowStarted(workflow_id="test-123"),
    )

    await publisher.publish_workflow_event(event)

    mock_websocket.send.assert_called_once()
    # Verify JSON was sent
    call_args = mock_websocket.send.call_args[0][0]
    assert "test-123" in call_args


@pytest.mark.asyncio
async def test_websocket_event_subscriber_connect():
    """Test WebSocket event subscriber connect."""
    subscriber = WebSocketEventSubscriber("ws://localhost:8000/ws/tui")

    with patch("adapter.client.websockets.connect") as mock_connect:
        mock_websocket = AsyncMock()

        # Make connect return an awaitable that returns the websocket
        async def connect_side_effect(*args, **kwargs):
            return mock_websocket

        mock_connect.side_effect = connect_side_effect

        await subscriber.connect()

        assert subscriber._connected is True
        assert subscriber._websocket == mock_websocket
        mock_connect.assert_called_once_with("ws://localhost:8000/ws/tui")


@pytest.mark.asyncio
async def test_websocket_event_subscriber_disconnect():
    """Test WebSocket event subscriber disconnect."""
    subscriber = WebSocketEventSubscriber("ws://localhost:8000/ws/tui")
    mock_websocket = AsyncMock()
    subscriber._websocket = mock_websocket
    subscriber._connected = True

    await subscriber.disconnect()

    assert subscriber._connected is False
    assert subscriber._websocket is None
    mock_websocket.close.assert_called_once()


@pytest.mark.asyncio
async def test_websocket_event_subscriber_send_command():
    """Test WebSocket event subscriber send command."""
    subscriber = WebSocketEventSubscriber("ws://localhost:8000/ws/tui")
    mock_websocket = AsyncMock()
    subscriber._websocket = mock_websocket
    subscriber._connected = True

    command = ControlCommand(workflow_id="test-123", command="cancel")

    await subscriber.send_command(command)

    mock_websocket.send.assert_called_once()
    # Verify JSON was sent
    call_args = mock_websocket.send.call_args[0][0]
    assert "test-123" in call_args
    assert "cancel" in call_args
