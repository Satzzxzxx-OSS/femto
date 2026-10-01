"""
Cursor management for Femto.
"""

class Cursor:
    """Tracks the cursor's x/y coordinates and viewport offsets."""

    def __init__(self):
        self.x = 0
        self.y = 0
        self.scroll_x = 0
        self.scroll_y = 0

    def move(self, dx, dy, max_x, max_y):
        """Move cursor with bounds checking against the buffer."""
        self.y = max(0, min(self.y + dy, max_y))

        # If moving vertically, clamp X to the new line's length
        if dy != 0:
            self.x = min(self.x, max_x(self.y))

        self.x = max(0, min(self.x, max_x(self.y)))

    def set_pos(self, x, y, max_x, max_y):
        """Set absolute cursor position."""
        self.y = max(0, min(y, max_y))
        self.x = max(0, min(x, max_x(self.y)))

    def update_scroll(self, screen_rows, screen_cols):
        """Update scroll offsets to keep cursor visible on screen."""
        # Vertical scrolling
        if self.y < self.scroll_y:
            self.scroll_y = self.y
        elif self.y >= self.scroll_y + screen_rows:
            self.scroll_y = self.y - screen_rows + 1

        # Horizontal scrolling
        if self.x < self.scroll_x:
            self.scroll_x = self.x
        elif self.x >= self.scroll_x + screen_cols:
            self.scroll_x = self.x - screen_cols + 1
