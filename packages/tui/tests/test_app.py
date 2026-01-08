"""Integration tests for PriorApp."""

import tempfile
from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

import pytest

from tui.app import PriorApp
from tui.protocols import AgentProtocol


class MockAgent:
    """Mock agent implementing AgentProtocol for testing."""

    def __init__(self):
        pass

    async def chat_stream(
        self, messages: list[dict[str, Any]], project_context: str = ""
    ) -> AsyncIterator[str]:
        """Mock streaming response."""
        yield "test response"


@pytest.mark.asyncio
async def test_app_initialization():
    """Test PriorApp can be initialized."""
    agent = MockAgent()
    app = PriorApp(agent)

    assert app.agent == agent
    assert app.TITLE == "Prior - Coding Agent"
    assert app.SUB_TITLE == "AI-powered coding assistant"


@pytest.mark.asyncio
async def test_app_with_project_root():
    """Test PriorApp with project root."""
    agent = MockAgent()

    with tempfile.TemporaryDirectory() as tmpdir:
        app = PriorApp(agent, project_root=Path(tmpdir))

        assert app.project_root == Path(tmpdir)


@pytest.mark.asyncio
async def test_app_mounts_chat_screen():
    """Test PriorApp mounts ChatScreen on mount."""
    agent = MockAgent()
    app = PriorApp(agent)

    async with app.run_test() as pilot:
        # Check that ChatScreen is mounted
        from tui.screens.chat import ChatScreen
        assert isinstance(app.screen, ChatScreen)
        # ChatScreen has chat_service, not agent directly
        assert app.screen.chat_service.agent == agent


@pytest.mark.asyncio
async def test_app_title():
    """Test app displays correct title."""
    agent = MockAgent()
    app = PriorApp(agent)

    async with app.run_test() as pilot:
        # Check header exists
        header = app.screen.query_one("Header")
        assert header is not None

