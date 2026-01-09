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
                    self._receive_queue.get(), timeout=0.1
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
async def test_chat_screen_initialization():
    """Test ChatScreen can be initialized."""
    with tempfile.TemporaryDirectory() as tmpdir:
        chat_service = MockChatService(project_root=Path(tmpdir))
        screen = ChatScreen(chat_service, project_root=Path(tmpdir))

        assert screen.chat_service == chat_service
        assert screen.project_root == Path(tmpdir)
        assert len(screen.message_history) == 0


@pytest.mark.asyncio
async def test_chat_screen_compose():
    """Test ChatScreen compose method."""
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
async def test_chat_screen_input_submission():
    """Test ChatScreen handles input submission."""
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
async def test_chat_screen_allows_multiple_inputs_during_streaming():
    """Test that input is allowed during streaming (multiple questions)."""
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
async def test_chat_screen_quit_action():
    """Test quit action."""
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
