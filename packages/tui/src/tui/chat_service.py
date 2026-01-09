"""Chat service layer for decoupling UI from business logic."""

from collections.abc import AsyncIterator
from pathlib import Path
from typing import TYPE_CHECKING

from protocol.models import ChatMessage

if TYPE_CHECKING:
    from adapter import AdapterClient


class ChatService:
    """Service layer for chat operations, decoupling UI from adapter."""

    def __init__(
        self,
        adapter: "AdapterClient | None" = None,
        project_root: Path | None = None,
    ):
        """
        Initialize chat service.

        Args:
            adapter: Adapter client for sending/receiving messages
            project_root: Project root directory (default: current directory)
        """
        self.adapter = adapter
        self.project_root = project_root or Path.cwd()
        # Track streaming chunks by message_id
        self._assistant_streams: dict[str, str] = {}
        # Message history for conversation tracking
        self.message_history: list[dict[str, str]] = []

    async def send_message(self, content: str) -> None:
        """
        Send a user message via adapter.

        Args:
            content: Message content to send
        """
        if self.adapter:
            message = ChatMessage(role="user", content=content)
            await self.adapter.send(message)
            # Add to history
            self.message_history.append({"role": "user", "content": content})

    async def receive_messages(
        self,
    ) -> AsyncIterator[ChatMessage]:
        """
        Receive and process messages from adapter.

        Handles streaming chunks by accumulating them and yielding
        complete messages only. This decouples streaming logic from UI.

        Yields:
            Complete chat messages (not chunks)
        """
        if not self.adapter:
            return

        async for message in self.adapter.receive():
            if message.role == "assistant":
                # Handle streaming chunks vs complete messages
                if message.event_type == "chunk":
                    # Streaming chunk: accumulate content
                    message_id = message.message_id or "default"
                    if message_id not in self._assistant_streams:
                        self._assistant_streams[message_id] = ""
                    self._assistant_streams[message_id] += message.content
                elif message.event_type == "message":
                    # Complete message: finalize and yield
                    message_id = message.message_id or "default"
                    # Use accumulated content if available, otherwise use
                    # message content
                    if message_id in self._assistant_streams:
                        final_content = self._assistant_streams[message_id]
                        # Clean up stream tracking
                        del self._assistant_streams[message_id]
                    else:
                        final_content = message.content
                    # Create complete message
                    complete_message = ChatMessage(
                        role="assistant",
                        content=final_content,
                        event_type="message",
                        message_id=message_id,
                    )
                    # Add to history
                    self.message_history.append(
                        {"role": "assistant", "content": final_content}
                    )
                    yield complete_message
                else:
                    # Fallback for messages without event_type (backward
                    # compatibility)
                    self.message_history.append(
                        {"role": "assistant", "content": message.content}
                    )
                    yield message
            else:
                # Non-assistant messages pass through as-is
                yield message

    def get_message_history(self) -> list[dict[str, str]]:
        """
        Get message history.

        Returns:
            List of message dicts with 'role' and 'content' keys
        """
        return self.message_history.copy()
