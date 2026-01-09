"""Unit tests for Agent class."""

from unittest.mock import MagicMock, patch

import pytest

from agent import Agent


def test_agent_initialization():
    """Test Agent can be initialized."""
    agent = Agent(model="test-model")
    assert agent.model == "test-model"


def test_agent_default_model():
    """Test Agent uses default model."""
    agent = Agent()
    assert agent.model == "claude-sonnet-4-5"


@pytest.mark.asyncio
async def test_agent_chat_stream():
    """Test Agent chat_stream method."""
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

        assert chunks == ["Hello", " World"]


@pytest.mark.asyncio
async def test_agent_chat_stream_with_project_context():
    """Test Agent chat_stream includes project context."""
    agent = Agent(model="test-model")

    mock_chunk = MagicMock()
    mock_chunk.choices = [MagicMock()]
    mock_chunk.choices[0].delta = MagicMock()
    mock_chunk.choices[0].delta.content = "Response"

    async def mock_acompletion(*args, **kwargs):
        # Check that system message with project context is included
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

        assert len(chunks) > 0
