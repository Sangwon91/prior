"""Simple LLM agent wrapper using LiteLLM."""

from collections.abc import AsyncIterator
from typing import Any

from litellm import acompletion


class Agent:
    """Thin wrapper around LiteLLM for streaming chat."""

    def __init__(self, model: str = "claude-sonnet-4-5"):
        """
        Initialize agent.

        Args:
            model: Model name to use (default: claude-sonnet-4-5)
        """
        self.model = model

    async def chat_stream(
        self, messages: list[dict[str, Any]], project_context: str = ""
    ) -> AsyncIterator[str]:
        """
        Stream chat responses from LLM.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            project_context: Optional project file tree context to include

        Yields:
            Chunks of response text as they arrive
        """
        # Prepare messages with project context as system message if provided
        system_messages = []
        if project_context:
            system_messages.append(
                {
                    "role": "system",
                    "content": f"You are a coding assistant. Here is the project structure:\n\n{project_context}\n\nYou can answer questions about the project structure and help with coding tasks.",
                }
            )

        all_messages = system_messages + messages

        # Call LiteLLM with streaming
        response = await acompletion(
            model=self.model,
            messages=all_messages,
            stream=True,
        )

        # Stream response chunks
        async for chunk in response:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    yield delta.content

