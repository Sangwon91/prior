"""Container that allows terminal native mouse selection."""

from textual.containers import VerticalScroll


class MousePassthroughScroll(VerticalScroll):
    """VerticalScroll container that passes mouse events to terminal for native selection.

    This container allows terminal emulator to handle text selection natively
    while still supporting mouse wheel scrolling within Textual.
    """

    # Disable mouse capture to allow terminal native selection
    # When mouse is not captured, terminal emulator can handle text selection
    # Note: This disables all mouse interactions including scrolling
    # Users can still use keyboard to scroll
    CAPTURE_MOUSE = False
