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

    async def send_message(self, content: str) -> None:
        """
        Send a user message via adapter.

        Args:
            content: Message content to send
        """
        if self.adapter:
            message = ChatMessage(role="user", content=content)
            await self.adapter.send(message)

    async def receive_messages(
        self,
    ) -> AsyncIterator[ChatMessage]:
        """
        Receive messages from adapter.

        Yields:
            Chat messages as they arrive
        """
        if self.adapter:
            async for message in self.adapter.receive():
                yield message
