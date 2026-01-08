"""Chat screen for coding agent."""

import asyncio
from pathlib import Path

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

    def __init__(self, chat_service: ChatService, project_root: Path | None = None):
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
        self._active_streaming_tasks: set[asyncio.Task] = set()  # Track active streaming tasks

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        with Vertical(id="chat-container"):
            yield Static(f"Project: {self.project_root.name}", id="status-bar")
            yield Static("", id="current-question")
            with MousePassthroughScroll(id="messages-container"):
                pass  # Messages will be added dynamically
            with Horizontal(id="input-container"):
                yield ClipboardInput(
                    placeholder="Ask about the project or request coding help...",
                    id="input-box",
                )
        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Focus input box
        self.query_one("#input-box", ClipboardInput).focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        user_input = event.value.strip()
        if not user_input:
            return

        # Update current question display
        current_question_widget = self.query_one("#current-question", Static)
        current_question_widget.update(f"Current Question: {user_input}")

        # Clear input (but don't disable - allow multiple questions)
        input_box = self.query_one("#input-box", ClipboardInput)
        input_box.value = ""

        # Add to history
        self.message_history.append({"role": "user", "content": user_input})

        # Display user message
        self._add_user_message(user_input)

        # Start streaming response as background task
        # This allows multiple questions to be asked simultaneously
        task = asyncio.create_task(self._stream_response())
        self._active_streaming_tasks.add(task)
        task.add_done_callback(self._active_streaming_tasks.discard)

    def _add_user_message(self, content: str) -> None:
        """Add user message to display."""
        messages_container = self.query_one("#messages-container", MousePassthroughScroll)
        user_markdown = Markdown(f"**You:** {content}", classes="user-message")
        messages_container.mount(user_markdown)
        # Scroll to bottom to show new message
        messages_container.scroll_end(animate=False)

    async def _stream_response(self) -> None:
        """Stream response from chat service."""
        current_response = ""
        try:
            # Get streaming response
            response_chunks: list[str] = []
            messages_container = self.query_one("#messages-container", MousePassthroughScroll)
            
            # Create streaming widget
            streaming_widget = Markdown("", classes="assistant-message")
            messages_container.mount(streaming_widget)
            messages_container.scroll_end(animate=False)

            async for chunk in self.chat_service.stream_response(self.message_history):
                response_chunks.append(chunk)
                current_response += chunk
                
                # Update streaming markdown widget with current response
                streaming_widget.update(current_response)
                # Scroll to bottom to follow streaming
                messages_container.scroll_end(animate=False)
                # Refresh to show updates
                await self._refresh_messages()

            # Add complete response to history
            full_response = "".join(response_chunks)
            self.message_history.append({"role": "assistant", "content": full_response})
            
            # Replace streaming widget with completed message
            completed_markdown = Markdown(full_response, classes="assistant-message")
            streaming_widget.remove()
            messages_container.mount(completed_markdown)
            
            # Scroll to bottom
            messages_container.scroll_end(animate=False)

        except Exception as e:
            messages_container = self.query_one("#messages-container", MousePassthroughScroll)
            error_markdown = Markdown(f"**Error:** {str(e)}", classes="assistant-message")
            messages_container.mount(error_markdown)
            messages_container.scroll_end(animate=False)

    async def _refresh_messages(self) -> None:
        """Refresh messages display."""
        # Yield control to allow UI updates
        await asyncio.sleep(0)


    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

