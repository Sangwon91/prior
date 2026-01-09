"""Bridge between Agent and TUI."""

import asyncio
from collections.abc import AsyncIterator

from protocol.models import ChatMessage


class Bridge:
    """Bridge that connects Agent and TUI through message queues."""

    def __init__(self):
        """Initialize bridge."""
        self._message_queue: asyncio.Queue[ChatMessage] = asyncio.Queue()
        self._subscribers: list[asyncio.Queue[ChatMessage]] = []

    async def send(self, message: ChatMessage) -> None:
        """
        Send a chat message to all subscribers.

        Args:
            message: Chat message to send
        """
        # Add to main queue
        await self._message_queue.put(message)

        # Broadcast to all subscribers
        for subscriber_queue in self._subscribers:
            try:
                await subscriber_queue.put(message)
            except Exception:
                # Remove dead subscribers
                if subscriber_queue in self._subscribers:
                    self._subscribers.remove(subscriber_queue)

    def create_subscriber(
        self,
    ) -> AsyncIterator[ChatMessage]:
        """
        Create a new message subscriber.

        Yields:
            Chat messages as they arrive
        """
        queue: asyncio.Queue[ChatMessage] = asyncio.Queue()
        self._subscribers.append(queue)

        async def message_iterator() -> AsyncIterator[ChatMessage]:
            try:
                while True:
                    message = await queue.get()
                    yield message
            finally:
                if queue in self._subscribers:
                    self._subscribers.remove(queue)

        return message_iterator()

    async def get_messages(self) -> AsyncIterator[ChatMessage]:
        """
        Get chat messages as they arrive (legacy method).

        Yields:
            Chat messages
        """
        while True:
            message = await self._message_queue.get()
            yield message
