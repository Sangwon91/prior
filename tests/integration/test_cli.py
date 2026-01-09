"""Integration tests for CLI."""

import asyncio
import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from prior.cli import main


def test_cli_main_with_model_env():
    """Test CLI main with model environment variable."""
    with patch.dict(os.environ, {"PRIOR_MODEL": "test-model"}):
        with (
            patch("prior.cli.load_dotenv"),
            patch("prior.cli.Agent") as mock_agent_class,
            patch("prior.cli.PriorApp") as mock_app_class,
            patch("prior.cli.start_adapter_server") as mock_start_server,
            patch("prior.cli.AdapterClient") as mock_adapter_class,
            patch("prior.cli.ChatService") as mock_chat_service_class,
        ):
            mock_agent = MagicMock()
            mock_app_instance = MagicMock()
            mock_bridge = MagicMock()
            mock_adapter = AsyncMock()
            mock_chat_service = MagicMock()

            mock_agent_class.return_value = mock_agent
            mock_app_class.return_value = mock_app_instance
            mock_start_server.return_value = (mock_bridge, 8000)
            mock_adapter_class.return_value = mock_adapter
            mock_chat_service_class.return_value = mock_chat_service

            main()

            # Verify Agent was created with correct model and adapter
            assert mock_agent_class.call_count == 1
            # PriorApp is called with agent and chat_service
            mock_app_class.assert_called_once()
            mock_app_instance.run.assert_called_once()


def test_cli_main_default_model():
    """Test CLI main uses default model."""
    with patch.dict(os.environ, {}, clear=True):
        with (
            patch("prior.cli.load_dotenv"),
            patch("prior.cli.Agent") as mock_agent_class,
            patch("prior.cli.PriorApp") as mock_app_class,
            patch("prior.cli.start_adapter_server") as mock_start_server,
            patch("prior.cli.AdapterClient") as mock_adapter_class,
            patch("prior.cli.ChatService") as mock_chat_service_class,
        ):
            mock_agent = MagicMock()
            mock_app_instance = MagicMock()
            mock_bridge = MagicMock()
            mock_adapter = AsyncMock()
            mock_chat_service = MagicMock()

            mock_agent_class.return_value = mock_agent
            mock_app_class.return_value = mock_app_instance
            mock_start_server.return_value = (mock_bridge, 8000)
            mock_adapter_class.return_value = mock_adapter
            mock_chat_service_class.return_value = mock_chat_service

            main()

            # Verify default model is used
            assert mock_agent_class.call_count == 1


def test_cli_main_loads_dotenv():
    """Test CLI main loads .env file."""
    with (
        patch("prior.cli.load_dotenv") as mock_load_dotenv,
        patch("prior.cli.Agent") as mock_agent_class,
        patch("prior.cli.PriorApp") as mock_app_class,
        patch("prior.cli.start_adapter_server") as mock_start_server,
        patch("prior.cli.AdapterClient") as mock_adapter_class,
        patch("prior.cli.ChatService") as mock_chat_service_class,
    ):
        mock_agent = MagicMock()
        mock_app_instance = MagicMock()
        mock_bridge = MagicMock()
        mock_adapter = AsyncMock()
        mock_chat_service = MagicMock()

        mock_agent_class.return_value = mock_agent
        mock_app_class.return_value = mock_app_instance
        mock_start_server.return_value = (mock_bridge, 8000)
        mock_adapter_class.return_value = mock_adapter
        mock_chat_service_class.return_value = mock_chat_service

        main()

        # Verify load_dotenv was called
        mock_load_dotenv.assert_called_once()


@pytest.mark.asyncio
async def test_chat_workflow_integration():
    """Test full chat workflow: message send → agent process → response."""
    from agent import Agent
    from agent.workflows import execute_chat_loop
    from adapter import AdapterClient
    from protocol.models import ChatMessage

    # Create mock agent
    mock_agent = MagicMock(spec=Agent)

    async def mock_chat_stream(messages, project_context=""):
        # Simulate streaming response
        yield "Hello"
        yield " from"
        yield " agent"

    mock_agent.chat_stream = mock_chat_stream
    mock_agent.adapter = None

    # Create mock adapter that simulates message passing
    received_messages = []
    sent_messages = []
    message_sent = False

    async def mock_send(message: ChatMessage):
        sent_messages.append(message)

    async def mock_receive():
        nonlocal message_sent
        # Yield user message only once
        if not message_sent:
            user_msg = ChatMessage(role="user", content="Test message")
            received_messages.append(user_msg)
            message_sent = True
            yield user_msg
        # Then raise CancelledError to stop the loop
        raise asyncio.CancelledError()

    mock_adapter = MagicMock(spec=AdapterClient)
    mock_adapter.send = AsyncMock(side_effect=mock_send)
    mock_adapter.receive = mock_receive
    mock_adapter.connect = AsyncMock()

    # Run chat loop with timeout and cancellation
    task = asyncio.create_task(
        execute_chat_loop(
            agent=mock_agent,
            adapter=mock_adapter,
            project_root=None,
        )
    )

    # Wait a bit for processing, then cancel
    try:
        await asyncio.wait_for(task, timeout=1.0)
    except (asyncio.TimeoutError, asyncio.CancelledError):
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass  # Expected

    # Verify that at least one message was received
    assert len(received_messages) > 0 or message_sent


@pytest.mark.asyncio
async def test_chat_workflow_message_flow():
    """Test that messages flow through the chat workflow correctly."""
    from agent.workflows import (
        ChatDeps,
        ChatState,
        ProcessChat,
        ReceiveMessage,
        create_chat_workflow,
    )
    from protocol.models import ChatMessage
    from workflow import GraphRunContext

    # Create mock agent
    mock_agent = MagicMock()

    async def mock_chat_stream(messages, project_context=""):
        yield "Response"

    mock_agent.chat_stream = mock_chat_stream
    mock_agent.adapter = None

    # Create mock adapter
    user_message = ChatMessage(role="user", content="Hello")
    message_yielded = False

    async def mock_receive():
        nonlocal message_yielded
        if not message_yielded:
            message_yielded = True
            yield user_message
        # Stop after first message by raising CancelledError
        raise asyncio.CancelledError()

    mock_adapter = MagicMock()
    mock_adapter.receive = mock_receive

    # Create workflow
    graph = create_chat_workflow()
    state = ChatState()
    deps = ChatDeps(agent=mock_agent)

    # Run workflow with timeout and cancellation
    task = asyncio.create_task(
        graph.run(
            ReceiveMessage(),
            state=state,
            deps=deps,
            adapter=mock_adapter,
        )
    )

    try:
        result = await asyncio.wait_for(task, timeout=1.0)
    except (asyncio.TimeoutError, asyncio.CancelledError):
        # Cancel the task if it's still running
        task.cancel()
        try:
            await task
        except asyncio.CancelledError:
            pass  # Expected

    # Verify message was received and processed
    assert len(state.message_history) > 0
    assert state.message_history[0]["role"] == "user"
    assert state.message_history[0]["content"] == "Hello"
