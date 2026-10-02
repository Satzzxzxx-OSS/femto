"""
Terminal rendering engine for Femto using curses.
Soft wrap, horizontal-scroll fallback, selection + match highlighting.
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
        self.match_attr = curses.A_REVERSE | curses.A_BOLD
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
            self.match_attr = curses.color_pair(2)
        except curses.error:
            pass

    def get_dimensions(self):
        height, width = self.stdscr.getmaxyx()
        return max(1, height - 2), max(1, width)

    # ── Text area ─────────────────────────────────────────────

    def draw_text(self, buffer, cursor, screen_rows, screen_cols,
                  sel=None, match=None):
        if not self.config.soft_wrap:
            self._draw_text_hard(buffer, cursor, screen_rows, screen_cols,
                                 sel, match)
            return

        visual_row = 0
        for y, line in enumerate(buffer.lines):
            x0 = 0  # logical char offset of the current chunk start
            for chunk in chunk_line(line, screen_cols):
                if visual_row < cursor.scroll_y:
                    visual_row += 1
                elif visual_row >= cursor.scroll_y + screen_rows:
                    return
                else:
                    draw_y = visual_row - cursor.scroll_y
                    self.stdscr.move(draw_y, 0)
                    self.stdscr.clrtoeol()
                    self._draw_chunk(draw_y, chunk, x0, y, sel, match)
                    visual_row += 1
                x0 += len(chunk)

        while visual_row - cursor.scroll_y < screen_rows:
            draw_y = visual_row - cursor.scroll_y
            if draw_y >= 0:
                self.stdscr.move(draw_y, 0)
                self.stdscr.clrtoeol()
                self._safe_addstr(draw_y, 0, "~", curses.A_BOLD)
            visual_row += 1

    def _draw_text_hard(self, buffer, cursor, screen_rows, screen_cols,
                        sel, match):
        for row in range(screen_rows):
            y = row + cursor.scroll_y
            self.stdscr.move(row, 0)
            self.stdscr.clrtoeol()
            if y < len(buffer.lines):
                x0 = cursor.scroll_x
                chunk = buffer.lines[y][x0:x0 + screen_cols]
                self._draw_chunk(row, chunk, x0, y, sel, match)
            else:
                self._safe_addstr(row, 0, "~", curses.A_BOLD)

    # ── highlight machinery ───────────────────────────────────

    def _overlap(self, bounds, x0, y, chunk_len):
        """Intersection of a logical span with this chunk; (lo, hi) or None."""
        (sx, sy), (ex, ey) = bounds
        if not (sy <= y <= ey):
            return None
        line_start = sx if y == sy else 0
        line_end = ex if y == ey else x0 + chunk_len
        lo = max(0, line_start - x0)
        hi = min(chunk_len, line_end - x0)
        return (lo, hi) if lo < hi else None

    def _draw_chunk(self, row, chunk, x0, y, sel, match):
        if not chunk:
            return
        intervals = []
        if sel is not None:
            iv = self._overlap(sel, x0, y, len(chunk))
            if iv:
                intervals.append((iv[0], iv[1], self.sel_attr))
        if match is not None:
            mx, my, ml = match
            iv = self._overlap(((mx, my), (mx + ml, my)), x0, y, len(chunk))
            if iv:
                intervals.append((iv[0], iv[1], self.match_attr))
        if not intervals:
            self._safe_addstr(row, 0, chunk)
            return
        intervals.sort()
        col = 0
        for lo, hi, attr in intervals:
            lo = max(lo, col)          # first span wins on overlap
            if lo >= hi:
                continue
            if lo > col:
                self._safe_addstr(row, col, chunk[col:lo])
            self._safe_addstr(row, lo, chunk[lo:hi], attr)
            col = hi
        if col < len(chunk):
            self._safe_addstr(row, col, chunk[col:])

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
            "^X Exit  ^S Save  ^W Find  ^\\ Replace  ^K Cut  ^U Paste  ^Z Undo",
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

    def _draw_confirm(self, display, help_text, screen_rows, screen_cols):
        self._draw_bar(screen_rows, display, screen_cols, self.prompt_attr)
        self._draw_bar(screen_rows + 1, help_text, screen_cols, self.bar_attr)

    def draw_exit_confirm(self, message, screen_rows, screen_cols):
        self._draw_confirm(
            f" {message}  (Y)es / (N)o / (C)ancel",
            "Y Yes    N No    C Cancel", screen_rows, screen_cols)

    def draw_replace_confirm(self, message, screen_rows, screen_cols):
        self._draw_confirm(
            f" {message}  (Y)es / (N)o / (A)ll / (C)ancel",
            "Y Yes    N No    A All    C Cancel", screen_rows, screen_cols)

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
        "search": "Enter Find Next    M-C Case    M-R Regex    ^G Cancel",
        "replace_search": "Enter Continue    M-C Case    M-R Regex    ^G Cancel",
        "replace_with": "Enter Confirm    ^G Cancel",
        "goto_line": "Enter Jump    ^G Cancel",
    }

    def render(self, buffer, cursor, message="", prompt=None, mode="normal",
               selection=None, mark_set=False, match=None):
        self.stdscr.erase()
        screen_rows, screen_cols = self.get_dimensions()
        self.draw_text(buffer, cursor, screen_rows, screen_cols,
                       selection, match)

        if prompt and prompt.active and mode in self._PROMPT_HELP:
            self.draw_prompt(prompt, screen_rows, screen_cols,
                             self._PROMPT_HELP[mode])
        elif mode == "exit_confirm":
            self.draw_exit_confirm(message, screen_rows, screen_cols)
            self.draw_cursor(cursor, buffer, screen_cols)
        elif mode == "replace_confirm":
            self.draw_replace_confirm(message, screen_rows, screen_cols)
            self.draw_cursor(cursor, buffer, screen_cols)
        else:
            self.draw_status_bar(buffer, cursor, screen_rows, screen_cols,
                                 message, mark_set)
            self.draw_cursor(cursor, buffer, screen_cols)

        self.stdscr.refresh()
