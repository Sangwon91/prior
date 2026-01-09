"""Tests for bridge module."""

import pytest

from adapter.bridge import Bridge
from protocol.models import (
    ControlCommand,
    NodeProgress,
    WorkflowEvent,
    WorkflowStarted,
)


@pytest.mark.asyncio
async def test_bridge_publish_event():
    """Test bridge publishes events."""
    bridge = Bridge()
    event = WorkflowEvent(
        workflow_id="test-123",
        event_type="started",
        data=WorkflowStarted(workflow_id="test-123"),
    )

    await bridge.publish_event(event)

    # Check event is in queue
    received_event = await bridge._event_queue.get()
    assert received_event.workflow_id == "test-123"
    assert received_event.event_type == "started"


@pytest.mark.asyncio
async def test_bridge_event_subscriber():
    """Test bridge event subscriber."""
    bridge = Bridge()
    event = WorkflowEvent(
        workflow_id="test-123",
        event_type="progress",
        data=NodeProgress(
            workflow_id="test-123",
            node_id="node-1",
            state="running",
        ),
    )

    # Create subscriber
    subscriber = bridge.create_event_subscriber()

    # Publish event
    await bridge.publish_event(event)

    # Receive event
    received_event = await anext(subscriber)
    assert received_event.workflow_id == "test-123"
    assert received_event.event_type == "progress"


@pytest.mark.asyncio
async def test_bridge_multiple_subscribers():
    """Test bridge with multiple subscribers."""
    bridge = Bridge()
    event = WorkflowEvent(
        workflow_id="test-123",
        event_type="started",
        data=WorkflowStarted(workflow_id="test-123"),
    )

    # Create multiple subscribers
    subscriber1 = bridge.create_event_subscriber()
    subscriber2 = bridge.create_event_subscriber()

    # Publish event
    await bridge.publish_event(event)

    # Both should receive event
    event1 = await anext(subscriber1)
    event2 = await anext(subscriber2)

    assert event1.workflow_id == "test-123"
    assert event2.workflow_id == "test-123"


@pytest.mark.asyncio
async def test_bridge_register_command_handler():
    """Test bridge command handler registration."""
    bridge = Bridge()

    handled_commands = []

    class TestHandler:
        async def handle_command(self, command: ControlCommand) -> None:
            handled_commands.append(command)

    handler = TestHandler()
    bridge.register_command_handler("test-123", handler)

    command = ControlCommand(workflow_id="test-123", command="cancel")
    await bridge.handle_command(command)

    assert len(handled_commands) == 1
    assert handled_commands[0].workflow_id == "test-123"
    assert handled_commands[0].command == "cancel"


@pytest.mark.asyncio
async def test_bridge_unregister_command_handler():
    """Test bridge command handler unregistration."""
    bridge = Bridge()

    handled_commands = []

    class TestHandler:
        async def handle_command(self, command: ControlCommand) -> None:
            handled_commands.append(command)

    handler = TestHandler()
    bridge.register_command_handler("test-123", handler)

    # Unregister
    bridge.unregister_command_handler("test-123")

    command = ControlCommand(workflow_id="test-123", command="cancel")
    await bridge.handle_command(command)

    # Should not be handled
    assert len(handled_commands) == 0


@pytest.mark.asyncio
async def test_bridge_get_events():
    """Test bridge get_events method."""
    bridge = Bridge()
    event = WorkflowEvent(
        workflow_id="test-123",
        event_type="started",
        data=WorkflowStarted(workflow_id="test-123"),
    )

    await bridge.publish_event(event)

    # Get events
    received_event = await anext(bridge.get_events())
    assert received_event.workflow_id == "test-123"
