"""Tests for MessageDisplay widget."""

import pytest
from textual.app import App
from textual.containers import VerticalScroll

from tui.widgets.message_display import MessageDisplay
from tui.widgets.mouse_passthrough import MousePassthroughScroll


class TestMessageApp(App):
    """Test app for MessageDisplay tests."""

    def compose(self):
        """Create test widgets."""
        from tui.widgets.mouse_passthrough import MousePassthroughScroll

        yield MousePassthroughScroll(id="container")


@pytest.mark.asyncio
async def test_message_display_adds_user_message():
    """Test MessageDisplay adds user message to container."""
    app = TestMessageApp()

    async with app.run_test():
        container = app.query_one("#container", MousePassthroughScroll)
        display = MessageDisplay(container)

        display.add_user_message("Hello")

        # Check that markdown widget was added with correct class
        markdown_widgets = container.query("Markdown.user-message")
        assert len(markdown_widgets) == 1


@pytest.mark.asyncio
async def test_message_display_adds_assistant_message():
    """Test MessageDisplay adds assistant message to container."""
    app = TestMessageApp()

    async with app.run_test():
        container = app.query_one("#container", MousePassthroughScroll)
        display = MessageDisplay(container)

        display.add_assistant_message("Hello World")

        # Check that markdown widget was added with correct class
        markdown_widgets = container.query("Markdown.assistant-message")
        assert len(markdown_widgets) == 1


@pytest.mark.asyncio
async def test_message_display_adds_multiple_messages():
    """Test MessageDisplay can add multiple messages."""
    app = TestMessageApp()

    async with app.run_test():
        container = app.query_one("#container", MousePassthroughScroll)
        display = MessageDisplay(container)

        display.add_user_message("Question 1")
        display.add_assistant_message("Answer 1")
        display.add_user_message("Question 2")

        # Check that all messages were added
        markdown_widgets = container.query("Markdown")
        assert len(markdown_widgets) == 3
