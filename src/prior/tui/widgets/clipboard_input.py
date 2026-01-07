"""Input widget with system clipboard integration."""

from textual.events import Paste
from textual.widgets import Input


class ClipboardInput(Input):
    """Input widget that uses system clipboard instead of internal clipboard.
    
    According to Textual FAQ, Textual supports text selection and copy via ctrl+c.
    This widget ensures paste events from terminal are properly handled.
    """

    def on_paste(self, event: Paste) -> None:
        """Handle paste event from terminal/system clipboard."""
        # Textual's Paste event contains the clipboard text
        clipboard_text = event.text
        if clipboard_text:
            # Remove newlines and control characters that might interfere
            clipboard_text = clipboard_text.replace("\n", " ").replace("\r", "")
            
            current_value = self.value
            cursor_position = self.cursor_position
            
            # Insert clipboard text at cursor position
            new_value = (
                current_value[:cursor_position]
                + clipboard_text
                + current_value[cursor_position:]
            )
            self.value = new_value
            # Move cursor to end of pasted text
            self.cursor_position = cursor_position + len(clipboard_text)
        
        # Stop the event from propagating
        event.stop()

