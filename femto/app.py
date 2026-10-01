"""
Main Application Controller for Femto.
"""

import curses
from femto.buffer import Buffer
from femto.cursor import Cursor
from femto.renderer import Renderer
from femto.keys import Key, is_backspace, is_enter


class Application:
    """Ties together the buffer, cursor, renderer, and input loop."""

    def __init__(self, filename=None):
        self.buffer = Buffer()
        self.buffer.load_file(filename)
        self.cursor = Cursor()
        self.message = ""
        self.running = True

    def handle_input(self, key, screen_rows, screen_cols):
        """Process a single keystroke."""
        self.message = ""
        buf = self.buffer
        cur = self.cursor
        max_x = buf.get_line_length
        max_y = buf.max_y

        # ── Commands ──────────────────────────────────────────
        if key == Key.CTRL_X:
            self.running = False
            return
        elif key == Key.CTRL_S:
            if buf.save():
                self.message = "File saved successfully."
            else:
                self.message = "Error saving file! (No filename?)"
            return

        # ── Word Navigation (Ctrl+Left / Ctrl+Right) ──────────
        elif key == Key.CTRL_LEFT:
            cur.x = buf.get_prev_word_pos(cur.y, cur.x)
        elif key == Key.CTRL_RIGHT:
            cur.x = buf.get_next_word_pos(cur.y, cur.x)

        # ── Page Navigation ───────────────────────────────────
        elif key == Key.PAGE_UP:
            cur.page_move(-screen_rows, max_x, max_y)
        elif key == Key.PAGE_DOWN:
            cur.page_move(screen_rows, max_x, max_y)

        # ── Home / End ────────────────────────────────────────
        elif key == Key.HOME or key == Key.CTRL_A:
            cur.home()
        elif key == Key.END or key == Key.CTRL_E:
            cur.end(max_x(cur.y))

        # ── Arrow Navigation ──────────────────────────────────
        elif key == Key.ARROW_UP:
            cur.move(0, -1, max_x, max_y)
        elif key == Key.ARROW_DOWN:
            cur.move(0, 1, max_x, max_y)
        elif key == Key.ARROW_LEFT:
            if cur.x > 0:
                cur.x -= 1
            elif cur.y > 0:
                cur.y -= 1
                cur.x = max_x(cur.y)
        elif key == Key.ARROW_RIGHT:
            if cur.x < max_x(cur.y):
                cur.x += 1
            elif cur.y < max_y:
                cur.y += 1
                cur.x = 0

        # ── Tab / Shift-Tab ───────────────────────────────────
        elif key == Key.TAB:
            cur.x = buf.insert_tab(cur.y, cur.x)
        elif key == Key.SHIFT_TAB:
            cur.x = buf.remove_tab(cur.y, cur.x)

        # ── Editing ───────────────────────────────────────────
        elif is_backspace(key):
            cur.x, cur.y = buf.backspace(cur.x, cur.y)
        elif key == Key.DELETE:
            buf.delete_char(cur.x, cur.y)
        elif is_enter(key):
            buf.insert_newline(cur.x, cur.y)
            cur.y += 1
            cur.x = 0
        elif 32 <= key <= 126:
            char = chr(key)
            buf.insert_char(cur.x, cur.y, char)
            cur.x += 1

    def main_loop(self, stdscr):
        """The core event loop running inside curses.wrapper."""
        renderer = Renderer(stdscr)

        while self.running:
            screen_rows, screen_cols = renderer.get_dimensions()
            self.cursor.update_scroll(screen_rows, screen_cols)
            renderer.render(self.buffer, self.cursor, self.message)

            try:
                key = stdscr.getch()
            except KeyboardInterrupt:
                self.running = False
                break

            if key == Key.RESIZE:
                continue

            self.handle_input(key, screen_rows, screen_cols)

    def run(self):
        """Entry point to start the curses application."""
        try:
            curses.wrapper(self.main_loop)
        except Exception as e:
            print(f"Femto crashed: {e}")
