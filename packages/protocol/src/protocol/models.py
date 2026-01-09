"""Pydantic models for chat messages."""

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """Chat message model."""

    role: Literal["user", "assistant", "system"]
    content: str
    timestamp: float | None = Field(
        default_factory=lambda: datetime.now().timestamp()
    )
    event_type: Literal["chunk", "message"] = Field(
        default="message",
        description=(
            "Type of event: 'chunk' for streaming chunks, "
            "'message' for complete messages"
        ),
    )
    message_id: str | None = Field(
        default=None,
        description=(
            "Optional message ID to group chunks from the same response"
        ),
    )
