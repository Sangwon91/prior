"""Protocol interfaces for event publishing and subscription."""

from collections.abc import AsyncIterator
from typing import Protocol

from .models import ControlCommand, WorkflowEvent


class EventPublisher(Protocol):
    """Event publishing interface."""

    async def publish_workflow_event(self, event: WorkflowEvent) -> None:
        """
        Publish a workflow event.

        Args:
            event: Workflow event to publish
        """
        ...


class EventSubscriber(Protocol):
    """Event subscription interface."""

    async def subscribe_workflow_events(
        self,
    ) -> AsyncIterator[WorkflowEvent]:
        """
        Subscribe to workflow events.

        Yields:
            Workflow events as they arrive
        """
        ...


class ControlCommandHandler(Protocol):
    """Control command handling interface."""

    async def handle_command(self, command: ControlCommand) -> None:
        """
        Handle a control command.

        Args:
            command: Control command to handle
        """
        ...
