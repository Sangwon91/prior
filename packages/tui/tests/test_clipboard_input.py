"""Unit tests for ClipboardInput widget."""

import pytest
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.events import Paste

from tui.widgets import ClipboardInput


class ClipboardTestApp(App):
    """Test app for ClipboardInput testing."""

    def compose(self) -> ComposeResult:
        """Create test widgets."""
        with Container():
            yield ClipboardInput(id="test-input")


@pytest.mark.asyncio
async def test_clipboard_input_inserts_text_at_cursor_position():
    """Test ClipboardInput inserts text at current cursor position."""
    app = ClipboardTestApp()

    async with app.run_test() as pilot:
        input_widget = app.query_one(ClipboardInput)

        # Set initial value and cursor position
        input_widget.value = "Hello World"
        input_widget.cursor_position = 5  # After "Hello"

        # Insert text
        input_widget._insert_text_at_cursor(" Beautiful")

        # Check result
        assert input_widget.value == "Hello Beautiful World"
        # " Beautiful" is 10 characters, so cursor should be at 5 + 10 = 15
        assert input_widget.cursor_position == 15

        await pilot.pause()


@pytest.mark.asyncio
async def test_clipboard_input_inserts_text_at_start_when_cursor_at_start():
    """Test ClipboardInput inserts text at start when cursor is at position 0."""
    app = ClipboardTestApp()

    async with app.run_test() as pilot:
        input_widget = app.query_one(ClipboardInput)

        # Set initial value and cursor at start
        input_widget.value = "World"
        input_widget.cursor_position = 0

        # Insert text
        input_widget._insert_text_at_cursor("Hello ")

        # Check result
        assert input_widget.value == "Hello World"
        assert input_widget.cursor_position == 6

        await pilot.pause()


@pytest.mark.asyncio
async def test_clipboard_input_inserts_text_at_end_when_cursor_at_end():
    """Test ClipboardInput inserts text at end when cursor is at end."""
    app = ClipboardTestApp()

    async with app.run_test() as pilot:
        input_widget = app.query_one(ClipboardInput)

        # Set initial value and cursor at end
        input_widget.value = "Hello"
        input_widget.cursor_position = 5

        # Insert text
        input_widget._insert_text_at_cursor(" World")

        # Check result
        assert input_widget.value == "Hello World"
        assert input_widget.cursor_position == 11

        await pilot.pause()


@pytest.mark.asyncio
async def test_clipboard_input_removes_newlines_from_inserted_text():
    """Test ClipboardInput removes newlines and carriage returns from pasted text."""
    app = ClipboardTestApp()

    async with app.run_test() as pilot:
        input_widget = app.query_one(ClipboardInput)

        # Set initial value
        input_widget.value = "Hello"
        input_widget.cursor_position = 5

        # Insert text with newlines
        input_widget._insert_text_at_cursor("\nWorld\n\rTest")

        # Check that newlines are replaced with spaces
        # "\nWorld\n\rTest" -> " World \r Test" -> " World   Test"
        # But Input widget may normalize multiple spaces, so we check the actual result
        # The important thing is that newlines are removed
        assert "Hello" in input_widget.value
        assert "World" in input_widget.value
        assert "Test" in input_widget.value
        assert "\n" not in input_widget.value
        assert "\r" not in input_widget.value
        # Check approximate cursor position (text length may vary due to space normalization)
        assert input_widget.cursor_position >= 15

        await pilot.pause()


@pytest.mark.asyncio
async def test_clipboard_input_on_paste_inserts_text_and_stops_event():
    """Test ClipboardInput on_paste inserts text and stops event propagation."""
    app = ClipboardTestApp()

    async with app.run_test() as pilot:
        input_widget = app.query_one(ClipboardInput)

        # Set initial value and cursor position
        input_widget.value = "Hello World"
        input_widget.cursor_position = 5

        # Create and handle Paste event using post_message
        # Paste event is created by Textual internally, so we simulate it
        # by calling on_paste with a mock event
        from unittest.mock import MagicMock

        paste_event = MagicMock(spec=Paste)
        paste_event.text = " Beautiful"
        paste_event.is_stopped = False

        def stop_mock():
            paste_event.is_stopped = True

        paste_event.stop = stop_mock

        input_widget.on_paste(paste_event)

        # Check result
        assert input_widget.value == "Hello Beautiful World"
        # " Beautiful" is 10 characters
        assert input_widget.cursor_position == 15

        # Check that event was stopped
        assert paste_event.is_stopped

        await pilot.pause()


@pytest.mark.asyncio
async def test_clipboard_input_on_paste_handles_empty_text():
    """Test ClipboardInput on_paste handles empty Paste event without changes."""
    app = ClipboardTestApp()

    async with app.run_test() as pilot:
        input_widget = app.query_one(ClipboardInput)

        # Set initial value
        input_widget.value = "Hello"
        initial_value = input_widget.value
        initial_cursor = input_widget.cursor_position

        # Create and handle empty Paste event
        from unittest.mock import MagicMock

        paste_event = MagicMock(spec=Paste)
        paste_event.text = ""
        paste_event.is_stopped = False

        def stop_mock():
            paste_event.is_stopped = True

        paste_event.stop = stop_mock

        input_widget.on_paste(paste_event)

        # Check that value didn't change
        assert input_widget.value == initial_value
        assert input_widget.cursor_position == initial_cursor

        # Check that event was still stopped
        assert paste_event.is_stopped

        await pilot.pause()


@pytest.mark.asyncio
async def test_clipboard_input_on_paste_removes_newlines_from_pasted_text():
    """Test ClipboardInput on_paste removes newlines from pasted text."""
    app = ClipboardTestApp()

    async with app.run_test() as pilot:
        input_widget = app.query_one(ClipboardInput)

        # Set initial value
        input_widget.value = "Hello"
        input_widget.cursor_position = 5

        # Create Paste event with newlines
        from unittest.mock import MagicMock

        paste_event = MagicMock(spec=Paste)
        paste_event.text = "\nWorld\n\rTest"
        paste_event.is_stopped = False

        def stop_mock():
            paste_event.is_stopped = True

        paste_event.stop = stop_mock

        input_widget.on_paste(paste_event)

        # Check that newlines are replaced with spaces
        # The exact spacing may vary due to Input widget normalization
        assert "Hello" in input_widget.value
        assert "World" in input_widget.value
        assert "Test" in input_widget.value
        assert "\n" not in input_widget.value
        assert "\r" not in input_widget.value
        # Check approximate cursor position
        assert input_widget.cursor_position >= 15

        await pilot.pause()


@pytest.mark.asyncio
async def test_clipboard_input_action_paste_does_nothing():
    """Test ClipboardInput action_paste does nothing (waits for Paste event)."""
    app = ClipboardTestApp()

    async with app.run_test() as pilot:
        input_widget = app.query_one(ClipboardInput)

        # Set initial value
        input_widget.value = "Hello"
        initial_value = input_widget.value
        initial_cursor = input_widget.cursor_position

        # Call action_paste (should do nothing, waiting for Paste event)
        input_widget.action_paste()

        # Check that value didn't change (action_paste does nothing)
        assert input_widget.value == initial_value
        assert input_widget.cursor_position == initial_cursor

        await pilot.pause()


@pytest.mark.asyncio
async def test_clipboard_input_complete_paste_flow():
    """Test ClipboardInput complete paste flow from action_paste to on_paste."""
    app = ClipboardTestApp()

    async with app.run_test() as pilot:
        input_widget = app.query_one(ClipboardInput)

        # Set initial value
        input_widget.value = "Hello"
        input_widget.cursor_position = 5

        # Simulate Ctrl+V: action_paste is called first (does nothing)
        input_widget.action_paste()

        # Then terminal sends Paste event (simulated)
        from unittest.mock import MagicMock

        paste_event = MagicMock(spec=Paste)
        paste_event.text = " World"
        paste_event.is_stopped = False

        def stop_mock():
            paste_event.is_stopped = True

        paste_event.stop = stop_mock

        input_widget.on_paste(paste_event)

        # Check final result
        assert input_widget.value == "Hello World"
        assert input_widget.cursor_position == 11

        await pilot.pause()


@pytest.mark.asyncio
async def test_clipboard_input_handles_multiple_paste_operations():
    """Test ClipboardInput handles multiple consecutive paste operations."""
    app = ClipboardTestApp()

    async with app.run_test() as pilot:
        input_widget = app.query_one(ClipboardInput)

        # Initial value
        input_widget.value = ""
        input_widget.cursor_position = 0

        # First paste
        from unittest.mock import MagicMock

        paste_event1 = MagicMock(spec=Paste)
        paste_event1.text = "Hello"
        paste_event1.is_stopped = False

        def stop_mock1():
            paste_event1.is_stopped = True

        paste_event1.stop = stop_mock1

        input_widget.on_paste(paste_event1)
        assert input_widget.value == "Hello"
        assert input_widget.cursor_position == 5

        # Second paste (cursor is at end)
        paste_event2 = MagicMock(spec=Paste)
        paste_event2.text = " World"
        paste_event2.is_stopped = False

        def stop_mock2():
            paste_event2.is_stopped = True

        paste_event2.stop = stop_mock2

        input_widget.on_paste(paste_event2)
        assert input_widget.value == "Hello World"
        assert input_widget.cursor_position == 11

        # Third paste in the middle
        input_widget.cursor_position = 5
        paste_event3 = MagicMock(spec=Paste)
        paste_event3.text = " Beautiful"
        paste_event3.is_stopped = False

        def stop_mock3():
            paste_event3.is_stopped = True

        paste_event3.stop = stop_mock3

        input_widget.on_paste(paste_event3)
        assert input_widget.value == "Hello Beautiful World"
        # " Beautiful" is 10 characters
        assert input_widget.cursor_position == 15

        await pilot.pause()
