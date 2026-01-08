"""Chat service layer for decoupling UI from business logic."""

from collections.abc import AsyncIterator
from pathlib import Path
from typing import Any

from .filetree import get_project_tree
from .protocols import AgentProtocol


class ChatService:
    """Service layer for chat operations, decoupling UI from Agent and filetree."""

    def __init__(self, agent: AgentProtocol, project_root: Path | None = None):
        """
        Initialize chat service.

        Args:
            agent: Agent instance for LLM interactions
            project_root: Project root directory (default: current directory)
        """
        self.agent = agent
        self.project_root = project_root or Path.cwd()
        self._project_tree: str | None = None

    @property
    def project_tree(self) -> str:
        """Get project tree, caching it for performance."""
        if self._project_tree is None:
            self._project_tree = get_project_tree(self.project_root)
        return self._project_tree

    async def stream_response(
        self, messages: list[dict[str, Any]]
    ) -> AsyncIterator[str]:
        """
        Stream response from agent with project context.

        Args:
            messages: List of message dicts with 'role' and 'content' keys

        Yields:
            Chunks of response text as they arrive
        """
        async for chunk in self.agent.chat_stream(
            messages, project_context=self.project_tree
        ):
            yield chunk

