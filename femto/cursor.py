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

    def move(self, dx, dy, max_x_func, max_y):
        self.y = max(0, min(self.y + dy, max_y))
        if dy != 0:
            self.x = min(self.x, max_x_func(self.y))
        self.x = max(0, min(self.x, max_x_func(self.y)))

    def page_move(self, dy, max_x_func, max_y):
        self.y = max(0, min(self.y + dy, max_y))
        self.x = min(self.x, max_x_func(self.y))

    def home(self):
        self.x = 0

    def end(self, line_length):
        self.x = line_length

    def set_pos(self, x, y, max_x_func, max_y):
        self.y = max(0, min(y, max_y))
        self.x = max(0, min(x, max_x_func(self.y)))

    def update_scroll(self, visual_y, screen_rows, margin):
        """Smooth scrolling based on visual row position."""
        if visual_y < self.scroll_y + margin:
            self.scroll_y = max(0, visual_y - margin)
        elif visual_y >= self.scroll_y + screen_rows - margin:
            self.scroll_y = max(0, visual_y - screen_rows + margin + 1)
