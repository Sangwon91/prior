"""Bridge between Agent and TUI."""

import asyncio
from collections.abc import AsyncIterator

from protocol.interfaces import ControlCommandHandler
from protocol.models import ControlCommand, WorkflowEvent


class Bridge:
    """Bridge that connects Agent and TUI through WebSocket."""

    def __init__(self):
        """Initialize bridge."""
        self._event_queue: asyncio.Queue[WorkflowEvent] = asyncio.Queue()
        self._command_handlers: dict[str, ControlCommandHandler] = {}
        self._event_subscribers: list[asyncio.Queue[WorkflowEvent]] = []

    def register_command_handler(
        self, workflow_id: str, handler: ControlCommandHandler
    ) -> None:
        """
        Register a command handler for a workflow.

        Args:
            workflow_id: Workflow ID to register handler for
            handler: Command handler implementation
        """
        self._command_handlers[workflow_id] = handler

    def unregister_command_handler(self, workflow_id: str) -> None:
        """
        Unregister a command handler for a workflow.

        Args:
            workflow_id: Workflow ID to unregister
        """
        self._command_handlers.pop(workflow_id, None)

    async def publish_event(self, event: WorkflowEvent) -> None:
        """
        Publish a workflow event to all subscribers.

        Args:
            event: Workflow event to publish
        """
        # Add to main queue
        await self._event_queue.put(event)

        # Broadcast to all subscribers
        for subscriber_queue in self._event_subscribers:
            try:
                await subscriber_queue.put(event)
            except Exception:
                # Remove dead subscribers
                if subscriber_queue in self._event_subscribers:
                    self._event_subscribers.remove(subscriber_queue)

    async def handle_command(self, command: ControlCommand) -> None:
        """
        Handle a control command.

        Args:
            command: Control command to handle
        """
        handler = self._command_handlers.get(command.workflow_id)
        if handler:
            await handler.handle_command(command)

    def create_event_subscriber(
        self,
    ) -> AsyncIterator[WorkflowEvent]:
        """
        Create a new event subscriber.

        Yields:
            Workflow events as they arrive
        """
        queue: asyncio.Queue[WorkflowEvent] = asyncio.Queue()
        self._event_subscribers.append(queue)

        async def event_iterator() -> AsyncIterator[WorkflowEvent]:
            try:
                while True:
                    event = await queue.get()
                    yield event
            finally:
                if queue in self._event_subscribers:
                    self._event_subscribers.remove(queue)

        return event_iterator()

    async def get_events(self) -> AsyncIterator[WorkflowEvent]:
        """
        Get workflow events as they arrive (legacy method).

        Yields:
            Workflow events
        """
        while True:
            event = await self._event_queue.get()
            yield event
