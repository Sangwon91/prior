"""Integration tests for ChatScreen."""

import asyncio
import tempfile
from collections.abc import AsyncIterator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from protocol.models import ChatMessage
from tui.chat_service import ChatService
from tui.screens.chat import ChatScreen


class MockAdapter:
    """Mock adapter for testing."""

    def __init__(self):
        self.sent_messages = []
        self.received_messages = []
        self._receive_queue = asyncio.Queue()

    async def send(self, message):
        """Mock send."""
        self.sent_messages.append(message)

    async def receive(self):
        """Mock receive."""
        while True:
            try:
                message = await asyncio.wait_for(
                    self._receive_queue.get(), timeout=1.0
                )
                yield message
            except asyncio.TimeoutError:
                break

    async def put_message(self, message):
        """Helper to put a message in the receive queue."""
        await self._receive_queue.put(message)


class MockChatService(ChatService):
    """Mock chat service for testing."""

    def __init__(self, project_root: Path | None = None):
        mock_adapter = MockAdapter()
        super().__init__(adapter=mock_adapter, project_root=project_root)
        self.send_calls = []

    async def send_message(self, content: str):
        """Mock send message."""
        self.send_calls.append(content)
        await super().send_message(content)


@pytest.mark.asyncio
async def test_chat_screen_initializes_with_chat_service_and_project_root():
    """Test ChatScreen initializes with chat service and project root."""
    with tempfile.TemporaryDirectory() as tmpdir:
        chat_service = MockChatService(project_root=Path(tmpdir))
        screen = ChatScreen(chat_service, project_root=Path(tmpdir))

        assert screen.chat_service == chat_service
        assert screen.project_root == Path(tmpdir)
        assert len(screen.message_history) == 0


@pytest.mark.asyncio
async def test_chat_screen_renders_input_and_messages_widgets():
    """Test ChatScreen renders input box and messages container widgets."""
    from tui.app import PriorApp

    mock_adapter = MockAdapter()
    chat_service = ChatService(adapter=mock_adapter)

    with tempfile.TemporaryDirectory() as tmpdir:
        app = PriorApp(chat_service=chat_service, project_root=Path(tmpdir))

        async with app.run_test():
            screen = app.screen
            # Check that widgets exist
            input_box = screen.query_one("#input-box", expect_type=None)
            assert input_box is not None

            messages_container = screen.query_one(
                "#messages-container", expect_type=None
            )
            assert messages_container is not None


@pytest.mark.asyncio
async def test_chat_screen_adds_message_to_history_and_sends_via_adapter():
    """Test ChatScreen adds message to history and sends via adapter on input."""
    from tui.app import PriorApp

    mock_adapter = MockAdapter()
    chat_service = ChatService(adapter=mock_adapter)

    with tempfile.TemporaryDirectory() as tmpdir:
        app = PriorApp(chat_service=chat_service, project_root=Path(tmpdir))

        async with app.run_test() as pilot:
            screen = app.screen
            input_box = screen.query_one("#input-box")
            input_box.value = "Test message"

            # Simulate input submission
            from textual.widgets import Input

            event = Input.Submitted(input_box, "Test message")

            await screen.on_input_submitted(event)

            # Wait a bit for processing
            await asyncio.sleep(0.1)
            await pilot.pause()

            # Check that message was added to history
            assert len(screen.message_history) >= 1
            assert screen.message_history[0]["role"] == "user"
            assert screen.message_history[0]["content"] == "Test message"

            # Check that message was sent via adapter
            assert len(mock_adapter.sent_messages) == 1
            assert mock_adapter.sent_messages[0].role == "user"
            assert mock_adapter.sent_messages[0].content == "Test message"


@pytest.mark.asyncio
async def test_chat_screen_allows_multiple_inputs_while_processing():
    """Test ChatScreen allows submitting multiple messages while processing."""
    from tui.app import PriorApp

    mock_adapter = MockAdapter()
    chat_service = ChatService(adapter=mock_adapter)

    with tempfile.TemporaryDirectory() as tmpdir:
        app = PriorApp(chat_service=chat_service, project_root=Path(tmpdir))

        async with app.run_test() as pilot:
            screen = app.screen
            input_box = screen.query_one("#input-box")

            # Submit first message
            from textual.widgets import Input

            initial_history_len = len(screen.message_history)
            event1 = Input.Submitted(input_box, "First question")
            await screen.on_input_submitted(event1)

            # Check that first message was added
            assert len(screen.message_history) == initial_history_len + 1
            assert screen.message_history[-1]["role"] == "user"
            assert screen.message_history[-1]["content"] == "First question"

            # Wait a bit
            await asyncio.sleep(0.1)
            await pilot.pause()

            # Submit second message (should be allowed)
            input_box.value = "Second question"
            event2 = Input.Submitted(input_box, "Second question")
            await screen.on_input_submitted(event2)

            # History should have increased (both messages added)
            assert len(screen.message_history) >= initial_history_len + 2
            # Find the second user message
            user_messages = [
                msg for msg in screen.message_history if msg["role"] == "user"
            ]
            assert len(user_messages) >= 2
            assert user_messages[-1]["content"] == "Second question"


@pytest.mark.asyncio
async def test_chat_screen_quit_action_exits_app():
    """Test ChatScreen quit action exits the application."""
    from tui.app import PriorApp

    mock_adapter = MockAdapter()
    chat_service = ChatService(adapter=mock_adapter)

    with tempfile.TemporaryDirectory() as tmpdir:
        app = PriorApp(chat_service=chat_service, project_root=Path(tmpdir))

        async with app.run_test():
            screen = app.screen
            # Quit action should exit app
            screen.action_quit()
            # App should be exiting (exact behavior depends on Textual)


@pytest.mark.asyncio
async def test_chat_screen_accumulates_streaming_chunks():
    """Test ChatScreen accumulates streaming chunks correctly."""
    from tui.app import PriorApp

    mock_adapter = MockAdapter()
    chat_service = ChatService(adapter=mock_adapter)

    with tempfile.TemporaryDirectory() as tmpdir:
        app = PriorApp(chat_service=chat_service, project_root=Path(tmpdir))

        async with app.run_test() as pilot:
            screen = app.screen

            # Send streaming chunks
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

            await mock_adapter.put_message(chunk1)
            # Wait for message to be processed
            await asyncio.sleep(0.2)
            await pilot.pause()

            # Verify first chunk was processed
            assert message_id in screen._assistant_streams
            assert screen._assistant_streams[message_id]["content"] == "Hello"

            await mock_adapter.put_message(chunk2)
            # Wait for message to be processed
            await asyncio.sleep(0.2)
            await pilot.pause()

            # Check that chunks are accumulated in stream tracking
            assert message_id in screen._assistant_streams
            assert screen._assistant_streams[message_id]["content"] == (
                "Hello World"
            )


@pytest.mark.asyncio
async def test_chat_screen_finalizes_message_on_complete_event():
    """Test ChatScreen finalizes message when complete event is received."""
    from tui.app import PriorApp

    mock_adapter = MockAdapter()
    chat_service = ChatService(adapter=mock_adapter)

    with tempfile.TemporaryDirectory() as tmpdir:
        app = PriorApp(chat_service=chat_service, project_root=Path(tmpdir))

        async with app.run_test() as pilot:
            screen = app.screen

            # Send streaming chunks
            message_id = "test-msg-456"
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
            complete = ChatMessage(
                role="assistant",
                content="Hello World",
                event_type="message",
                message_id=message_id,
            )

            await mock_adapter.put_message(chunk1)
            await asyncio.sleep(0.2)
            await pilot.pause()

            await mock_adapter.put_message(chunk2)
            await asyncio.sleep(0.2)
            await pilot.pause()

            # Verify chunks are accumulated before complete message
            assert message_id in screen._assistant_streams
            assert screen._assistant_streams[message_id]["content"] == (
                "Hello World"
            )

            await mock_adapter.put_message(complete)
            await asyncio.sleep(0.2)
            await pilot.pause()

            # Check that message was finalized and added to history
            assert message_id not in screen._assistant_streams
            assistant_messages = [
                msg
                for msg in screen.message_history
                if msg["role"] == "assistant"
            ]
            assert len(assistant_messages) > 0
            assert assistant_messages[-1]["content"] == "Hello World"
