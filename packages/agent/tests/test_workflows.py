"""Tests for agent workflows."""

from __future__ import annotations

import asyncio
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from agent.workflows import (
    ChatDeps,
    ChatState,
    ProcessChat,
    ReceiveMessage,
    create_chat_workflow,
    create_project_analysis_workflow,
    execute_chat_loop,
    execute_project_analysis,
)
from protocol.models import ChatMessage


@pytest.mark.asyncio
async def test_create_project_analysis_workflow():
    """Test creating project analysis workflow."""
    graph = create_project_analysis_workflow()

    # Graph should have the node classes
    assert len(graph.node_defs) == 2


@pytest.mark.asyncio
async def test_execute_project_analysis():
    """Test executing project analysis workflow."""
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)

        # Create some test files
        (root / "file1.py").write_text("# test")
        (root / "file2.txt").write_text("test")
        (root / "subdir").mkdir()
        (root / "subdir" / "file3.py").write_text("# test")

        result = await execute_project_analysis(root)

        # Check results
        assert result is not None
        assert "file_count" in result
        assert result["file_count"] > 0
        assert "total_lines" in result
        assert "tree" in result
        assert "file1.py" in result["tree"]


@pytest.mark.asyncio
async def test_create_chat_workflow():
    """Test creating chat workflow."""
    graph = create_chat_workflow()

    # Graph should have the node classes
    assert len(graph.node_defs) == 2
    assert ReceiveMessage in graph.node_defs
    assert ProcessChat in graph.node_defs


@pytest.mark.asyncio
async def test_receive_message_node():
    """Test ReceiveMessage node receives user messages."""
    from workflow import GraphRunContext

    # Create mock adapter
    mock_adapter = AsyncMock()
    user_message = ChatMessage(role="user", content="Hello")

    async def mock_receive():
        yield user_message

    # Set receive to return the async generator directly
    mock_adapter.receive = mock_receive

    # Create state and context
    state = ChatState()
    deps = ChatDeps(agent=MagicMock())
    ctx = GraphRunContext(state=state, deps=deps, adapter=mock_adapter)

    # Create and run node
    node = ReceiveMessage()
    result = await node.run(ctx)

    # Check that message was received
    assert ctx.state.current_message == user_message
    assert len(ctx.state.message_history) == 1
    assert ctx.state.message_history[0]["role"] == "user"
    assert ctx.state.message_history[0]["content"] == "Hello"
    assert isinstance(result, ProcessChat)


@pytest.mark.asyncio
async def test_receive_message_node_no_adapter():
    """Test ReceiveMessage node handles missing adapter."""
    from workflow import GraphRunContext

    # Create state and context without adapter
    state = ChatState()
    deps = ChatDeps(agent=MagicMock())
    ctx = GraphRunContext(state=state, deps=deps, adapter=None)

    # Create and run node
    node = ReceiveMessage()
    result = await node.run(ctx)

    # Should return End node
    from workflow import End

    assert isinstance(result, End)


@pytest.mark.asyncio
async def test_process_chat_node():
    """Test ProcessChat node processes messages with agent."""
    from workflow import GraphRunContext

    # Create mock agent
    mock_agent = MagicMock()

    async def mock_chat_stream(messages, project_context=""):
        yield "Hello"
        yield " World"

    # Set chat_stream to return the async generator directly
    mock_agent.chat_stream = mock_chat_stream
    mock_agent.adapter = None

    # Create mock adapter
    mock_adapter = AsyncMock()

    # Create state with current message
    state = ChatState()
    state.current_message = ChatMessage(role="user", content="Hi")
    state.message_history = [{"role": "user", "content": "Hi"}]

    deps = ChatDeps(agent=mock_agent)
    ctx = GraphRunContext(state=state, deps=deps, adapter=mock_adapter)

    # Create and run node
    node = ProcessChat()
    result = await node.run(ctx)

    # Check that message history was updated
    assert len(ctx.state.message_history) == 2
    assert ctx.state.message_history[1]["role"] == "assistant"
    assert ctx.state.message_history[1]["content"] == "Hello World"
    assert isinstance(result, ReceiveMessage)


@pytest.mark.asyncio
async def test_process_chat_node_no_deps():
    """Test ProcessChat node handles missing deps."""
    from workflow import GraphRunContext

    # Create state and context without deps
    state = ChatState()
    ctx = GraphRunContext(state=state, deps=None, adapter=MagicMock())

    # Create and run node
    node = ProcessChat()
    result = await node.run(ctx)

    # Should return End node
    from workflow import End

    assert isinstance(result, End)


@pytest.mark.asyncio
async def test_process_chat_node_no_message():
    """Test ProcessChat node handles missing current message."""
    from workflow import GraphRunContext

    # Create state without current message
    state = ChatState()
    deps = ChatDeps(agent=MagicMock())
    ctx = GraphRunContext(state=state, deps=deps, adapter=MagicMock())

    # Create and run node
    node = ProcessChat()
    result = await node.run(ctx)

    # Should return End node
    from workflow import End

    assert isinstance(result, End)


@pytest.mark.asyncio
async def test_execute_chat_loop_no_adapter():
    """Test execute_chat_loop handles missing adapter."""
    mock_agent = MagicMock()

    # Should return immediately if no adapter
    await execute_chat_loop(agent=mock_agent, adapter=None)

    # Agent should not be called
    assert not mock_agent.chat_stream.called


@pytest.mark.asyncio
async def test_execute_chat_loop_receives_and_processes():
    """Test execute_chat_loop receives and processes messages."""
    # Create mock agent
    mock_agent = MagicMock()

    async def mock_chat_stream(messages, project_context=""):
        yield "Response"

    mock_agent.chat_stream = mock_chat_stream
    mock_agent.adapter = None

    # Create mock adapter
    mock_adapter = AsyncMock()
    user_message = ChatMessage(role="user", content="Hello")

    message_count = 0

    async def mock_receive():
        nonlocal message_count
        if message_count == 0:
            message_count += 1
            yield user_message
        else:
            # Stop after first message to avoid infinite loop
            await asyncio.sleep(0.1)
            raise asyncio.CancelledError()

    # Set receive to return the async generator directly
    mock_adapter.receive = mock_receive

    # Run chat loop with timeout
    try:
        await asyncio.wait_for(
            execute_chat_loop(
                agent=mock_agent,
                adapter=mock_adapter,
                project_root=None,
            ),
            timeout=1.0,
        )
    except asyncio.TimeoutError:
        pass  # Expected, loop runs indefinitely
    except asyncio.CancelledError:
        pass  # Also expected

    # Check that at least one message was processed
    assert message_count > 0
