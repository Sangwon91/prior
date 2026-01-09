"""Event subscriber implementation for TUI."""

from collections.abc import AsyncIterator

from protocol.interfaces import EventSubscriber
from protocol.models import WorkflowEvent


class TuiEventSubscriber:
    """Event subscriber implementation for TUI."""

    def __init__(self, subscriber: EventSubscriber | None = None):
        """
        Initialize event subscriber.

        Args:
            subscriber: Event subscriber implementation
        """
        self._subscriber = subscriber

    def set_subscriber(self, subscriber: EventSubscriber) -> None:
        """
        Set the event subscriber implementation.

        Args:
            subscriber: Event subscriber implementation
        """
        self._subscriber = subscriber

    async def subscribe_workflow_events(
        self,
    ) -> AsyncIterator[WorkflowEvent]:
        """
        Subscribe to workflow events.

        Yields:
            Workflow events as they arrive
        """
        if self._subscriber:
            async for event in self._subscriber.subscribe_workflow_events():
                yield event

