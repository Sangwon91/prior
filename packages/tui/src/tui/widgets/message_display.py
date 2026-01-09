"""Message display widget for chat interface."""

from textual.widgets import Markdown

from .mouse_passthrough import MousePassthroughScroll


class MessageDisplay:
    """Manages message rendering in chat container."""

    def __init__(self, container: MousePassthroughScroll):
        """
        Initialize message display.

        Args:
            container: Container widget to display messages in
        """
        self.container = container

    def add_user_message(self, content: str) -> None:
        """
        Add user message to display.

        Args:
            content: Message content to display
        """
        user_markdown = Markdown(
            f"**You:** {content}", classes="user-message"
        )
        self.container.mount(user_markdown)
        # Scroll to bottom to show new message
        self.container.scroll_end(animate=False)

    def add_assistant_message(self, content: str) -> None:
        """
        Add assistant message to display.

        Args:
            content: Message content to display
        """
        assistant_markdown = Markdown(
            content, classes="assistant-message"
        )
        self.container.mount(assistant_markdown)
        self.container.scroll_end(animate=False)

