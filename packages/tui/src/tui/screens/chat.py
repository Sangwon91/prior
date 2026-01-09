"""Chat screen for coding agent."""

import asyncio
from pathlib import Path

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Static

from ..chat_service import ChatService
from ..widgets import ClipboardInput, MessageDisplay, MousePassthroughScroll


class ChatScreen(Screen):
    """Chat interface screen."""

    CSS = """
    ChatScreen {
        layout: vertical;
    }

    #chat-container {
        height: 1fr;
        layout: vertical;
    }

    #current-question {
        height: auto;
        border-bottom: wide $primary;
        padding: 1;
        background: $primary 10%;
    }

    #messages-container {
        height: 1fr;
        border: wide $primary;
        padding: 1;
    }

    #input-container {
        height: auto;
        border-top: wide $primary;
        padding: 1;
    }

    #input-box {
        width: 1fr;
    }

    .user-message {
        margin: 1;
        padding: 1;
        background: $primary 20%;
    }

    .assistant-message {
        margin: 1;
        padding: 1;
        background: $surface;
    }

    #status-bar {
        height: 1;
        padding: 0 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
    ]

    def __init__(
        self, chat_service: ChatService, project_root: Path | None = None
    ):
        """
        Initialize chat screen.

        Args:
            chat_service: ChatService instance for handling chat operations
            project_root: Project root directory (default: current directory)
        """
        super().__init__()
        self.chat_service = chat_service
        self.project_root = project_root or chat_service.project_root
        self._receive_task: asyncio.Task | None = None
        self._message_display: MessageDisplay | None = None

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        with Vertical(id="chat-container"):
            yield Static(
                f"Project: {self.project_root.name}", id="status-bar"
            )
            yield Static("", id="current-question")
            with MousePassthroughScroll(id="messages-container"):
                pass  # Messages will be added dynamically
            with Horizontal(id="input-container"):
                yield ClipboardInput(
                    placeholder=(
                        "Ask about the project or request coding help..."
                    ),
                    id="input-box",
                )
        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Initialize message display
        messages_container = self.query_one(
            "#messages-container", MousePassthroughScroll
        )
        self._message_display = MessageDisplay(messages_container)

        # Focus input box
        self.query_one("#input-box", ClipboardInput).focus()

        # Start receiving messages from adapter
        if self.chat_service.adapter:
            self._receive_task = asyncio.create_task(
                self._receive_messages()
            )

    def on_unmount(self) -> None:
        """Called when screen is unmounted."""
        if self._receive_task:
            self._receive_task.cancel()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        user_input = event.value.strip()
        if not user_input:
            return

        # Update current question display
        current_question_widget = self.query_one(
            "#current-question", Static
        )
        current_question_widget.update(f"Current Question: {user_input}")

        # Clear input (but don't disable - allow multiple questions)
        input_box = self.query_one("#input-box", ClipboardInput)
        input_box.value = ""

        # Send message via adapter (history managed by ChatService)
        await self.chat_service.send_message(user_input)

        # Display user message
        if self._message_display:
            self._message_display.add_user_message(user_input)

    async def _receive_messages(self) -> None:
        """Receive messages from adapter and display them."""
        try:
            async for message in self.chat_service.receive_messages():
                # ChatService handles streaming and only yields complete
                # messages
                if message.role == "assistant" and self._message_display:
                    self._message_display.add_assistant_message(
                        message.content
                    )
        except asyncio.CancelledError:
            pass

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
