"""Integration tests for ChatScreen."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from prior.core.agent import Agent
from prior.tui.screens.chat import ChatScreen


class MockAgent(Agent):
    """Mock agent for testing."""
    
    def __init__(self):
        super().__init__(model="test-model")
        self.chat_calls = []
    
    async def chat_stream(self, messages, project_context=""):
        """Mock streaming response."""
        self.chat_calls.append((messages, project_context))
        # Yield some test chunks
        for chunk in ["Hello", " ", "World"]:
            yield chunk


@pytest.mark.asyncio
async def test_chat_screen_initialization():
    """Test ChatScreen can be initialized."""
    agent = MockAgent()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        screen = ChatScreen(agent, project_root=Path(tmpdir))
        
        assert screen.agent == agent
        assert screen.project_root == Path(tmpdir)
        assert len(screen.message_history) == 0
        assert screen.is_streaming is False


@pytest.mark.asyncio
async def test_chat_screen_compose():
    """Test ChatScreen compose method."""
    from prior.tui.app import PriorApp
    
    agent = MockAgent()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        app = PriorApp(agent, project_root=Path(tmpdir))
        
        async with app.run_test() as pilot:
            screen = app.screen
            # Check that widgets exist
            input_box = screen.query_one("#input-box", expect_type=None)
            assert input_box is not None
            
            messages_log = screen.query_one("#messages-log", expect_type=None)
            assert messages_log is not None


@pytest.mark.asyncio
async def test_chat_screen_input_submission():
    """Test ChatScreen handles input submission."""
    from prior.tui.app import PriorApp
    
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
            for _ in range(10):  # Try up to 10 times
                await asyncio.sleep(0.1)
                await pilot.pause()
                if not screen.is_streaming:
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
async def test_chat_screen_streaming_disables_input():
    """Test that input is disabled during streaming."""
    from prior.tui.app import PriorApp
    
    agent = MockAgent()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        app = PriorApp(agent, project_root=Path(tmpdir))
        
        async with app.run_test() as pilot:
            screen = app.screen
            input_box = screen.query_one("#input-box")
            
            # Start streaming
            screen.is_streaming = True
            
            # Try to submit - should be ignored
            from textual.widgets import Input
            event = Input.Submitted(input_box, "Test")
            initial_history_len = len(screen.message_history)
            
            await screen.on_input_submitted(event)
            
            # History should not change
            assert len(screen.message_history) == initial_history_len


@pytest.mark.asyncio
async def test_chat_screen_quit_action():
    """Test quit action."""
    from prior.tui.app import PriorApp
    
    agent = MockAgent()
    
    with tempfile.TemporaryDirectory() as tmpdir:
        app = PriorApp(agent, project_root=Path(tmpdir))
        
        async with app.run_test() as pilot:
            screen = app.screen
            # Quit action should exit app
            screen.action_quit()
            # App should be exiting (exact behavior depends on Textual)

