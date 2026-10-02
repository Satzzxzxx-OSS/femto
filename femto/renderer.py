"""
Terminal rendering engine for Femto using curses.
Supports soft line wrapping and visual cursor mapping.
"""

import curses
from femto import __version__, __app_name__

BAR_STYLE = "color"

def get_visual_position(logical_x, logical_y, lines, width):
    """Map logical (x,y) to visual (vx, vy) accounting for soft wrap."""
    vy = 0
    for i in range(logical_y):
        l = len(lines[i])
        vy += max(1, (l + width - 1) // width)
        
    l = len(lines[logical_y])
    if l == 0:
        return 0, vy
        
    offset_rows = logical_x // width
    vx = logical_x % width
    
    # If cursor is exactly at the end of a line that is a multiple of width,
    # it wraps to the next visual row at column 0.
    if logical_x == l and l > 0 and l % width == 0:
        offset_rows = (l // width)
        vx = 0
        
    return vx, vy + offset_rows


class Renderer:
    def __init__(self, stdscr, config):
        self.stdscr = stdscr
        self.config = config
        self.bar_attr = curses.A_REVERSE
        self.prompt_attr = curses.A_REVERSE | curses.A_BOLD
        self.setup_colors()

    def setup_colors(self):
        if BAR_STYLE != "color": return
        try:
            curses.start_color()
            if not curses.has_colors(): return
            curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
            curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_YELLOW)
            self.bar_attr = curses.color_pair(1)
            self.prompt_attr = curses.color_pair(2) | curses.A_BOLD
        except curses.error:
            pass

    def get_dimensions(self):
        height, width = self.stdscr.getmaxyx()
        return max(1, height - 2), max(1, width)

    def draw_text(self, buffer, cursor, screen_rows, screen_cols):
        visual_row = 0
        for logical_y, line in enumerate(buffer.lines):
            if not line:
                chunks = [""]
            else:
                chunks = [line[i:i+screen_cols] for i in range(0, len(line), screen_cols)]
            
            for chunk in chunks:
                if visual_row < cursor.scroll_y:
                    visual_row += 1
                    continue
                if visual_row >= cursor.scroll_y + screen_rows:
                    return
                
                draw_y = visual_row - cursor.scroll_y
                self.stdscr.move(draw_y, 0)
                self.stdscr.clrtoeol()
                
                if chunk:
                    try:
                        self.stdscr.addstr(draw_y, 0, chunk)
                    except curses.error:
                        pass
                
                visual_row += 1
                
        # Fill remaining screen rows with ~ (nano style)
        while visual_row - cursor.scroll_y < screen_rows:
            draw_y = visual_row - cursor.scroll_y
            if draw_y >= 0:
                self.stdscr.move(draw_y, 0)
                self.stdscr.clrtoeol()
                try:
                    self.stdscr.addstr(draw_y, 0, "~", curses.A_BOLD)
                except curses.error:
                    pass
            visual_row += 1

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
        self._draw_bar(screen_rows, prompt.get_display(screen_cols), screen_cols, self.prompt_attr)
        self._draw_bar(screen_rows + 1, help_text, screen_cols, self.bar_attr)
        cx = min(prompt.get_cursor_x(), screen_cols - 1)
        try: self.stdscr.move(screen_rows, cx)
        except curses.error: pass

    def draw_exit_confirm(self, message, screen_rows, screen_cols):
        display = f" {message}  (Y)es / (N)o / (C)ancel"
        self._draw_bar(screen_rows, display, screen_cols, self.prompt_attr)
        self._draw_bar(screen_rows + 1, "Y Yes    N No    C Cancel", screen_cols, self.bar_attr)

    def _draw_bar(self, row, text, width, attr):
        text = text.ljust(width)[:width]
        try: self.stdscr.addstr(row, 0, text, attr)
        except curses.error: pass

    def draw_cursor(self, cursor, buffer, screen_cols):
        vx, vy = get_visual_position(cursor.x, cursor.y, buffer.lines, screen_cols)
        draw_y = vy - cursor.scroll_y
        draw_x = vx
        try: self.stdscr.move(draw_y, draw_x)
        except curses.error: pass

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
            self.draw_prompt(prompt, screen_rows, screen_cols, self._PROMPT_HELP[mode])
        elif mode == "exit_confirm":
            self.draw_exit_confirm(message, screen_rows, screen_cols)
            self.draw_cursor(cursor, buffer, screen_cols)
        else:
            self.draw_status_bar(buffer, cursor, screen_rows, screen_cols, message)
            self.draw_cursor(cursor, buffer, screen_cols)

        self.stdscr.refresh()
