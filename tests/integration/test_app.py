"""Integration tests for PriorApp."""

import tempfile
from pathlib import Path

import pytest

from prior.core.agent import Agent
from prior.tui.app import PriorApp


class MockAgent(Agent):
    """Mock agent for testing."""
    
    def __init__(self):
        super().__init__(model="test-model")


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
        from prior.tui.screens.chat import ChatScreen
        assert isinstance(app.screen, ChatScreen)
        assert app.screen.agent == agent


@pytest.mark.asyncio
async def test_app_title():
    """Test app displays correct title."""
    agent = MockAgent()
    app = PriorApp(agent)
    
    async with app.run_test() as pilot:
        # Check header exists
        header = app.screen.query_one("Header")
        assert header is not None

