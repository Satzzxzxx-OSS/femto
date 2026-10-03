"""
Text buffer management for Femto.

The buffer owns the logical text (a list of lines) plus file I/O.
Since v0.0.2rc1 every mutation bumps a `revision` counter (via
`touch()`), which the renderer uses to skip redraws of unchanged
frames.  Saves are atomic: temp file -> fsync -> os.replace.
"""

import os

from femto.search import SearchOptions, find_next


class Buffer:
    """Handles the text content as a list of lines."""

    def __init__(self, config):
        self.lines = [""]
        self.filename = None
        self.modified = False
        self.revision = 0          # render-cache invalidation counter
        self.config = config

    # ── File I/O ──────────────────────────────────────────────

    def load_file(self, filepath):
        """Load a file into the buffer."""
        self.filename = filepath
        if filepath and os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    spaces = " " * self.config.tab_size
                    self.lines = content.replace('\t', spaces).splitlines()
                    if not self.lines:
                        self.lines = [""]
            except Exception as e:
                self.lines = [f"Error reading file: {e}"]
        else:
            self.lines = [""]
        self.modified = False
        self.revision = 0

    def save(self):
        """Atomic save: write temp file, fsync, os.replace into place.

        With `make_backup = true` in .femtorc the previous version is
        kept as `<name>~`.
        """
        if not self.filename:
            return False
        tmp = self.filename + ".femto-tmp"
        try:
            with open(tmp, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.lines))
                f.flush()
                os.fsync(f.fileno())
            if getattr(self.config, 'make_backup', False) \
                    and os.path.exists(self.filename):
                os.replace(self.filename, self.filename + "~")
            os.replace(tmp, self.filename)
            self.modified = False
            return True
        except Exception:
            try:
                os.remove(tmp)
            except OSError:
                pass
            return False

    def touch(self):
        """Mark modified and bump the revision counter."""
        self.modified = True
        self.revision += 1

    # ── Editing ───────────────────────────────────────────────

    def insert_char(self, x, y, char):
        """Insert a character at (x, y)."""
        line = self.lines[y]
        self.lines[y] = line[:x] + char + line[x:]
        self.touch()

    def insert_newline(self, x, y):
        """Split the line at (x, y) into two lines."""
        line = self.lines[y]
        self.lines[y] = line[:x]
        self.lines.insert(y + 1, line[x:])
        self.touch()

    def delete_char(self, x, y):
        """Delete the character at (x, y), merging lines at EOL."""
        if x < len(self.lines[y]):
            line = self.lines[y]
            self.lines[y] = line[:x] + line[x + 1:]
            self.touch()
        elif x == len(self.lines[y]) and y < len(self.lines) - 1:
            self.lines[y] += self.lines[y + 1]
            del self.lines[y + 1]
            self.touch()

    def backspace(self, x, y):
        """Handle backspace at (x, y); returns new (x, y)."""
        if x > 0:
            self.delete_char(x - 1, y)     # touches internally
            return x - 1, y
        elif y > 0:
            prev_len = len(self.lines[y - 1])
            self.lines[y - 1] += self.lines[y]
            del self.lines[y]
            self.touch()
            return prev_len, y - 1
        return x, y

    # ── Tab / Indentation ─────────────────────────────────────

    def insert_tab(self, y, x):
        """Insert `tab_size` spaces at cursor; returns new x."""
        spaces = " " * self.config.tab_size
        line = self.lines[y]
        self.lines[y] = line[:x] + spaces + line[x:]
        self.touch()
        return x + len(spaces)

    def remove_tab(self, y, x):
        """Remove up to `tab_size` leading spaces; returns new x."""
        line = self.lines[y]
        spaces_to_remove = 0
        for i in range(min(self.config.tab_size, len(line))):
            if line[i] == ' ':
                spaces_to_remove += 1
            else:
                break
        if spaces_to_remove > 0:
            self.lines[y] = line[spaces_to_remove:]
            self.touch()
            return max(0, x - spaces_to_remove)
        return x

    # ── Word Navigation ───────────────────────────────────────

    def get_next_word_pos(self, y, x):
        """X position of the start of the next word on line y."""
        line = self.lines[y]
        while x < len(line) and line[x].isalnum():
            x += 1
        while x < len(line) and not line[x].isalnum():
            x += 1
        return x

    def get_prev_word_pos(self, y, x):
        """X position of the start of the previous word on line y."""
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
        """Case-sensitive plain search (back-compat wrapper).

        Returns (x, y) or None.  Full-featured search (case/regex/wrap
        control, match length) lives in femto.search.
        """
        hit = find_next(self, term, SearchOptions(), start_x, start_y)
        return (hit[0], hit[1]) if hit else None

    # ── Helpers ───────────────────────────────────────────────

    def get_line_length(self, y):
        """Length of line y (0 for out-of-range rows)."""
        if 0 <= y < len(self.lines):
            return len(self.lines[y])
        return 0

    @property
    def max_y(self):
        """Maximum valid line index."""
        return max(0, len(self.lines) - 1)
