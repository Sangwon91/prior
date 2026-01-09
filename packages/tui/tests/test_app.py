"""Integration tests for PriorApp."""

import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from tui.app import PriorApp
from tui.chat_service import ChatService


class MockAdapter:
    """Mock adapter for testing."""

    def __init__(self):
        self.sent_messages = []
        self.received_messages = []

    async def send(self, message):
        """Mock send."""
        self.sent_messages.append(message)

    async def receive(self):
        """Mock receive."""
        for msg in self.received_messages:
            yield msg


@pytest.mark.asyncio
async def test_app_initialization():
    """Test PriorApp can be initialized."""
    mock_adapter = MockAdapter()
    chat_service = ChatService(adapter=mock_adapter)
    app = PriorApp(chat_service=chat_service)

    assert app.chat_service == chat_service
    assert app.TITLE == "Prior - Coding Agent"
    assert app.SUB_TITLE == "AI-powered coding assistant"


@pytest.mark.asyncio
async def test_app_with_project_root():
    """Test PriorApp with project root."""
    mock_adapter = MockAdapter()
    chat_service = ChatService(adapter=mock_adapter)

    with tempfile.TemporaryDirectory() as tmpdir:
        app = PriorApp(chat_service=chat_service, project_root=Path(tmpdir))

        assert app.project_root == Path(tmpdir)


@pytest.mark.asyncio
async def test_app_mounts_chat_screen():
    """Test PriorApp mounts ChatScreen on mount."""
    mock_adapter = MockAdapter()
    chat_service = ChatService(adapter=mock_adapter)
    app = PriorApp(chat_service=chat_service)

    async with app.run_test():
        # Check that ChatScreen is mounted
        from tui.screens.chat import ChatScreen

        assert isinstance(app.screen, ChatScreen)
        # ChatScreen has chat_service
        assert app.screen.chat_service == chat_service


@pytest.mark.asyncio
async def test_app_title():
    """Test app displays correct title."""
    mock_adapter = MockAdapter()
    chat_service = ChatService(adapter=mock_adapter)
    app = PriorApp(chat_service=chat_service)

    async with app.run_test():
        # Check header exists
        header = app.screen.query_one("Header")
        assert header is not None
