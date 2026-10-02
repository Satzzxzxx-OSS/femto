"""
Terminal rendering engine for Femto using curses.
"""

import curses
from femto import __version__, __app_name__

# Bar style:
#   "color"   -> black text on cyan / yellow bars (classic, high contrast)
#   "reverse" -> plain reverse video (immune to custom console palettes)
BAR_STYLE = "reverse"


class Renderer:
    """Handles all drawing operations to the terminal."""

    def __init__(self, stdscr):
        self.stdscr = stdscr
        # Fallback attributes if colors are unavailable
        self.bar_attr = curses.A_REVERSE
        self.prompt_attr = curses.A_REVERSE | curses.A_BOLD
        self.setup_colors()

    def setup_colors(self):
        """Initialise high-contrast colour pairs (Windows-safe)."""
        if BAR_STYLE != "color":
            return
        try:
            curses.start_color()
            if not curses.has_colors():
                return
            # NOTE: deliberately NO use_default_colors() here - on
            # windows-curses it can wash out bar backgrounds.
            curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
            curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_YELLOW)
            self.bar_attr = curses.color_pair(1)
            self.prompt_attr = curses.color_pair(2) | curses.A_BOLD
        except curses.error:
            pass  # keep the reverse-video fallback

    def get_dimensions(self):
        height, width = self.stdscr.getmaxyx()
        return max(1, height - 2), max(1, width)

    # ── Text area ─────────────────────────────────────────────

    def draw_text(self, buffer, cursor, screen_rows, screen_cols):
        for row in range(screen_rows):
            buf_y = row + cursor.scroll_y
            self.stdscr.move(row, 0)
            self.stdscr.clrtoeol()

            if buf_y < len(buffer.lines):
                line = buffer.lines[buf_y]
                visible = line[cursor.scroll_x : cursor.scroll_x + screen_cols]
                try:
                    self.stdscr.addstr(row, 0, visible)
                except curses.error:
                    pass
            else:
                try:
                    self.stdscr.addstr(row, 0, "~", curses.A_BOLD)
                except curses.error:
                    pass

    # ── Bottom bars ───────────────────────────────────────────

    def draw_status_bar(self, buffer, cursor, screen_rows, screen_cols, message=""):
        status = f" {__app_name__} v{__version__}"
        status += f"  {buffer.filename or 'New Buffer'}"
        if buffer.modified:
            status += "  [Modified]"
        status += f"  Ln {cursor.y + 1}, Col {cursor.x + 1}"
        if message:
            status += f"  | {message}"

        self._draw_bar(screen_rows, status, screen_cols, self.bar_attr)
        self._draw_bar(
            screen_rows + 1,
            "^X Exit  ^S Save  ^W Find  ^T Line  ^Z Undo  ^Y Redo",
            screen_cols,
            self.bar_attr,
        )

    def draw_prompt(self, prompt, screen_rows, screen_cols, help_text=""):
        self._draw_bar(
            screen_rows,
            prompt.get_display(screen_cols),
            screen_cols,
            self.prompt_attr,
        )
        self._draw_bar(screen_rows + 1, help_text, screen_cols, self.bar_attr)
        cx = min(prompt.get_cursor_x(), screen_cols - 1)
        try:
            self.stdscr.move(screen_rows, cx)
        except curses.error:
            pass

    def draw_exit_confirm(self, message, screen_rows, screen_cols):
        display = f" {message}  (Y)es / (N)o / (C)ancel"
        self._draw_bar(screen_rows, display, screen_cols, self.prompt_attr)
        self._draw_bar(
            screen_rows + 1,
            "Y Yes    N No    C Cancel",
            screen_cols,
            self.bar_attr,
        )

    # ── Helpers ───────────────────────────────────────────────

    def _draw_bar(self, row, text, width, attr):
        text = text.ljust(width)[:width]
        try:
            self.stdscr.addstr(row, 0, text, attr)
        except curses.error:
            pass

    def draw_cursor(self, cursor):
        draw_y = cursor.y - cursor.scroll_y
        draw_x = cursor.x - cursor.scroll_x
        try:
            self.stdscr.move(draw_y, draw_x)
        except curses.error:
            pass

    # ── Main render entry ─────────────────────────────────────

    _PROMPT_HELP = {
        "save_as": "Enter Save    ^G Cancel",
        "search": "Enter Find Next    ^G Cancel",
        "goto_line": "Enter Jump    ^G Cancel",
    }

    def render(self, buffer, cursor, message="", prompt=None, mode="normal"):
        self.stdscr.erase()
        screen_rows, screen_cols = self.get_dimensions()
        self.draw_text(buffer, cursor, screen_rows, screen_cols)

        if prompt and prompt.active and mode in self._PROMPT_HELP:
            self.draw_prompt(
                prompt, screen_rows, screen_cols, self._PROMPT_HELP[mode]
            )
        elif mode == "exit_confirm":
            self.draw_exit_confirm(message, screen_rows, screen_cols)
            self.draw_cursor(cursor)
        else:
            self.draw_status_bar(
                buffer, cursor, screen_rows, screen_cols, message
            )
            self.draw_cursor(cursor)

        self.stdscr.refresh()
