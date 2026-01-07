"""Main Textual application."""

from pathlib import Path

from textual.app import App

from ..core.agent import Agent
from .screens.chat import ChatScreen


class PriorApp(App):
    """Main Prior TUI application."""

    CSS = """
    Screen {
        background: $surface;
    }
    
    PriorApp {
        background: $surface;
    }
    """

    TITLE = "Prior - Coding Agent"
    SUB_TITLE = "AI-powered coding assistant"

    def __init__(self, agent: Agent, project_root: Path | None = None):
        """
        Initialize the app.

        Args:
            agent: Agent instance
            project_root: Project root directory (default: current directory)
        """
        super().__init__()
        self.agent = agent
        self.project_root = project_root or Path.cwd()

    def on_mount(self) -> None:
        """Called when app is mounted."""
        self.push_screen(ChatScreen(self.agent, self.project_root))

