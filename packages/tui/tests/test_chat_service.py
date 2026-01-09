"""Tests for ChatService."""

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from protocol.models import ChatMessage
from tui.chat_service import ChatService


class MockAdapter:
    """Mock adapter for testing."""

    def __init__(self):
        self.sent_messages = []
        self._receive_queue = asyncio.Queue()

    async def send(self, message: ChatMessage) -> None:
        """Mock send."""
        self.sent_messages.append(message)

    async def receive(self) -> AsyncIterator[ChatMessage]:
        """Mock receive."""
        while True:
            try:
                message = await asyncio.wait_for(
                    self._receive_queue.get(), timeout=1.0
                )
                yield message
            except asyncio.TimeoutError:
                break

    async def put_message(self, message: ChatMessage) -> None:
        """Helper to put a message in the receive queue."""
        await self._receive_queue.put(message)


@pytest.mark.asyncio
async def test_chat_service_initializes_with_adapter_and_project_root():
    """Test ChatService initializes with adapter and project root."""
    mock_adapter = MockAdapter()
    project_root = Path("/test/project")

    service = ChatService(adapter=mock_adapter, project_root=project_root)

    assert service.adapter == mock_adapter
    assert service.project_root == project_root
    assert len(service.message_history) == 0
    assert len(service._assistant_streams) == 0


@pytest.mark.asyncio
async def test_chat_service_send_message_sends_via_adapter_and_adds_to_history():
    """Test ChatService send_message sends via adapter and adds to history."""
    mock_adapter = MockAdapter()
    service = ChatService(adapter=mock_adapter)

    await service.send_message("Hello")

    assert len(mock_adapter.sent_messages) == 1
    assert mock_adapter.sent_messages[0].role == "user"
    assert mock_adapter.sent_messages[0].content == "Hello"
    assert len(service.message_history) == 1
    assert service.message_history[0]["role"] == "user"
    assert service.message_history[0]["content"] == "Hello"


@pytest.mark.asyncio
async def test_chat_service_receive_messages_accumulates_chunks():
    """Test ChatService receive_messages accumulates streaming chunks."""
    mock_adapter = MockAdapter()
    service = ChatService(adapter=mock_adapter)

    message_id = "test-msg-123"
    chunk1 = ChatMessage(
        role="assistant",
        content="Hello",
        event_type="chunk",
        message_id=message_id,
    )
    chunk2 = ChatMessage(
        role="assistant",
        content=" World",
        event_type="chunk",
        message_id=message_id,
    )

    # Start receiving in background
    received_messages = []
    receive_task = asyncio.create_task(
        _collect_messages(service.receive_messages(), received_messages)
    )

    await mock_adapter.put_message(chunk1)
    await asyncio.sleep(0.2)

    # Verify chunk is accumulated but not yielded yet
    assert message_id in service._assistant_streams
    assert service._assistant_streams[message_id] == "Hello"
    assert len(received_messages) == 0

    await mock_adapter.put_message(chunk2)
    await asyncio.sleep(0.2)

    # Verify chunks are accumulated
    assert service._assistant_streams[message_id] == "Hello World"
    assert len(received_messages) == 0

    receive_task.cancel()
    try:
        await receive_task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_chat_service_receive_messages_yields_complete_message():
    """Test ChatService receive_messages yields complete message after chunks."""
    mock_adapter = MockAdapter()
    service = ChatService(adapter=mock_adapter)

    message_id = "test-msg-456"
    chunk1 = ChatMessage(
        role="assistant",
        content="Hello",
        event_type="chunk",
        message_id=message_id,
    )
    complete = ChatMessage(
        role="assistant",
        content="Hello World",
        event_type="message",
        message_id=message_id,
    )

    # Start receiving
    received_messages = []
    receive_task = asyncio.create_task(
        _collect_messages(service.receive_messages(), received_messages)
    )

    await mock_adapter.put_message(chunk1)
    await asyncio.sleep(0.2)

    # Chunk accumulated but not yielded
    assert len(received_messages) == 0

    await mock_adapter.put_message(complete)
    await asyncio.sleep(0.2)

    # Complete message should be yielded with accumulated content
    assert len(received_messages) == 1
    assert received_messages[0].role == "assistant"
    assert received_messages[0].content == "Hello"
    assert message_id not in service._assistant_streams
    assert len(service.message_history) == 1
    assert service.message_history[0]["content"] == "Hello"

    receive_task.cancel()
    try:
        await receive_task
    except asyncio.CancelledError:
        pass


@pytest.mark.asyncio
async def test_chat_service_get_message_history_returns_copy():
    """Test ChatService get_message_history returns a copy of history."""
    mock_adapter = MockAdapter()
    service = ChatService(adapter=mock_adapter)

    await service.send_message("Test")

    history = service.get_message_history()
    assert len(history) == 1
    assert history[0]["content"] == "Test"

    # Modify returned list should not affect service
    history.append({"role": "assistant", "content": "Response"})
    assert len(service.message_history) == 1


async def _collect_messages(
    message_iterator: AsyncIterator[ChatMessage],
    collected: list[ChatMessage],
) -> None:
    """Helper to collect messages from iterator."""
    try:
        async for message in message_iterator:
            collected.append(message)
    except asyncio.CancelledError:
        pass
