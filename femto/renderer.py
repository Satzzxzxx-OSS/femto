"""
Terminal rendering engine for Femto using curses.
Supports soft wrap, line numbers, syntax highlighting, and selection/match overlays.
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
        self.match_attr = curses.color_pair(2)
        self.gutter_attr = curses.A_BOLD
        self.setup_colors()

    def setup_colors(self):
        if BAR_STYLE != "color":
            return
        try:
            curses.start_color()
            # Try to use default colors for transparent backgrounds
            try:
                curses.use_default_colors()
                bg = -1
            except curses.error:
                bg = curses.COLOR_BLACK
                
            curses.init_pair(1, curses.COLOR_BLACK, curses.COLOR_CYAN)
            curses.init_pair(2, curses.COLOR_BLACK, curses.COLOR_YELLOW)
            
            # Syntax colors
            curses.init_pair(3, curses.COLOR_GREEN, bg)
            curses.init_pair(4, curses.COLOR_MAGENTA, bg)
            curses.init_pair(5, curses.COLOR_CYAN, bg)
            curses.init_pair(6, curses.COLOR_YELLOW, bg)
            
            # Gutter color
            curses.init_pair(7, curses.COLOR_BLUE, bg)
            
            self.bar_attr = curses.color_pair(1)
            self.prompt_attr = curses.color_pair(2) | curses.A_BOLD
            self.match_attr = curses.color_pair(2)
            self.gutter_attr = curses.color_pair(7) | curses.A_BOLD
        except curses.error:
            pass

    def get_dimensions(self):
        height, width = self.stdscr.getmaxyx()
        return max(1, height - 2), max(1, width)

    # ── Text area ─────────────────────────────────────────────

    def draw_text(self, buffer, cursor, screen_rows, screen_cols,
                  sel=None, match=None):
        gutter_width = len(str(len(buffer.lines))) + 1 if self.config.show_line_numbers else 0
        text_cols = max(1, screen_cols - gutter_width)
        
        if not self.config.soft_wrap:
            self._draw_text_hard(buffer, cursor, screen_rows, text_cols,
                                 sel, match, gutter_width)
            return

        visual_row = 0
        for y, line in enumerate(buffer.lines):
            chunks = chunk_line(line, text_cols)
            
            for i, chunk in enumerate(chunks):
                if visual_row < cursor.scroll_y:
                    visual_row += 1
                    continue
                if visual_row >= cursor.scroll_y + screen_rows:
                    return
                    
                draw_y = visual_row - cursor.scroll_y
                
                # Draw Gutter
                if self.config.show_line_numbers:
                    self.stdscr.move(draw_y, 0)
                    if i == 0: # First visual row of logical line
                        num_str = str(y + 1).rjust(gutter_width - 1) + " "
                        self._safe_addstr(draw_y, 0, num_str, self.gutter_attr)
                    else:
                        self._safe_addstr(draw_y, 0, " " * gutter_width)
                
                # Draw Text
                self.stdscr.move(draw_y, gutter_width)
                self.stdscr.clrtoeol() 
                
                # Get highlights
                highlights = []
                if self.config.syntax_highlight and buffer.filename and buffer.filename.endswith('.py'):
                    from femto.highlight import get_spans
                    highlights = get_spans(line)
                
                # Calculate logical start of this chunk
                logical_x0 = sum(len(c) for c in chunks[:i])
                
                self._draw_chunk(draw_y, chunk, logical_x0, y, sel, match, highlights, gutter_width)
                visual_row += 1

        while visual_row - cursor.scroll_y < screen_rows:
            draw_y = visual_row - cursor.scroll_y
            if draw_y >= 0:
                self.stdscr.move(draw_y, 0)
                self.stdscr.clrtoeol()
                if self.config.show_line_numbers:
                    self._safe_addstr(draw_y, 0, " " * gutter_width)
                self._safe_addstr(draw_y, gutter_width, "~", curses.A_BOLD)
            visual_row += 1

    def _draw_text_hard(self, buffer, cursor, screen_rows, text_cols,
                        sel, match, gutter_width):
        for row in range(screen_rows):
            y = row + cursor.scroll_y
            self.stdscr.move(row, 0)
            self.stdscr.clrtoeol()
            
            if self.config.show_line_numbers:
                if y < len(buffer.lines):
                    num_str = str(y + 1).rjust(gutter_width - 1) + " "
                    self._safe_addstr(row, 0, num_str, self.gutter_attr)
                else:
                    self._safe_addstr(row, 0, " " * gutter_width)
                    
            if y < len(buffer.lines):
                x0 = cursor.scroll_x
                chunk = buffer.lines[y][x0:x0 + text_cols]
                
                highlights = []
                if self.config.syntax_highlight and buffer.filename and buffer.filename.endswith('.py'):
                    from femto.highlight import get_spans
                    highlights = get_spans(buffer.lines[y])
                    
                self._draw_chunk(row, chunk, x0, y, sel, match, highlights, gutter_width)
            else:
                self._safe_addstr(row, gutter_width, "~", curses.A_BOLD)

    # ── highlight & overlay machinery ─────────────────────────

    def _overlap(self, bounds, x0, y, chunk_len):
        (sx, sy), (ex, ey) = bounds
        if not (sy <= y <= ey):
            return None
        line_start = sx if y == sy else 0
        line_end = ex if y == ey else x0 + chunk_len
        lo = max(0, line_start - x0)
        hi = min(chunk_len, line_end - x0)
        return (lo, hi) if lo < hi else None

    def _draw_chunk(self, row, chunk, x0, y, sel, match, highlights, gutter_offset=0):
        if not chunk:
            return
            
        intervals = []
        
        # 1. Syntax Highlights (lowest priority)
        for hs, he, color_id in highlights:
            lo = max(0, hs - x0)
            hi = min(len(chunk), he - x0)
            if lo < hi:
                intervals.append((lo, hi, curses.color_pair(color_id)))
                
        # 2. Search Match
        if match is not None:
            mx, my, ml = match
            if my == y:
                lo = max(0, mx - x0)
                hi = min(len(chunk), mx + ml - x0)
                if lo < hi:
                    intervals.append((lo, hi, self.match_attr))
                    
        # 3. Selection (highest priority)
        if sel is not None:
            iv = self._overlap(sel, x0, y, len(chunk))
            if iv:
                intervals.append((iv[0], iv[1], self.sel_attr))
                
        # Draw base text
        self._safe_addstr(row, gutter_offset, chunk)
        
        # Overlay intervals (later intervals overwrite earlier ones)
        for lo, hi, attr in intervals:
            self._safe_addstr(row, gutter_offset + lo, chunk[lo:hi], attr)

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
        if self.config.mouse:
            status += "  [Mouse]"
        status += f"  Ln {cursor.y + 1}, Col {cursor.x + 1}"
        if message:
            status += f"  | {message}"

        self._draw_bar(screen_rows, status, screen_cols, self.bar_attr)
        self._draw_bar(
            screen_rows + 1,
            "^X Exit  ^S Save  ^W Find  ^K Cut  ^U Paste  M-N Lines  M-M Mouse",
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
        gutter_width = len(str(len(buffer.lines))) + 1 if self.config.show_line_numbers else 0
        text_cols = max(1, screen_cols - gutter_width)
        
        vx, vy = get_visual_position(
            cursor.x, cursor.y, buffer.lines, text_cols,
            self.config.soft_wrap)
        try:
            self.stdscr.move(vy - cursor.scroll_y, vx - cursor.scroll_x + gutter_width)
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
