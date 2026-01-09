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
