"""
Terminal rendering engine for Femto using curses.
Supports soft wrap, horizontal-scroll fallback and selection highlight.
"""

import curses
from femto import __version__, __app_name__
from femto.layout import chunk_line, get_visual_position

BAR_STYLE = "color"


class Renderer:
    def __init__(self, stdscr, config):
        self.stdscr = stdscr
        self.config = config
        self.bar_attr = curses.A_REVERSE
        self.prompt_attr = curses.A_REVERSE | curses.A_BOLD
        self.sel_attr = curses.A_REVERSE
        self.setup_colors()

    def setup_colors(self):
        if BAR_STYLE != "color":
            return
        try:
            curses.start_color()
            if not curses.has_colors():
                return
            curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
            curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_YELLOW)
            self.bar_attr = curses.color_pair(1)
            self.prompt_attr = curses.color_pair(2) | curses.A_BOLD
        except curses.error:
            pass

    def get_dimensions(self):
        height, width = self.stdscr.getmaxyx()
        return max(1, height - 2), max(1, width)

    # ── Text area ─────────────────────────────────────────────

    def draw_text(self, buffer, cursor, screen_rows, screen_cols, sel=None):
        if not self.config.soft_wrap:
            self._draw_text_hard(buffer, cursor, screen_rows, screen_cols, sel)
            return

        visual_row = 0
        for y, line in enumerate(buffer.lines):
            for i, chunk in enumerate(chunk_line(line, screen_cols)):
                if visual_row < cursor.scroll_y:
                    visual_row += 1
                    continue
                if visual_row >= cursor.scroll_y + screen_rows:
                    return
                draw_y = visual_row - cursor.scroll_y
                self.stdscr.move(draw_y, 0)
                self.stdscr.clrtoeol()
                self._draw_chunk(draw_y, chunk, i * screen_cols, y, sel)
                visual_row += 1

        while visual_row - cursor.scroll_y < screen_rows:
            draw_y = visual_row - cursor.scroll_y
            if draw_y >= 0:
                self.stdscr.move(draw_y, 0)
                self.stdscr.clrtoeol()
                self._safe_addstr(draw_y, 0, "~", curses.A_BOLD)
            visual_row += 1

    def _draw_text_hard(self, buffer, cursor, screen_rows, screen_cols, sel):
        for row in range(screen_rows):
            y = row + cursor.scroll_y
            self.stdscr.move(row, 0)
            self.stdscr.clrtoeol()
            if y < len(buffer.lines):
                x0 = cursor.scroll_x
                chunk = buffer.lines[y][x0:x0 + screen_cols]
                self._draw_chunk(row, chunk, x0, y, sel)
            else:
                self._safe_addstr(row, 0, "~", curses.A_BOLD)

    def _draw_chunk(self, row, chunk, x0, y, sel):
        """Draw one visual chunk, reverse-videoing the selected span."""
        if not chunk:
            return
        if sel is None:
            self._safe_addstr(row, 0, chunk)
            return
        (sx, sy), (ex, ey) = sel
        if not (sy <= y <= ey):
            self._safe_addstr(row, 0, chunk)
            return
        line_start = sx if y == sy else 0
        line_end = ex if y == ey else x0 + len(chunk)
        lo = max(0, line_start - x0)
        hi = min(len(chunk), line_end - x0)
        if lo >= hi:
            self._safe_addstr(row, 0, chunk)
            return
        if lo:
            self._safe_addstr(row, 0, chunk[:lo])
        self._safe_addstr(row, lo, chunk[lo:hi], self.sel_attr)
        if hi < len(chunk):
            self._safe_addstr(row, hi, chunk[hi:])

    def _safe_addstr(self, row, col, text, attr=0):
        try:
            if attr:
                self.stdscr.addstr(row, col, text, attr)
            else:
                self.stdscr.addstr(row, col, text)
        except curses.error:
            pass

    # ── Bottom bars ───────────────────────────────────────────

    def draw_status_bar(self, buffer, cursor, screen_rows, screen_cols,
                        message="", mark_set=False):
        status = f" {__app_name__} v{__version__}"
        status += f"  {buffer.filename or 'New Buffer'}"
        if buffer.modified:
            status += "  [Modified]"
        if mark_set:
            status += "  [Mark]"
        status += f"  Ln {cursor.y + 1}, Col {cursor.x + 1}"
        if message:
            status += f"  | {message}"

        self._draw_bar(screen_rows, status, screen_cols, self.bar_attr)
        self._draw_bar(
            screen_rows + 1,
            "^X Exit  ^S Save  ^W Find  ^K Cut  ^U Paste  M-A Mark  ^Z Undo",
            screen_cols, self.bar_attr,
        )

    def draw_prompt(self, prompt, screen_rows, screen_cols, help_text=""):
        self._draw_bar(screen_rows, prompt.get_display(screen_cols),
                       screen_cols, self.prompt_attr)
        self._draw_bar(screen_rows + 1, help_text, screen_cols, self.bar_attr)
        cx = min(prompt.get_cursor_x(), screen_cols - 1)
        try:
            self.stdscr.move(screen_rows, cx)
        except curses.error:
            pass

    def draw_exit_confirm(self, message, screen_rows, screen_cols):
        display = f" {message}  (Y)es / (N)o / (C)ancel"
        self._draw_bar(screen_rows, display, screen_cols, self.prompt_attr)
        self._draw_bar(screen_rows + 1, "Y Yes    N No    C Cancel",
                       screen_cols, self.bar_attr)

    def _draw_bar(self, row, text, width, attr):
        text = text.ljust(width)[:width]
        try:
            self.stdscr.addstr(row, 0, text, attr)
        except curses.error:
            pass

    def draw_cursor(self, cursor, buffer, screen_cols):
        vx, vy = get_visual_position(
            cursor.x, cursor.y, buffer.lines, screen_cols,
            self.config.soft_wrap)
        try:
            self.stdscr.move(vy - cursor.scroll_y, vx - cursor.scroll_x)
        except curses.error:
            pass

    _PROMPT_HELP = {
        "save_as": "Enter Save    ^G Cancel",
        "search": "Enter Find Next    ^G Cancel",
        "goto_line": "Enter Jump    ^G Cancel",
    }

    def render(self, buffer, cursor, message="", prompt=None, mode="normal",
               selection=None, mark_set=False):
        self.stdscr.erase()
        screen_rows, screen_cols = self.get_dimensions()
        self.draw_text(buffer, cursor, screen_rows, screen_cols, selection)

        if prompt and prompt.active and mode in self._PROMPT_HELP:
            self.draw_prompt(prompt, screen_rows, screen_cols,
                             self._PROMPT_HELP[mode])
        elif mode == "exit_confirm":
            self.draw_exit_confirm(message, screen_rows, screen_cols)
            self.draw_cursor(cursor, buffer, screen_cols)
        else:
            self.draw_status_bar(buffer, cursor, screen_rows, screen_cols,
                                 message, mark_set)
            self.draw_cursor(cursor, buffer, screen_cols)

        self.stdscr.refresh()
