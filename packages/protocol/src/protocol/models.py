"""Pydantic models for protocol messages."""

from datetime import datetime
from typing import Literal, Union

from pydantic import BaseModel, Field


class WorkflowStarted(BaseModel):
    """Workflow started event data."""

    workflow_id: str
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())


class NodeProgress(BaseModel):
    """Node progress event data."""

    workflow_id: str
    node_id: str
    state: Literal["pending", "running", "completed", "failed", "skipped"]
    progress: float | None = None  # 0.0 ~ 1.0
    message: str | None = None


class WorkflowCompleted(BaseModel):
    """Workflow completed event data."""

    workflow_id: str
    result: dict | None = None


class WorkflowError(BaseModel):
    """Workflow error event data."""

    workflow_id: str
    error: str
    details: dict | None = None


class WorkflowEvent(BaseModel):
    """Workflow event message."""

    workflow_id: str
    event_type: Literal["started", "progress", "completed", "error"]
    data: Union[
        WorkflowStarted,
        NodeProgress,
        WorkflowCompleted,
        WorkflowError,
    ]


class ControlCommand(BaseModel):
    """Control command message."""

    workflow_id: str
    command: Literal["cancel", "pause", "resume"]
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())
