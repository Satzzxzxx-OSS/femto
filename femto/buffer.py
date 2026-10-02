"""
Text buffer management for Femto.
"""

import os

from femto.search import SearchOptions, find_next

class Buffer:
    def __init__(self, config):
        self.lines = [""]
        self.filename = None
        self.modified = False
        self.config = config

    def load_file(self, filepath):
        self.filename = filepath
        if filepath and os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Replace tabs with spaces based on config
                    spaces = " " * self.config.tab_size
                    self.lines = content.replace('\t', spaces).splitlines()
                    if not self.lines:
                        self.lines = [""]
            except Exception as e:
                self.lines = [f"Error reading file: {e}"]
        else:
            self.lines = [""]
        self.modified = False

    def save(self):
        if not self.filename:
            return False
        try:
            with open(self.filename, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.lines))
            self.modified = False
            return True
        except Exception:
            return False

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

    def insert_tab(self, y, x):
        spaces = " " * self.config.tab_size
        line = self.lines[y]
        self.lines[y] = line[:x] + spaces + line[x:]
        self.modified = True
        return x + len(spaces)

    def remove_tab(self, y, x):
        line = self.lines[y]
        spaces_to_remove = 0
        for i in range(min(self.config.tab_size, len(line))):
            if line[i] == ' ':
                spaces_to_remove += 1
            else:
                break
        if spaces_to_remove > 0:
            self.lines[y] = line[spaces_to_remove:]
            self.modified = True
            return max(0, x - spaces_to_remove)
        return x

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

    def find_text(self, term, start_x, start_y):
        """Case-sensitive plain search (back-compat wrapper).

        Returns (x, y) or None. Full-featured search (case/regex/wrap
        control, match length) lives in femto.search.
        """
        hit = find_next(self, term, SearchOptions(), start_x, start_y)
        return (hit[0], hit[1]) if hit else None

    def get_line_length(self, y):
        if 0 <= y < len(self.lines):
            return len(self.lines[y])
        return 0

    @property
    def max_y(self):
        return max(0, len(self.lines) - 1)
