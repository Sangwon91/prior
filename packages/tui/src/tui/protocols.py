"""Protocols for dependency injection."""

from collections.abc import AsyncIterator
from typing import Any, Protocol


class AgentProtocol(Protocol):
    """Protocol for agent implementations."""

    async def chat_stream(
        self,
        messages: list[dict[str, Any]],
        project_context: str = "",
    ) -> AsyncIterator[str]:
        """
        Stream chat responses from LLM.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            project_context: Optional project file tree context to include

        Yields:
            Chunks of response text as they arrive
        """
        ...
