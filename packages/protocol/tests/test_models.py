"""Tests for protocol models."""

import pytest

from protocol.models import ChatMessage


def test_chat_message_user():
    """Test ChatMessage with user role."""
    message = ChatMessage(role="user", content="Hello")
    assert message.role == "user"
    assert message.content == "Hello"
    assert message.timestamp is not None


def test_chat_message_assistant():
    """Test ChatMessage with assistant role."""
    message = ChatMessage(role="assistant", content="Hi there")
    assert message.role == "assistant"
    assert message.content == "Hi there"


def test_chat_message_system():
    """Test ChatMessage with system role."""
    message = ChatMessage(role="system", content="System message")
    assert message.role == "system"
    assert message.content == "System message"


def test_chat_message_timestamp():
    """Test ChatMessage timestamp generation."""
    message1 = ChatMessage(role="user", content="First")
    message2 = ChatMessage(role="user", content="Second")
    # Timestamps should be different (or very close)
    assert message1.timestamp is not None
    assert message2.timestamp is not None


def test_json_serialization():
    """Test JSON serialization of ChatMessage."""
    message = ChatMessage(role="user", content="Test message")
    json_str = message.model_dump_json()
    assert isinstance(json_str, str)
    assert "Test message" in json_str
    assert "user" in json_str

    # Test deserialization
    parsed = ChatMessage.model_validate_json(json_str)
    assert parsed.role == message.role
    assert parsed.content == message.content


def test_json_deserialization():
    """Test JSON deserialization of ChatMessage."""
    json_str = (
        '{"role":"assistant","content":"Hello world","timestamp":1234567890.0}'
    )
    message = ChatMessage.model_validate_json(json_str)
    assert message.role == "assistant"
    assert message.content == "Hello world"
    assert message.timestamp == 1234567890.0
