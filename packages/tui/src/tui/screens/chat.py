"""Chat screen for coding agent."""

import asyncio
from pathlib import Path

from protocol.models import ChatMessage  # noqa: F401
from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, Markdown, Static

from ..chat_service import ChatService
from ..widgets import ClipboardInput, MousePassthroughScroll


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
        self.message_history: list[dict[str, str]] = []
        self._receive_task: asyncio.Task | None = None
        self._current_assistant_widget: Markdown | None = None
        self._current_assistant_content: str = ""
        # Track assistant messages by message_id for streaming
        self._assistant_streams: dict[str, dict[str, str | Markdown]] = {}

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

        # Send message via adapter
        await self.chat_service.send_message(user_input)

        # Add to history
        self.message_history.append({"role": "user", "content": user_input})

        # Display user message
        self._add_user_message(user_input)
        # Reset assistant widget for new conversation turn
        self._current_assistant_widget = None
        self._current_assistant_content = ""
        self._assistant_streams.clear()

    async def _receive_messages(self) -> None:
        """Receive messages from adapter and display them."""
        try:
            async for message in self.chat_service.receive_messages():
                # Type: message is ChatMessage
                if message.role == "assistant":
                    # Handle streaming chunks vs complete messages
                    if message.event_type == "chunk":
                        # Streaming chunk: accumulate content
                        message_id = message.message_id or "default"
                        if message_id not in self._assistant_streams:
                            self._assistant_streams[message_id] = {
                                "content": "",
                                "widget": None,
                            }
                        stream = self._assistant_streams[message_id]
                        stream["content"] += message.content
                        updated_widget = self._update_assistant_stream(
                            message_id, stream["content"], stream["widget"]
                        )
                        if stream["widget"] is None:
                            stream["widget"] = updated_widget
                    elif message.event_type == "message":
                        # Complete message: finalize and add to history
                        message_id = message.message_id or "default"
                        # If this message_id was being streamed, use accumulated
                        # content, otherwise use message content
                        if message_id in self._assistant_streams:
                            final_content = (
                                self._assistant_streams[message_id]["content"]
                            )
                            # Update widget one last time with final content
                            widget = self._assistant_streams[message_id]["widget"]
                            if widget:
                                widget.update(final_content)
                            # Clean up stream tracking
                            del self._assistant_streams[message_id]
                        else:
                            final_content = message.content
                            self._add_assistant_message(final_content)
                        # Add to history
                        self.message_history.append(
                            {"role": "assistant", "content": final_content}
                        )
                    else:
                        # Fallback for messages without event_type (backward
                        # compatibility)
                        self._add_assistant_message(message.content)
                        self.message_history.append(
                            {"role": "assistant", "content": message.content}
                        )
        except asyncio.CancelledError:
            pass

    def _add_user_message(self, content: str) -> None:
        """Add user message to display."""
        messages_container = self.query_one(
            "#messages-container", MousePassthroughScroll
        )
        user_markdown = Markdown(
            f"**You:** {content}", classes="user-message"
        )
        messages_container.mount(user_markdown)
        # Scroll to bottom to show new message
        messages_container.scroll_end(animate=False)

    def _add_assistant_message(self, content: str) -> None:
        """Add assistant message to display."""
        messages_container = self.query_one(
            "#messages-container", MousePassthroughScroll
        )
        # Accumulate content
        self._current_assistant_content += content
        if self._current_assistant_widget is None:
            assistant_markdown = Markdown(
                self._current_assistant_content, classes="assistant-message"
            )
            messages_container.mount(assistant_markdown)
            self._current_assistant_widget = assistant_markdown
        else:
            # Update existing widget with accumulated content
            self._current_assistant_widget.update(self._current_assistant_content)
        messages_container.scroll_end(animate=False)

    def _update_assistant_stream(
        self, message_id: str, content: str, widget: Markdown | None
    ) -> Markdown:
        """Update assistant message stream display.

        Returns:
            The widget that was created or updated
        """
        messages_container = self.query_one(
            "#messages-container", MousePassthroughScroll
        )
        if widget is None:
            # Create new widget for this stream
            assistant_markdown = Markdown(
                content, classes="assistant-message"
            )
            messages_container.mount(assistant_markdown)
            self._current_assistant_widget = assistant_markdown
            messages_container.scroll_end(animate=False)
            return assistant_markdown
        else:
            # Update existing widget
            widget.update(content)
            messages_container.scroll_end(animate=False)
            return widget

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
