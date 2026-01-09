"""Simple LLM agent wrapper using LiteLLM."""

import uuid
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING, Any

from litellm import acompletion

from protocol.models import ChatMessage

if TYPE_CHECKING:
    from adapter import AdapterClient


class Agent:
    """Thin wrapper around LiteLLM for streaming chat."""

    def __init__(
        self,
        model: str = "claude-sonnet-4-5",
        adapter: "AdapterClient | None" = None,
    ):
        """
        Initialize agent.

        Args:
            model: Model name to use (default: claude-sonnet-4-5)
            adapter: Optional adapter client for sending messages
        """
        self.model = model
        self.adapter = adapter

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
                    "content": (
                        f"You are a coding assistant. "
                        f"Here is the project structure:\n\n"
                        f"{project_context}\n\n"
                        f"You can answer questions about the project "
                        f"structure and help with coding tasks."
                    ),
                }
            )

        all_messages = system_messages + messages

        # Generate unique message ID for this response
        message_id = str(uuid.uuid4())

        # Call LiteLLM with streaming
        response = await acompletion(
            model=self.model,
            messages=all_messages,
            stream=True,
        )

        # Stream response chunks
        response_content = ""
        async for chunk in response:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    response_content += delta.content
                    # Send chunk via adapter if available
                    if self.adapter:
                        chat_message = ChatMessage(
                            role="assistant",
                            content=delta.content,
                            event_type="chunk",
                            message_id=message_id,
                        )
                        await self.adapter.send(chat_message)
                    yield delta.content

        # Send complete message after streaming is done
        if self.adapter and response_content:
            complete_message = ChatMessage(
                role="assistant",
                content=response_content,
                event_type="message",
                message_id=message_id,
            )
            await self.adapter.send(complete_message)
