"""Tests for bridge module."""

import pytest

from adapter.bridge import Bridge
from protocol.models import ChatMessage


@pytest.mark.asyncio
async def test_bridge_send_makes_message_available_via_get_messages():
    """Test bridge send makes messages available via get_messages."""
    bridge = Bridge()
    message = ChatMessage(role="user", content="Hello")

    await bridge.send(message)

    # Verify message is available through public API
    received_message = await anext(bridge.get_messages())
    assert received_message.role == "user"
    assert received_message.content == "Hello"


@pytest.mark.asyncio
async def test_bridge_subscriber_receives_sent_messages():
    """Test bridge subscriber receives messages sent via send."""
    bridge = Bridge()
    message = ChatMessage(role="assistant", content="Hi there")

    # Create subscriber
    subscriber = bridge.create_subscriber()

    # Send message
    await bridge.send(message)

    # Receive message
    received_message = await anext(subscriber)
    assert received_message.role == "assistant"
    assert received_message.content == "Hi there"


@pytest.mark.asyncio
async def test_bridge_multiple_subscribers():
    """Test bridge with multiple subscribers."""
    bridge = Bridge()
    message = ChatMessage(role="user", content="Test message")

    # Create multiple subscribers
    subscriber1 = bridge.create_subscriber()
    subscriber2 = bridge.create_subscriber()

    # Send message
    await bridge.send(message)

    # Both should receive message
    msg1 = await anext(subscriber1)
    msg2 = await anext(subscriber2)

    assert msg1.content == "Test message"
    assert msg2.content == "Test message"


@pytest.mark.asyncio
async def test_bridge_get_messages_returns_sent_messages():
    """Test bridge get_messages returns messages sent via send."""
    bridge = Bridge()
    message = ChatMessage(role="system", content="System message")

    await bridge.send(message)

    # Get messages
    received_message = await anext(bridge.get_messages())
    assert received_message.content == "System message"
