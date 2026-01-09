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
    GetProjectTree,
    ProcessChat,
    ProjectState,
    ReceiveMessage,
    create_chat_workflow,
    create_project_analysis_workflow,
    execute_chat_loop,
    execute_project_analysis,
)
from protocol.models import ChatMessage


@pytest.mark.asyncio
async def test_create_project_analysis_workflow_executes_successfully():
    """Test project analysis workflow executes and returns results."""
    graph = create_project_analysis_workflow()

    # Verify workflow can execute and return results
    with tempfile.TemporaryDirectory() as tmpdir:
        root = Path(tmpdir)
        (root / "file1.py").write_text("# test")

        result = await graph.run(
            GetProjectTree(project_root=root),
            state=ProjectState(),
        )

        # Verify workflow executed successfully
        assert result.output is not None
        assert "file_count" in result.output
        assert "total_lines" in result.output


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
async def test_create_chat_workflow_processes_messages():
    """Test chat workflow processes messages correctly."""
    graph = create_chat_workflow()

    # Verify workflow can execute with mock adapter
    mock_adapter = AsyncMock()
    user_message = ChatMessage(role="user", content="Hello")
    call_count = 0

    async def mock_receive():
        nonlocal call_count
        call_count += 1
        # First call: yield message
        if call_count == 1:
            yield user_message
        # Subsequent calls: raise CancelledError to stop
        # This prevents infinite loop when ProcessChat returns ReceiveMessage
        raise asyncio.CancelledError()

    mock_adapter.receive = mock_receive

    mock_agent = MagicMock()

    async def mock_chat_stream(messages, project_context=""):
        yield "Response"

    mock_agent.chat_stream = mock_chat_stream
    mock_agent.adapter = None

    state = ChatState()
    deps = ChatDeps(agent=mock_agent)

    # Run workflow with timeout to prevent infinite wait
    # ProcessChat returns ReceiveMessage, which will try to receive again
    # but mock_receive() raises CancelledError, causing workflow to stop
    try:
        result = await asyncio.wait_for(
            graph.run(
                ReceiveMessage(),
                state=state,
                deps=deps,
                adapter=mock_adapter,
            ),
            timeout=1.0,
        )
    except (asyncio.TimeoutError, asyncio.CancelledError):
        # Expected - workflow stops when no more messages
        pass

    # Verify message was processed
    assert len(state.message_history) > 0
    assert state.message_history[0]["role"] == "user"
    assert state.message_history[0]["content"] == "Hello"


@pytest.mark.asyncio
async def test_receive_message_node_receives_and_stores_user_message():
    """Test ReceiveMessage node receives user messages and stores them."""
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
async def test_receive_message_node_returns_end_when_no_adapter():
    """Test ReceiveMessage node returns End node when adapter is missing."""
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
async def test_process_chat_node_processes_message_and_updates_history():
    """Test ProcessChat node processes messages with agent and updates history."""
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
async def test_process_chat_node_returns_end_when_deps_missing():
    """Test ProcessChat node returns End node when dependencies are missing."""
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
async def test_process_chat_node_returns_end_when_no_current_message():
    """Test ProcessChat node returns End node when current message is missing."""
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
async def test_execute_chat_loop_returns_immediately_when_no_adapter():
    """Test execute_chat_loop returns immediately when adapter is missing."""
    mock_agent = MagicMock()

    # Should return immediately if no adapter
    await execute_chat_loop(agent=mock_agent, adapter=None)

    # Agent should not be called
    assert not mock_agent.chat_stream.called


@pytest.mark.asyncio
async def test_execute_chat_loop_receives_and_processes_messages():
    """Test execute_chat_loop receives messages and processes them with agent."""
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
