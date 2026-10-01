"""
Interactive prompt system for Femto.
Handles text input displayed in the bottom status bar area.
"""

import curses


class Prompt:
    """Manages a single-line text input prompt."""

    def __init__(self):
        self.label = ""
        self.text = ""
        self.cursor_pos = 0
        self.active = False

    def start(self, label, default=""):
        """Activate the prompt with a label and optional default text."""
        self.label = label
        self.text = default
        self.cursor_pos = len(default)
        self.active = True

    def deactivate(self):
        """Deactivate the prompt and clear state."""
        self.active = False
        self.label = ""
        self.text = ""
        self.cursor_pos = 0

    def handle_key(self, key):
        """
        Process a keypress while the prompt is active.

        Returns:
            'confirmed'  – user pressed Enter
            'cancelled'  – user pressed Ctrl+G or Escape
            'active'     – prompt remains open
        """
        # Confirm
        if key in (10, 13, curses.KEY_ENTER):
            return 'confirmed'

        # Cancel
        if key in (7, 27):  # Ctrl+G or Escape
            return 'cancelled'

        # Backspace
        if key in (curses.KEY_BACKSPACE, 127, 8):
            if self.cursor_pos > 0:
                self.text = (
                    self.text[: self.cursor_pos - 1]
                    + self.text[self.cursor_pos :]
                )
                self.cursor_pos -= 1

        # Delete
        elif key == curses.KEY_DC:
            if self.cursor_pos < len(self.text):
                self.text = (
                    self.text[: self.cursor_pos]
                    + self.text[self.cursor_pos + 1 :]
                )

        # Cursor movement within prompt
        elif key == curses.KEY_LEFT:
            self.cursor_pos = max(0, self.cursor_pos - 1)
        elif key == curses.KEY_RIGHT:
            self.cursor_pos = min(len(self.text), self.cursor_pos + 1)
        elif key == curses.KEY_HOME:
            self.cursor_pos = 0
        elif key == curses.KEY_END:
            self.cursor_pos = len(self.text)

        # Printable ASCII
        elif 32 <= key <= 126:
            char = chr(key)
            self.text = (
                self.text[: self.cursor_pos]
                + char
                + self.text[self.cursor_pos :]
            )
            self.cursor_pos += 1

        return 'active'

    def get_display(self, width):
        """Return the prompt string formatted to fill *width* columns."""
        display = f"{self.label}{self.text}"
        return display.ljust(width)[:width]

    def get_cursor_x(self):
        """Return the screen column of the prompt cursor."""
        return len(self.label) + self.cursor_pos
