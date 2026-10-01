"""
Terminal rendering engine for Femto using curses.
"""

import curses
from femto import __version__, __app_name__

class Renderer:
    """Handles all drawing operations to the terminal."""
    
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.setup_colors()

    def setup_colors(self):
        """Initialize color pairs."""
        curses.start_color()
        curses.use_default_colors()
        # Status bar colors (White text on Blue background)
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLUE)
        # Warning/Error colors
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)

    def get_dimensions(self):
        """Return usable text area rows and cols."""
        height, width = self.stdscr.getmaxyx()
        # Reserve 2 rows at the bottom for status and help bars
        return max(1, height - 2), max(1, width)

    def draw_text(self, buffer, cursor, screen_rows, screen_cols):
        """Draw the text buffer to the screen."""
        for row in range(screen_rows):
            buf_y = row + cursor.scroll_y
            self.stdscr.move(row, 0)
            self.stdscr.clrtoeol()
            
            if buf_y < len(buffer.lines):
                line = buffer.lines[buf_y]
                # Apply horizontal scrolling
                visible_line = line[cursor.scroll_x : cursor.scroll_x + screen_cols]
                try:
                    self.stdscr.addstr(row, 0, visible_line)
                except curses.error:
                    pass # Ignore writing to the very bottom-right corner
            else:
                # Draw tilde for empty lines like nano/vim
                try:
                    self.stdscr.addstr(row, 0, "~", curses.A_BOLD)
                except curses.error:
                    pass

    def draw_status_bar(self, buffer, screen_rows, screen_cols, message=""):
        """Draw the nano-style status bar and help bar."""
        # --- Line 1: File info & Message ---
        status_text = f" {__app_name__} v{__version__}"
        if buffer.filename:
            status_text += f"  File: {buffer.filename}"
        else:
            status_text += "  New Buffer"
            
        if buffer.modified:
            status_text += "  [Modified]"
            
        if message:
            status_text += f"  >> {message}"

        # Pad to fill screen width
        status_text = status_text.ljust(screen_cols)[:screen_cols]
        
        try:
            self.stdscr.addstr(screen_rows, 0, status_text, curses.color_pair(1))
        except curses.error:
            pass

        # --- Line 2: Help shortcuts ---
        help_text = "^X Exit    ^S Save"
        help_text = help_text.ljust(screen_cols)[:screen_cols]
        try:
            self.stdscr.addstr(screen_rows + 1, 0, help_text, curses.color_pair(1))
        except curses.error:
            pass

    def draw_cursor(self, cursor):
        """Position the terminal cursor."""
        draw_y = cursor.y - cursor.scroll_y
        draw_x = cursor.x - cursor.scroll_x
        try:
            self.stdscr.move(draw_y, draw_x)
        except curses.error:
            pass

    def render(self, buffer, cursor, message=""):
        """Main render loop call."""
        self.stdscr.erase()
        screen_rows, screen_cols = self.get_dimensions()
        
        self.draw_text(buffer, cursor, screen_rows, screen_cols)
        self.draw_status_bar(buffer, screen_rows, screen_cols, message)
        self.draw_cursor(cursor)
        
        self.stdscr.refresh()
