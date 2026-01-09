"""Event publisher implementation for agent."""

import uuid
from typing import Any

from protocol.interfaces import EventPublisher
from protocol.models import (
    NodeProgress,
    WorkflowCompleted,
    WorkflowError,
    WorkflowEvent,
    WorkflowStarted,
)


class AgentEventPublisher:
    """Event publisher implementation for agent."""

    def __init__(self, publisher: EventPublisher | None = None):
        """
        Initialize event publisher.

        Args:
            publisher: Event publisher implementation
        """
        self._publisher = publisher
        self._active_workflows: dict[str, Any] = {}

    def set_publisher(self, publisher: EventPublisher) -> None:
        """
        Set the event publisher implementation.

        Args:
            publisher: Event publisher implementation
        """
        self._publisher = publisher

    async def publish_workflow_event(
        self, event: WorkflowEvent
    ) -> None:
        """
        Publish a workflow event.

        Args:
            event: Workflow event to publish
        """
        if self._publisher:
            await self._publisher.publish_workflow_event(event)

    async def publish_workflow_started(
        self, workflow_id: str
    ) -> None:
        """
        Publish workflow started event.

        Args:
            workflow_id: Workflow ID
        """
        event = WorkflowEvent(
            workflow_id=workflow_id,
            event_type="started",
            data=WorkflowStarted(workflow_id=workflow_id),
        )
        await self.publish_workflow_event(event)

    async def publish_node_progress(
        self,
        workflow_id: str,
        node_id: str,
        state: str,
        progress: float | None = None,
        message: str | None = None,
    ) -> None:
        """
        Publish node progress event.

        Args:
            workflow_id: Workflow ID
            node_id: Node ID
            state: Node state
            progress: Progress (0.0 ~ 1.0)
            message: Optional message
        """
        event = WorkflowEvent(
            workflow_id=workflow_id,
            event_type="progress",
            data=NodeProgress(
                workflow_id=workflow_id,
                node_id=node_id,
                state=state,
                progress=progress,
                message=message,
            ),
        )
        await self.publish_workflow_event(event)

    async def publish_workflow_completed(
        self, workflow_id: str, result: dict | None = None
    ) -> None:
        """
        Publish workflow completed event.

        Args:
            workflow_id: Workflow ID
            result: Workflow result
        """
        event = WorkflowEvent(
            workflow_id=workflow_id,
            event_type="completed",
            data=WorkflowCompleted(
                workflow_id=workflow_id, result=result
            ),
        )
        await self.publish_workflow_event(event)

    async def publish_workflow_error(
        self,
        workflow_id: str,
        error: str,
        details: dict | None = None,
    ) -> None:
        """
        Publish workflow error event.

        Args:
            workflow_id: Workflow ID
            error: Error message
            details: Optional error details
        """
        event = WorkflowEvent(
            workflow_id=workflow_id,
            event_type="error",
            data=WorkflowError(
                workflow_id=workflow_id,
                error=error,
                details=details,
            ),
        )
        await self.publish_workflow_event(event)

    def generate_workflow_id(self) -> str:
        """
        Generate a new workflow ID.

        Returns:
            Generated workflow ID
        """
        return str(uuid.uuid4())

