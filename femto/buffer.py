"""
Text buffer management for Femto.
"""

import os


class Buffer:
    """Handles the text content as a list of lines."""

    def __init__(self):
        self.lines = [""]
        self.filename = None
        self.modified = False

    # ── File I/O ──────────────────────────────────────────────

    def load_file(self, filepath):
        """Load a file into the buffer."""
        self.filename = filepath
        if filepath and os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    self.lines = content.replace('\t', '    ').splitlines()
                    if not self.lines:
                        self.lines = [""]
            except Exception as e:
                self.lines = [f"Error reading file: {e}"]
        else:
            self.lines = [""]
        self.modified = False

    def save(self):
        """Save the buffer to the current filename."""
        if not self.filename:
            return False
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.lines))
            self.modified = False
            return True
        except Exception:
            return False

    # ── Editing ───────────────────────────────────────────────

    def insert_char(self, x, y, char):
        line = self.lines[y]
        self.lines[y] = line[:x] + char + line[x:]
        self.modified = True

    def insert_newline(self, x, y):
        line = self.lines[y]
        self.lines[y] = line[:x]
        self.lines.insert(y + 1, line[x:])
        self.modified = True

    def delete_char(self, x, y):
        if x < len(self.lines[y]):
            line = self.lines[y]
            self.lines[y] = line[:x] + line[x + 1:]
            self.modified = True
        elif x == len(self.lines[y]) and y < len(self.lines) - 1:
            self.lines[y] += self.lines[y + 1]
            del self.lines[y + 1]
            self.modified = True

    def backspace(self, x, y):
        if x > 0:
            self.delete_char(x - 1, y)
            return x - 1, y
        elif y > 0:
            prev_len = len(self.lines[y - 1])
            self.lines[y - 1] += self.lines[y]
            del self.lines[y]
            self.modified = True
            return prev_len, y - 1
        return x, y

    # ── Tab / Indentation ─────────────────────────────────────

    def insert_tab(self, y, x):
        spaces = "    "
        line = self.lines[y]
        self.lines[y] = line[:x] + spaces + line[x:]
        self.modified = True
        return x + len(spaces)

    def remove_tab(self, y, x):
        line = self.lines[y]
        spaces_to_remove = 0
        for i in range(min(4, len(line))):
            if line[i] == ' ':
                spaces_to_remove += 1
            else:
                break
        if spaces_to_remove > 0:
            self.lines[y] = line[spaces_to_remove:]
            self.modified = True
            return max(0, x - spaces_to_remove)
        return x

    # ── Word Navigation ───────────────────────────────────────

    def get_next_word_pos(self, y, x):
        line = self.lines[y]
        while x < len(line) and line[x].isalnum():
            x += 1
        while x < len(line) and not line[x].isalnum():
            x += 1
        return x

    def get_prev_word_pos(self, y, x):
        line = self.lines[y]
        if x == 0:
            return 0
        x -= 1
        while x >= 0 and not line[x].isalnum():
            x -= 1
        while x >= 0 and line[x].isalnum():
            x -= 1
        return x + 1

    # ── Search ────────────────────────────────────────────────

    def find_text(self, term, start_x, start_y):
        """
        Case-sensitive forward search for *term*.

        Starts at (start_x, start_y) and wraps around the entire buffer.
        Returns (x, y) of the match, or None.
        """
        if not term:
            return None

        num_lines = len(self.lines)
        if num_lines == 0:
            return None

        for i in range(num_lines):
            y = (start_y + i) % num_lines
            line = self.lines[y]
            search_from = start_x if i == 0 else 0
            pos = line.find(term, search_from)
            if pos != -1:
                return pos, y

        return None

    # ── Helpers ───────────────────────────────────────────────

    def get_line_length(self, y):
        if 0 <= y < len(self.lines):
            return len(self.lines[y])
        return 0

    @property
    def max_y(self):
        return max(0, len(self.lines) - 1)
