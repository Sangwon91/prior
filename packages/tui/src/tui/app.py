"""Main Textual application."""

from pathlib import Path

from textual.app import App

from .chat_service import ChatService
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

    def __init__(
        self,
        chat_service: ChatService,
        project_root: Path | None = None,
    ):
        """
        Initialize the app.

        Args:
            chat_service: Chat service instance
            project_root: Project root directory (default: current directory)
        """
        super().__init__()
        self.chat_service = chat_service
        self.project_root = project_root or Path.cwd()

    def on_mount(self) -> None:
        """Called when app is mounted."""
        self.push_screen(
            ChatScreen(self.chat_service, self.project_root)
        )
