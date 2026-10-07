"""
Cursor state and viewport scrolling for Femto.
"""


class Cursor:
    def __init__(self):
        self.x = 0
        self.y = 0
        self.scroll_x = 0
        self.scroll_y = 0

    def set_pos(self, x, y, get_line_length, max_y):
        self.y = max(0, min(y, max_y))
        self.x = max(0, min(x, get_line_length(self.y)))

    def clamp(self, get_line_length, max_y):
        self.set_pos(self.x, self.y, get_line_length, max_y)

    def move_left(self, buffer):
        if self.x > 0:
            self.x -= 1
        elif self.y > 0:
            self.y -= 1
            self.x = buffer.get_line_length(self.y)

    def move_right(self, buffer):
        if self.x < buffer.get_line_length(self.y):
            self.x += 1
        elif self.y < buffer.max_y:
            self.y += 1
            self.x = 0

    def move_up(self, buffer, soft_wrap=True, text_cols=80):
        if self.y > 0:
            self.y -= 1
            self.x = min(self.x, buffer.get_line_length(self.y))

    def move_down(self, buffer, soft_wrap=True, text_cols=80):
        if self.y < buffer.max_y:
            self.y += 1
            self.x = min(self.x, buffer.get_line_length(self.y))

    def move_word_left(self, buffer):
        line = buffer.lines[self.y]
        if self.x == 0:
            if self.y > 0:
                self.y -= 1
                self.x = buffer.get_line_length(self.y)
            return
        i = self.x - 1
        while i > 0 and line[i - 1].isspace():
            i -= 1
        while i > 0 and not line[i - 1].isspace():
            i -= 1
        self.x = i

    def move_word_right(self, buffer):
        line = buffer.lines[self.y]
        n = len(line)
        if self.x >= n:
            if self.y < buffer.max_y:
                self.y += 1
                self.x = 0
            return
        i = self.x
        while i < n and not line[i].isspace():
            i += 1
        while i < n and line[i].isspace():
            i += 1
        self.x = i

    def page_up(self, buffer, rows):
        self.y = max(0, self.y - max(1, rows - 1))
        self.x = min(self.x, buffer.get_line_length(self.y))

    def page_down(self, buffer, rows):
        self.y = min(buffer.max_y, self.y + max(1, rows - 1))
        self.x = min(self.x, buffer.get_line_length(self.y))

    def update_scroll(self, y, x, screen_rows, screen_cols, margin=3,
                      soft_wrap=True):
        """NOTE: original argument order is (y, x, rows, cols, margin)."""
        if soft_wrap:
            self.scroll_x = 0
        else:
            if x < self.scroll_x + margin:
                self.scroll_x = max(0, x - margin)
            elif x >= self.scroll_x + screen_cols - margin:
                self.scroll_x = x - screen_cols + margin + 1
        if y < self.scroll_y + margin:
            self.scroll_y = max(0, y - margin)
        elif y >= self.scroll_y + screen_rows - margin:
            self.scroll_y = y - screen_rows + margin + 1
