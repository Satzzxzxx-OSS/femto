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

    def load_file(self, filepath):
        """Load a file into the buffer."""
        self.filename = filepath
        if filepath and os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Replace tabs with spaces for consistent rendering
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

    def insert_char(self, x, y, char):
        """Insert a character at (x, y)."""
        line = self.lines[y]
        self.lines[y] = line[:x] + char + line[x:]
        self.modified = True

    def insert_newline(self, x, y):
        """Split the line at (x, y) into two lines."""
        line = self.lines[y]
        self.lines[y] = line[:x]
        self.lines.insert(y + 1, line[x:])
        self.modified = True

    def delete_char(self, x, y):
        """Delete the character at (x, y)."""
        if x < len(self.lines[y]):
            line = self.lines[y]
            self.lines[y] = line[:x] + line[x+1:]
            self.modified = True
        elif x == len(self.lines[y]) and y < len(self.lines) - 1:
            # Merge with next line
            self.lines[y] += self.lines[y + 1]
            del self.lines[y + 1]
            self.modified = True

    def backspace(self, x, y):
        """Handle backspace at (x, y), returns new (x, y)."""
        if x > 0:
            self.delete_char(x - 1, y)
            return x - 1, y
        elif y > 0:
            # Merge current line with previous line
            prev_len = len(self.lines[y - 1])
            self.lines[y - 1] += self.lines[y]
            del self.lines[y]
            self.modified = True
            return prev_len, y - 1
        return x, y

    def get_line_length(self, y):
        """Returns the length of line y."""
        if 0 <= y < len(self.lines):
            return len(self.lines[y])
        return 0

    @property
    def max_y(self):
        """Maximum Y index."""
        return max(0, len(self.lines) - 1)
