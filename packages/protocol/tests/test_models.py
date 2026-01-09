"""Tests for protocol models."""

import pytest

from protocol.models import ChatMessage


def test_chat_message_creates_user_message_with_timestamp():
    """Test ChatMessage creates user message with automatic timestamp."""
    message = ChatMessage(role="user", content="Hello")
    assert message.role == "user"
    assert message.content == "Hello"
    assert message.timestamp is not None


def test_chat_message_creates_assistant_message():
    """Test ChatMessage creates assistant message correctly."""
    message = ChatMessage(role="assistant", content="Hi there")
    assert message.role == "assistant"
    assert message.content == "Hi there"


def test_chat_message_creates_system_message():
    """Test ChatMessage creates system message correctly."""
    message = ChatMessage(role="system", content="System message")
    assert message.role == "system"
    assert message.content == "System message"


def test_chat_message_generates_timestamp_on_creation():
    """Test ChatMessage generates timestamp automatically on creation."""
    message1 = ChatMessage(role="user", content="First")
    message2 = ChatMessage(role="user", content="Second")
    # Timestamps should be generated
    assert message1.timestamp is not None
    assert message2.timestamp is not None


def test_chat_message_serializes_and_deserializes_to_json():
    """Test ChatMessage can be serialized to JSON and deserialized back."""
    message = ChatMessage(role="user", content="Test message")
    json_str = message.model_dump_json()
    assert isinstance(json_str, str)
    assert "Test message" in json_str
    assert "user" in json_str

    # Test deserialization preserves data
    parsed = ChatMessage.model_validate_json(json_str)
    assert parsed.role == message.role
    assert parsed.content == message.content


def test_chat_message_deserializes_from_json_string():
    """Test ChatMessage can be deserialized from JSON string."""
    json_str = (
        '{"role":"assistant","content":"Hello world","timestamp":1234567890.0}'
    )
    message = ChatMessage.model_validate_json(json_str)
    assert message.role == "assistant"
    assert message.content == "Hello world"
    assert message.timestamp == 1234567890.0
