"""
Main Application Controller for Femto.
"""

import signal
import curses

from femto.buffer import Buffer
from femto.cursor import Cursor
from femto.renderer import Renderer, get_visual_position
from femto.prompt import Prompt
from femto.history import History
from femto.config import Config
from femto.keys import Key, is_backspace, is_enter


def _ignore_suspend():
    sig = getattr(signal, "SIGTSTP", None)
    if sig is None: return
    try: signal.signal(sig, signal.SIG_IGN)
    except (OSError, ValueError): pass


class Mode:
    NORMAL = "normal"
    SAVE_AS = "save_as"
    SEARCH = "search"
    GOTO_LINE = "goto_line"
    EXIT_CONFIRM = "exit_confirm"


class Application:
    def __init__(self, filename=None):
        self.config = Config()
        self.buffer = Buffer(self.config)
        self.buffer.load_file(filename)
        self.cursor = Cursor()
        self.renderer = None
        self.message = ""
        self.running = True
        self.mode = Mode.NORMAL
        self.prompt = Prompt()
        self.history = History()
        self.pending_exit = False
        self.last_search = ""
        self.last_found_pos = None

    def _snapshot(self):
        self.history.push(self.buffer.lines, self.cursor.x, self.cursor.y)

    def handle_input(self, key, screen_rows, screen_cols):
        if self.mode == Mode.SAVE_AS: self._handle_save_as(key)
        elif self.mode == Mode.SEARCH: self._handle_search(key)
        elif self.mode == Mode.GOTO_LINE: self._handle_goto_line(key)
        elif self.mode == Mode.EXIT_CONFIRM: self._handle_exit_confirm(key)
        else: self._handle_normal(key, screen_rows, screen_cols)

    def _handle_save_as(self, key):
        result = self.prompt.handle_key(key)
        if result == 'confirmed':
            filename = self.prompt.text.strip()
            if not filename: return
            self.buffer.filename = filename
            if self.buffer.save(): self.message = f"Saved → {filename}"
            else: self.message = "Error: could not save file."
            self._exit_prompt_mode()
            if self.pending_exit: self.running = False
        elif result == 'cancelled':
            self._exit_prompt_mode()
            self.message = "Save cancelled."

    def _handle_search(self, key):
        result = self.prompt.handle_key(key)
        if result == 'confirmed':
            term = self.prompt.text
            if term:
                self.last_search = term
                self._find_text(term)
            self._exit_prompt_mode()
        elif result == 'cancelled':
            self._exit_prompt_mode()

    def _find_text(self, term):
        if self.last_found_pos == (self.cursor.x, self.cursor.y):
            start_x = self.cursor.x + 1
        else:
            start_x = self.cursor.x
        result = self.buffer.find_text(term, start_x, self.cursor.y)
        if result:
            x, y = result
            self.cursor.set_pos(x, y, self.buffer.get_line_length, self.buffer.max_y)
            self.last_found_pos = (x, y)
            self.message = f"Found: {term}"
        else:
            self.message = f"Not found: {term}"
            self.last_found_pos = None

    def _handle_goto_line(self, key):
        result = self.prompt.handle_key(key)
        if result == 'confirmed':
            raw = self.prompt.text.strip()
            try:
                target = int(raw)
                target_y = max(0, min(target - 1, self.buffer.max_y))
                self.cursor.set_pos(0, target_y, self.buffer.get_line_length, self.buffer.max_y)
                self.message = f"Line {target_y + 1}/{self.buffer.max_y + 1}"
            except ValueError:
                self.message = "Invalid line number."
            self._exit_prompt_mode()
        elif result == 'cancelled':
            self._exit_prompt_mode()

    def _handle_exit_confirm(self, key):
        if key in (ord('y'), ord('Y')):
            if self.buffer.filename:
                if self.buffer.save(): self.running = False
                else:
                    self.message = "Error: could not save file."
                    self.mode = Mode.NORMAL
            else:
                self.mode = Mode.SAVE_AS
                self.prompt.start("Save As: ")
                self.pending_exit = True
        elif key in (ord('n'), ord('N')): self.running = False
        elif key in (ord('c'), ord('C'), Key.CTRL_G, Key.ESCAPE):
            self.mode = Mode.NORMAL
            self.message = "Exit cancelled."

    def _handle_normal(self, key, screen_rows, screen_cols):
        self.message = ""
        buf = self.buffer
        cur = self.cursor
        max_x = buf.get_line_length
        max_y = buf.max_y

        if key == Key.CTRL_X:
            if buf.modified:
                self.mode = Mode.EXIT_CONFIRM
                self.message = "Save modified buffer?"
            else: self.running = False
            return
        if key == Key.CTRL_S:
            if buf.filename:
                if buf.save(): self.message = "File saved."
                else: self.message = "Error: could not save file."
            else:
                self.mode = Mode.SAVE_AS
                self.prompt.start("Save As: ")
            return
        if key == Key.CTRL_W:
            self.mode = Mode.SEARCH
            self.prompt.start("Search: ", self.last_search)
            return
        if key == Key.CTRL_T:
            self.mode = Mode.GOTO_LINE
            self.prompt.start("Go To Line: ")
            return
        if key == Key.CTRL_Z: self._do_undo(); return
        if key == Key.CTRL_Y: self._do_redo(); return

        if key == Key.CTRL_LEFT: cur.x = buf.get_prev_word_pos(cur.y, cur.x)
        elif key == Key.CTRL_RIGHT: cur.x = buf.get_next_word_pos(cur.y, cur.x)
        elif key == Key.PAGE_UP: cur.page_move(-screen_rows, max_x, max_y)
        elif key == Key.PAGE_DOWN: cur.page_move(screen_rows, max_x, max_y)
        elif key == Key.HOME or key == Key.CTRL_A: cur.home()
        elif key == Key.END or key == Key.CTRL_E: cur.end(max_x(cur.y))
        elif key == Key.ARROW_UP: cur.move(0, -1, max_x, max_y)
        elif key == Key.ARROW_DOWN: cur.move(0, 1, max_x, max_y)
        elif key == Key.ARROW_LEFT:
            if cur.x > 0: cur.x -= 1
            elif cur.y > 0:
                cur.y -= 1
                cur.x = max_x(cur.y)
        elif key == Key.ARROW_RIGHT:
            if cur.x < max_x(cur.y): cur.x += 1
            elif cur.y < max_y:
                cur.y += 1
                cur.x = 0
        elif key == Key.TAB:
            self._snapshot()
            cur.x = buf.insert_tab(cur.y, cur.x)
        elif key == Key.SHIFT_TAB:
            self._snapshot()
            cur.x = buf.remove_tab(cur.y, cur.x)
        elif is_backspace(key):
            self._snapshot()
            cur.x, cur.y = buf.backspace(cur.x, cur.y)
        elif key == Key.DELETE:
            self._snapshot()
            buf.delete_char(cur.x, cur.y)
        elif is_enter(key):
            self._snapshot()
            buf.insert_newline(cur.x, cur.y)
            cur.y += 1
            cur.x = 0
        elif 32 <= key <= 126:
            self._snapshot()
            buf.insert_char(cur.x, cur.y, chr(key))
            cur.x += 1

    def _do_undo(self):
        result = self.history.undo(self.buffer.lines, self.cursor.x, self.cursor.y)
        if result:
            lines, x, y = result
            self.buffer.lines = lines
            self.buffer.modified = True
            self.cursor.set_pos(x, y, self.buffer.get_line_length, self.buffer.max_y)
            self.message = "Undo."
        else: self.message = "Nothing to undo."

    def _do_redo(self):
        result = self.history.redo(self.buffer.lines, self.cursor.x, self.cursor.y)
        if result:
            lines, x, y = result
            self.buffer.lines = lines
            self.buffer.modified = True
            self.cursor.set_pos(x, y, self.buffer.get_line_length, self.buffer.max_y)
            self.message = "Redo."
        else: self.message = "Nothing to redo."

    def _exit_prompt_mode(self):
        self.prompt.deactivate()
        self.mode = Mode.NORMAL
        self.pending_exit = False

    def main_loop(self, stdscr):
        _ignore_suspend()
        self.renderer = Renderer(stdscr, self.config)

        while self.running:
            screen_rows, screen_cols = self.renderer.get_dimensions()
            
            # Calculate visual Y for smooth scrolling before drawing
            _, vy = get_visual_position(self.cursor.x, self.cursor.y, self.buffer.lines, screen_cols)
            self.cursor.update_scroll(vy, screen_rows, self.config.smooth_scroll_margin)

            self.renderer.render(
                self.buffer, self.cursor, message=self.message,
                prompt=self.prompt, mode=self.mode,
            )

            try: key = stdscr.getch()
            except KeyboardInterrupt:
                self.running = False
                break

            if key == Key.RESIZE: continue
            self.handle_input(key, screen_rows, screen_cols)

    def run(self):
        try: curses.wrapper(self.main_loop)
        except Exception as e: print(f"Femto crashed: {e}")
