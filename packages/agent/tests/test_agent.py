"""Unit tests for Agent class."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent import Agent
from protocol.models import ChatMessage


def test_agent_initializes_with_custom_model():
    """Test Agent initializes with specified model."""
    agent = Agent(model="test-model")
    assert agent.model == "test-model"


def test_agent_uses_default_model_when_no_model_specified():
    """Test Agent uses default model when no model is specified."""
    agent = Agent()
    assert agent.model == "claude-sonnet-4-5"


@pytest.mark.asyncio
async def test_agent_chat_stream_yields_response_chunks():
    """Test Agent chat_stream yields response chunks correctly."""
    agent = Agent(model="test-model")

    # Mock LiteLLM response
    mock_chunk1 = MagicMock()
    mock_chunk1.choices = [MagicMock()]
    mock_chunk1.choices[0].delta = MagicMock()
    mock_chunk1.choices[0].delta.content = "Hello"

    mock_chunk2 = MagicMock()
    mock_chunk2.choices = [MagicMock()]
    mock_chunk2.choices[0].delta = MagicMock()
    mock_chunk2.choices[0].delta.content = " World"

    async def mock_acompletion(*args, **kwargs):
        async def gen():
            yield mock_chunk1
            yield mock_chunk2

        return gen()

    with patch("agent.agent.acompletion", side_effect=mock_acompletion):
        messages = [{"role": "user", "content": "Test"}]
        chunks = []
        async for chunk in agent.chat_stream(messages):
            chunks.append(chunk)

        # Verify we received all chunks
        assert len(chunks) == 2
        assert "".join(chunks) == "Hello World"


@pytest.mark.asyncio
async def test_agent_chat_stream_includes_project_context_in_system_message():
    """Test Agent chat_stream includes project context as system message."""
    agent = Agent(model="test-model")

    mock_chunk = MagicMock()
    mock_chunk.choices = [MagicMock()]
    mock_chunk.choices[0].delta = MagicMock()
    mock_chunk.choices[0].delta.content = "Response"

    async def mock_acompletion(*args, **kwargs):
        # Verify that system message with project context is included
        messages = kwargs.get("messages", [])
        assert len(messages) > 0
        assert messages[0]["role"] == "system"
        assert "project structure" in messages[0]["content"].lower()

        async def gen():
            yield mock_chunk

        return gen()

    with patch("agent.agent.acompletion", side_effect=mock_acompletion):
        messages = [{"role": "user", "content": "Test"}]
        chunks = []
        async for chunk in agent.chat_stream(
            messages, project_context="test/context"
        ):
            chunks.append(chunk)

        # Verify response was received
        assert len(chunks) > 0
        assert "Response" in chunks


@pytest.mark.asyncio
async def test_agent_chat_stream_sends_chunks_via_adapter_with_event_type():
    """Test Agent chat_stream sends chunks via adapter with event_type."""
    mock_adapter = AsyncMock()
    agent = Agent(model="test-model", adapter=mock_adapter)

    mock_chunk1 = MagicMock()
    mock_chunk1.choices = [MagicMock()]
    mock_chunk1.choices[0].delta = MagicMock()
    mock_chunk1.choices[0].delta.content = "Hello"

    mock_chunk2 = MagicMock()
    mock_chunk2.choices = [MagicMock()]
    mock_chunk2.choices[0].delta = MagicMock()
    mock_chunk2.choices[0].delta.content = " World"

    async def mock_acompletion(*args, **kwargs):
        async def gen():
            yield mock_chunk1
            yield mock_chunk2

        return gen()

    with patch("agent.agent.acompletion", side_effect=mock_acompletion):
        messages = [{"role": "user", "content": "Test"}]
        chunks = []
        async for chunk in agent.chat_stream(messages):
            chunks.append(chunk)

        # Verify chunks were sent via adapter with event_type="chunk"
        assert (
            mock_adapter.send.call_count == 3
        )  # 2 chunks + 1 complete message

        # Check chunk messages
        chunk_calls = [
            call
            for call in mock_adapter.send.call_args_list
            if call[0][0].event_type == "chunk"
        ]
        assert len(chunk_calls) == 2

        # Verify all chunks have same message_id
        message_ids = [call[0][0].message_id for call in chunk_calls]
        assert len(set(message_ids)) == 1  # All same message_id

        # Check complete message
        complete_calls = [
            call
            for call in mock_adapter.send.call_args_list
            if call[0][0].event_type == "message"
        ]
        assert len(complete_calls) == 1
        complete_message = complete_calls[0][0][0]
        assert complete_message.content == "Hello World"
        assert complete_message.message_id == message_ids[0]
