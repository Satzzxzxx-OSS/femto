"""
Main Application Controller for Femto.
Implements a simple mode state-machine:
    NORMAL → SAVE_AS → NORMAL
    NORMAL → EXIT_CONFIRM → (SAVE_AS | exit)
"""

import curses
from femto.buffer import Buffer
from femto.cursor import Cursor
from femto.renderer import Renderer
from femto.prompt import Prompt
from femto.keys import Key, is_backspace, is_enter


class Mode:
    """Application input modes."""
    NORMAL = "normal"
    SAVE_AS = "save_as"
    EXIT_CONFIRM = "exit_confirm"


class Application:
    """Ties together buffer, cursor, renderer, prompt, and the input loop."""

    def __init__(self, filename=None):
        self.buffer = Buffer()
        self.buffer.load_file(filename)
        self.cursor = Cursor()
        self.renderer = None          # assigned inside main_loop
        self.message = ""
        self.running = True
        self.mode = Mode.NORMAL
        self.prompt = Prompt()
        self.pending_exit = False     # exit after Save-As completes

    # ── Input routing ─────────────────────────────────────────

    def handle_input(self, key, screen_rows, screen_cols):
        """Route a keypress to the handler for the current mode."""
        if self.mode == Mode.SAVE_AS:
            self._handle_save_as(key)
        elif self.mode == Mode.EXIT_CONFIRM:
            self._handle_exit_confirm(key)
        else:
            self._handle_normal(key, screen_rows, screen_cols)

    # ── SAVE AS mode ──────────────────────────────────────────

    def _handle_save_as(self, key):
        result = self.prompt.handle_key(key)

        if result == 'confirmed':
            filename = self.prompt.text.strip()
            if not filename:
                # Empty name → stay in prompt so user can type
                return
            self.buffer.filename = filename
            if self.buffer.save():
                self.message = f"Saved → {filename}"
            else:
                self.message = "Error: could not save file."
            self._exit_prompt_mode()
            if self.pending_exit:
                self.running = False

        elif result == 'cancelled':
            self._exit_prompt_mode()
            self.message = "Save cancelled."

    def _exit_prompt_mode(self):
        self.prompt.deactivate()
        self.mode = Mode.NORMAL
        self.pending_exit = False

    # ── EXIT CONFIRM mode ─────────────────────────────────────

    def _handle_exit_confirm(self, key):
        # Yes → save then exit
        if key in (ord('y'), ord('Y')):
            if self.buffer.filename:
                if self.buffer.save():
                    self.running = False
                else:
                    self.message = "Error: could not save file."
                    self.mode = Mode.NORMAL
            else:
                # No filename yet → ask for one, then exit
                self.mode = Mode.SAVE_AS
                self.prompt.start("Save As: ")
                self.pending_exit = True

        # No → discard and exit
        elif key in (ord('n'), ord('N')):
            self.running = False

        # Cancel → back to editing
        elif key in (ord('c'), ord('C'), Key.CTRL_G, Key.ESCAPE):
            self.mode = Mode.NORMAL
            self.message = "Exit cancelled."

    # ── NORMAL mode ───────────────────────────────────────────

    def _handle_normal(self, key, screen_rows, screen_cols):
        self.message = ""
        buf = self.buffer
        cur = self.cursor
        max_x = buf.get_line_length
        max_y = buf.max_y

        # ── File commands ─────────────────────────────────────
        if key == Key.CTRL_X:
            if buf.modified:
                self.mode = Mode.EXIT_CONFIRM
                self.message = "Save modified buffer?"
            else:
                self.running = False
            return

        if key == Key.CTRL_S:
            if buf.filename:
                if buf.save():
                    self.message = "File saved."
                else:
                    self.message = "Error: could not save file."
            else:
                self.mode = Mode.SAVE_AS
                self.prompt.start("Save As: ")
            return

        # ── Word navigation ───────────────────────────────────
        if key == Key.CTRL_LEFT:
            cur.x = buf.get_prev_word_pos(cur.y, cur.x)
        elif key == Key.CTRL_RIGHT:
            cur.x = buf.get_next_word_pos(cur.y, cur.x)

        # ── Page navigation ───────────────────────────────────
        elif key == Key.PAGE_UP:
            cur.page_move(-screen_rows, max_x, max_y)
        elif key == Key.PAGE_DOWN:
            cur.page_move(screen_rows, max_x, max_y)

        # ── Home / End ────────────────────────────────────────
        elif key == Key.HOME or key == Key.CTRL_A:
            cur.home()
        elif key == Key.END or key == Key.CTRL_E:
            cur.end(max_x(cur.y))

        # ── Arrow navigation ──────────────────────────────────
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

    # ── Main loop ─────────────────────────────────────────────

    def main_loop(self, stdscr):
        """Core event loop inside curses.wrapper."""
        self.renderer = Renderer(stdscr)

        while self.running:
            screen_rows, screen_cols = self.renderer.get_dimensions()
            self.cursor.update_scroll(screen_rows, screen_cols)

            self.renderer.render(
                self.buffer,
                self.cursor,
                message=self.message,
                prompt=self.prompt,
                mode=self.mode,
            )

            try:
                key = stdscr.getch()
            except KeyboardInterrupt:
                self.running = False
                break

            if key == Key.RESIZE:
                continue

            self.handle_input(key, screen_rows, screen_cols)

    def run(self):
        """Entry point – wraps the main loop with curses initialisation."""
        try:
            curses.wrapper(self.main_loop)
        except Exception as e:
            print(f"Femto crashed: {e}")
