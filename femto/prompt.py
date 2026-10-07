"""
Prompt line model for Femto (search, replace, save-as, goto).
"""


class Prompt:
    def __init__(self):
        self.active = False
        self.label = ""
        self.text = ""
        self.cursor_pos = 0
        self.help = ""

    def start(self, label, help_text=""):
        self.active = True
        self.label = label
        self.help = help_text
        self.text = ""
        self.cursor_pos = 0

    def clear(self):
        self.active = False
        self.label = ""
        self.text = ""
        self.cursor_pos = 0

    def insert(self, ch):
        self.text = (self.text[:self.cursor_pos] + ch +
                     self.text[self.cursor_pos:])
        self.cursor_pos += len(ch)

    def backspace(self):
        if self.cursor_pos > 0:
            self.text = (self.text[:self.cursor_pos - 1] +
                         self.text[self.cursor_pos:])
            self.cursor_pos -= 1

    def delete(self):
        if self.cursor_pos < len(self.text):
            self.text = (self.text[:self.cursor_pos] +
                         self.text[self.cursor_pos + 1:])

    def move(self, dx):
        self.cursor_pos = max(0, min(len(self.text), self.cursor_pos + dx))

    def home(self):
        self.cursor_pos = 0

    def end(self):
        self.cursor_pos = len(self.text)

    def get_display(self, width):
        return f" {self.label}: {self.text}"

    def get_cursor_x(self):
        return len(self.label) + 3 + self.cursor_pos

    def handle_key(self, key):
        """Legacy helper: 'enter' | 'cancel' | 'change' | None."""
        if key in (10, 13, 343, 344):
            return "enter"
        if key in (27, 7):
            return "cancel"
        if key in (8, 127):
            self.backspace()
            return "change"
        if isinstance(key, str) and len(key) == 1 and ord(key) > 31:
            self.insert(key)
            return "change"
        if isinstance(key, int) and 32 <= key <= 126:
            self.insert(chr(key))
            return "change"
        return None
