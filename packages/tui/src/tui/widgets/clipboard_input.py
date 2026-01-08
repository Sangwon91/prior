"""Input widget with system clipboard integration."""

from textual.events import Paste
from textual.widgets import Input


class ClipboardInput(Input):
    """Input widget that uses system clipboard instead of internal clipboard.
    
    According to Textual FAQ, Textual supports text selection and copy via ctrl+c.
    This widget ensures paste events from terminal are properly handled.
    """

    def on_paste(self, event: Paste) -> None:
        """Handle paste event from terminal/system clipboard.
        
        This is called when terminal sends paste data (e.g., from Ctrl+V or
        middle mouse button). The event.text contains the clipboard content.
        """
        clipboard_text = event.text
        if clipboard_text:
            self._insert_text_at_cursor(clipboard_text)
        
        # Stop the event from propagating to prevent default behavior
        # which might use internal clipboard
        event.stop()

    def action_paste(self) -> None:
        """Handle paste action (Ctrl+V).
        
        When Ctrl+V is pressed, the terminal should send a Paste event.
        We don't call super() to avoid using internal clipboard.
        The terminal's Paste event will be handled by on_paste().
        """
        # Don't call super() - we rely on terminal's Paste event
        # The terminal will send paste data which triggers on_paste()
        # If no Paste event comes, nothing happens (user can use Shift+Insert
        # or terminal's paste shortcut instead)
        pass

    def _insert_text_at_cursor(self, text: str) -> None:
        """Insert text at current cursor position."""
        # Remove newlines and control characters that might interfere
        text = text.replace("\n", " ").replace("\r", "")
        
        current_value = self.value
        cursor_position = self.cursor_position
        
        # Insert text at cursor position
        new_value = (
            current_value[:cursor_position]
            + text
            + current_value[cursor_position:]
        )
        self.value = new_value
        # Move cursor to end of inserted text
        self.cursor_position = cursor_position + len(text)

