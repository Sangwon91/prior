"""Chat screen for coding agent."""

import asyncio
from collections.abc import AsyncIterator
from pathlib import Path

from rich.markdown import Markdown
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Footer, Header, Input, RichLog, Static

from ...core.agent import Agent
from ...core.filetree import get_project_tree


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

    #messages-area {
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

    #streaming-message {
        padding: 1;
        min-height: 1;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self, agent: Agent, project_root: Path | None = None):
        """
        Initialize chat screen.

        Args:
            agent: Agent instance
            project_root: Project root directory (default: current directory)
        """
        super().__init__()
        self.agent = agent
        self.project_root = project_root or Path.cwd()
        self.project_tree = get_project_tree(self.project_root)
        self.message_history: list[dict[str, str]] = []
        self.is_streaming = False
        self._current_response: str = ""  # Track current streaming response

    def compose(self) -> ComposeResult:
        """Create child widgets."""
        yield Header()
        with Vertical(id="chat-container"):
            yield Static(f"Project: {self.project_root.name}", id="status-bar")
            with VerticalScroll(id="messages-area"):
                yield RichLog(id="messages-log", markup=True, wrap=True)
                yield Static("", id="streaming-message", classes="assistant-message")
            with Horizontal(id="input-container"):
                yield Input(
                    placeholder="Ask about the project or request coding help...",
                    id="input-box",
                )
        yield Footer()

    def on_mount(self) -> None:
        """Called when screen is mounted."""
        # Focus input box
        self.query_one("#input-box", Input).focus()

    async def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle input submission."""
        if self.is_streaming:
            return

        user_input = event.value.strip()
        if not user_input:
            return

        # Clear input
        input_box = self.query_one("#input-box", Input)
        input_box.value = ""
        input_box.disabled = True

        # Display user message
        self._add_user_message(user_input)

        # Add to history
        self.message_history.append({"role": "user", "content": user_input})

        # Start streaming response as background task
        # This allows the UI to remain responsive during streaming
        self.is_streaming = True
        asyncio.create_task(self._stream_response())

    def _add_user_message(self, content: str) -> None:
        """Add user message to display."""
        log = self.query_one("#messages-log", RichLog)
        log.write(f"[bold blue]You:[/bold blue] {content}")

    async def _stream_response(self) -> None:
        """Stream response from agent."""
        try:
            # Get streaming response
            response_chunks: list[str] = []
            log = self.query_one("#messages-log", RichLog)
            streaming_widget = self.query_one("#streaming-message", Static)
            streaming_widget.update("[bold green]Assistant:[/bold green] ")
            self._current_response = ""

            async for chunk in self.agent.chat_stream(
                self.message_history, project_context=self.project_tree
            ):
                response_chunks.append(chunk)
                self._current_response += chunk
                
                # Update streaming widget with current response
                streaming_widget.update(f"[bold green]Assistant:[/bold green] {self._current_response}")
                # Refresh to show updates
                await self._refresh_messages()

            # Add complete response to history and log
            full_response = "".join(response_chunks)
            self.message_history.append({"role": "assistant", "content": full_response})
            
            # Move streaming message to log and clear streaming widget
            log.write(f"[bold green]Assistant:[/bold green] {full_response}")
            streaming_widget.update("")

        except Exception as e:
            log = self.query_one("#messages-log", RichLog)
            log.write(f"[red]Error: {str(e)}[/red]")
            streaming_widget = self.query_one("#streaming-message", Static)
            streaming_widget.update("")
        finally:
            self.is_streaming = False
            self._current_response = ""
            input_box = self.query_one("#input-box", Input)
            input_box.disabled = False
            input_box.focus()

    async def _refresh_messages(self) -> None:
        """Refresh messages display."""
        # Yield control to allow UI updates
        await asyncio.sleep(0)

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()

