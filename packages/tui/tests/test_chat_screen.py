"""Integration tests for ChatScreen."""

import asyncio
import tempfile
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest

from tui.chat_service import ChatService
from tui.screens.chat import ChatScreen


class MockAgent:
    """Mock agent implementing AgentProtocol for testing."""

    def __init__(self):
        self.chat_calls = []

    async def chat_stream(
        self, messages: list[dict[str, Any]], project_context: str = ""
    ) -> AsyncIterator[str]:
        """Mock streaming response."""
        self.chat_calls.append((messages, project_context))
        # Yield some test chunks
        for chunk in ["Hello", " ", "World"]:
            yield chunk


class MockChatService(ChatService):
    """Mock chat service for testing."""

    def __init__(self, project_root: Path | None = None):
        agent = MockAgent()
        super().__init__(agent, project_root)
        self.stream_calls = []

    async def stream_response(self, messages):
        """Mock streaming response."""
        self.stream_calls.append(messages)
        # Yield some test chunks
        for chunk in ["Hello", " ", "World"]:
            yield chunk


@pytest.mark.asyncio
async def test_chat_screen_initialization():
    """Test ChatScreen can be initialized."""
    with tempfile.TemporaryDirectory() as tmpdir:
        chat_service = MockChatService(project_root=Path(tmpdir))
        screen = ChatScreen(chat_service, project_root=Path(tmpdir))

        assert screen.chat_service == chat_service
        assert screen.project_root == Path(tmpdir)
        assert len(screen.message_history) == 0
        # Check that no streaming tasks are active
        assert len(screen._active_streaming_tasks) == 0


@pytest.mark.asyncio
async def test_chat_screen_compose():
    """Test ChatScreen compose method."""
    from tui.app import PriorApp

    agent = MockAgent()

    with tempfile.TemporaryDirectory() as tmpdir:
        app = PriorApp(agent, project_root=Path(tmpdir))

        async with app.run_test():
            screen = app.screen
            # Check that widgets exist
            input_box = screen.query_one("#input-box", expect_type=None)
            assert input_box is not None

            messages_container = screen.query_one(
                "#messages-container", expect_type=None
            )
            assert messages_container is not None

            # streaming-message widget is created dynamically during streaming
            # so it won't exist initially


@pytest.mark.asyncio
async def test_chat_screen_input_submission():
    """Test ChatScreen handles input submission."""
    from tui.app import PriorApp

    agent = MockAgent()

    with tempfile.TemporaryDirectory() as tmpdir:
        app = PriorApp(agent, project_root=Path(tmpdir))

        async with app.run_test() as pilot:
            screen = app.screen
            input_box = screen.query_one("#input-box")
            input_box.value = "Test message"

            # Simulate input submission
            from textual.widgets import Input

            event = Input.Submitted(input_box, "Test message")

            await screen.on_input_submitted(event)

            # Wait for streaming to complete (with timeout)
            import asyncio

            for _ in range(20):  # Try up to 20 times
                await asyncio.sleep(0.1)
                await pilot.pause()
                # Check if streaming tasks are done
                if len(screen._active_streaming_tasks) == 0:
                    break

            # Check that message was added to history
            assert len(screen.message_history) >= 1  # at least user message
            assert screen.message_history[0]["role"] == "user"
            assert screen.message_history[0]["content"] == "Test message"

            # Check that agent was called (streaming should have started)
            # Note: streaming is async, so it might not complete immediately
            # But the user message should be in history
            assert screen.message_history[0]["content"] == "Test message"

            # If streaming completed, assistant message should be there
            if len(screen.message_history) >= 2:
                assert screen.message_history[1]["role"] == "assistant"


@pytest.mark.asyncio
async def test_chat_screen_allows_multiple_inputs_during_streaming():
    """Test that input is allowed during streaming (multiple questions)."""
    from tui.app import PriorApp

    agent = MockAgent()

    with tempfile.TemporaryDirectory() as tmpdir:
        app = PriorApp(agent, project_root=Path(tmpdir))

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

            # Wait a bit and check if streaming started (may complete quickly with mock)
            await asyncio.sleep(0.1)
            await pilot.pause()

            # Submit second message (should be allowed regardless of streaming state)
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

    agent = MockAgent()

    with tempfile.TemporaryDirectory() as tmpdir:
        app = PriorApp(agent, project_root=Path(tmpdir))

        async with app.run_test():
            screen = app.screen
            # Quit action should exit app
            screen.action_quit()
            # App should be exiting (exact behavior depends on Textual)
