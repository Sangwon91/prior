"""Main Textual application."""

from pathlib import Path

from textual.app import App

from .chat_service import ChatService
from .protocols import AgentProtocol
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

    def __init__(self, agent: AgentProtocol, project_root: Path | None = None):
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
        chat_service = ChatService(self.agent, self.project_root)
        self.push_screen(ChatScreen(chat_service, self.project_root))
