"""
Text buffer management for Femto.

I/O Fidelity (v0.0.3a01):
  * Detects dominant line ending (CRLF/CR/LF) on load.
  * Normalizes to \n internally so cursor math and wrapping stay clean.
  * Re-applies the correct ending on save.
  * Ensures POSIX-compliant trailing newlines.
"""

import os

from femto.search import SearchOptions, find_next


class Buffer:
    """Handles the text content as a list of lines."""

    def __init__(self, config):
        self.lines = [""]
        self.filename = None
        self.modified = False
        self.revision = 0
        self.config = config
        
        # I/O state
        self.line_ending = '\n'
        self.had_final_newline = False

    # ── File I/O ──────────────────────────────────────────────

    def load_file(self, filepath):
        """Load a file, detecting line endings and normalizing internally."""
        self.filename = filepath
        self.line_ending = '\n'
        self.had_final_newline = False
        
        if filepath and os.path.exists(filepath):
            try:
                # Read raw to detect line endings
                with open(filepath, 'r', encoding='utf-8', newline='') as f:
                    content = f.read()
                    
                # Detect dominant line ending
                crlf_count = content.count('\r\n')
                temp = content.replace('\r\n', '')  # Don't double count
                cr_count = temp.count('\r')
                lf_count = temp.count('\n')
                
                if crlf_count >= lf_count and crlf_count >= cr_count and crlf_count > 0:
                    self.line_ending = '\r\n'
                elif cr_count > lf_count and cr_count > 0:
                    self.line_ending = '\r'
                else:
                    self.line_ending = '\n'
                    
                self.had_final_newline = content.endswith(('\n', '\r'))
                
                # Normalize to \n for internal buffer (keeps cursor math clean!)
                content = content.replace('\r\n', '\n').replace('\r', '\n')
                
                spaces = " " * self.config.tab_size
                self.lines = content.replace('\t', spaces).split('\n')
                
                # If file ended with a newline, split() creates an extra empty string.
                # Remove it to keep the internal representation accurate.
                if self.had_final_newline and self.lines and self.lines[-1] == '':
                    self.lines.pop()
                    
                if not self.lines:
                    self.lines = [""]
            except Exception as e:
                self.lines = [f"Error reading file: {e}"]
        else:
            self.lines = [""]
            
        self.modified = False
        self.revision = 0

    def save(self):
        """Atomic save with correct line endings and trailing newline."""
        if not self.filename:
            return False
            
        # Determine ending to use (config overrides detected)
        ending = self.line_ending
        cfg_ending = getattr(self.config, 'line_ending', 'auto')
        if cfg_ending == 'crlf':
            ending = '\r\n'
        elif cfg_ending == 'cr':
            ending = '\r'
        elif cfg_ending == 'lf':
            ending = '\n'
            
        final_nl = getattr(self.config, 'final_newline', True)
        
        tmp = self.filename + ".femto-tmp"
        try:
            with open(tmp, 'w', encoding='utf-8', newline='') as f:
                text = ending.join(self.lines)
                # Add trailing newline if configured, or if the original file had one
                if final_nl or self.had_final_newline:
                    text += ending
                f.write(text)
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
        line = self.lines[y]
        self.lines[y] = line[:x] + char + line[x:]
        self.touch()

    def insert_newline(self, x, y):
        line = self.lines[y]
        self.lines[y] = line[:x]
        self.lines.insert(y + 1, line[x:])
        self.touch()

    def delete_char(self, x, y):
        if x < len(self.lines[y]):
            line = self.lines[y]
            self.lines[y] = line[:x] + line[x + 1:]
            self.touch()
        elif x == len(self.lines[y]) and y < len(self.lines) - 1:
            self.lines[y] += self.lines[y + 1]
            del self.lines[y + 1]
            self.touch()

    def backspace(self, x, y):
        if x > 0:
            self.delete_char(x - 1, y)
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
        spaces = " " * self.config.tab_size
        line = self.lines[y]
        self.lines[y] = line[:x] + spaces + line[x:]
        self.touch()
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
            self.touch()
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
        hit = find_next(self, term, SearchOptions(), start_x, start_y)
        return (hit[0], hit[1]) if hit else None

    # ── Helpers ───────────────────────────────────────────────

    def get_line_length(self, y):
        if 0 <= y < len(self.lines):
            return len(self.lines[y])
        return 0

    @property
    def max_y(self):
        return max(0, len(self.lines) - 1)
