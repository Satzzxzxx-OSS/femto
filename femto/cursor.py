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

    def update_scroll(self, visual_y, visual_x, screen_rows, screen_cols,
                      margin, soft_wrap=True):
        """Keep the cursor inside the viewport with smooth margins."""
        # ── Vertical ──
        if visual_y < self.scroll_y + margin:
            self.scroll_y = max(0, visual_y - margin)
        elif visual_y >= self.scroll_y + screen_rows - margin:
            self.scroll_y = max(0, visual_y - screen_rows + margin + 1)

        # Safety clamp for very small terminals
        if self.scroll_y > visual_y:
            self.scroll_y = visual_y
        if self.scroll_y + screen_rows <= visual_y:
            self.scroll_y = visual_y - screen_rows + 1

        # ── Horizontal ──
        if soft_wrap:
            self.scroll_x = 0
        else:
            h = 2
            if visual_x < self.scroll_x + h:
                self.scroll_x = max(0, visual_x - h)
            elif visual_x >= self.scroll_x + screen_cols - h:
                self.scroll_x = max(0, visual_x - screen_cols + h + 1)

            # Safety clamp for very narrow terminals
            if self.scroll_x > visual_x:
                self.scroll_x = visual_x
            if self.scroll_x + screen_cols <= visual_x:
                self.scroll_x = visual_x - screen_cols + 1
