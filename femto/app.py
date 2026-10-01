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
        self.message = "" # Clear transient messages

        # --- Commands ---
        if key == Key.CTRL_X:
            self.running = False
            return
        elif key == Key.CTRL_S:
            if self.buffer.save():
                self.message = "File saved successfully."
            else:
                self.message = "Error saving file! (No filename?)"
            return

        # --- Navigation ---
        elif key == Key.ARROW_UP:
            self.cursor.move(0, -1, self.buffer.get_line_length, self.buffer.max_y)
        elif key == Key.ARROW_DOWN:
            self.cursor.move(0, 1, self.buffer.get_line_length, self.buffer.max_y)
        elif key == Key.ARROW_LEFT:
            if self.cursor.x > 0:
                self.cursor.x -= 1
            elif self.cursor.y > 0:
                self.cursor.y -= 1
                self.cursor.x = self.buffer.get_line_length(self.cursor.y)
        elif key == Key.ARROW_RIGHT:
            line_len = self.buffer.get_line_length(self.cursor.y)
            if self.cursor.x < line_len:
                self.cursor.x += 1
            elif self.cursor.y < self.buffer.max_y:
                self.cursor.y += 1
                self.cursor.x = 0

        # --- Editing ---
        elif is_backspace(key):
            self.cursor.x, self.cursor.y = self.buffer.backspace(
                self.cursor.x, self.cursor.y
            )
        elif key == Key.DELETE:
            self.buffer.delete_char(self.cursor.x, self.cursor.y)
        elif is_enter(key):
            self.buffer.insert_newline(self.cursor.x, self.cursor.y)
            self.cursor.y += 1
            self.cursor.x = 0
        elif 32 <= key <= 126:
            # Printable ASCII characters
            char = chr(key)
            self.buffer.insert_char(self.cursor.x, self.cursor.y, char)
            self.cursor.x += 1

    def main_loop(self, stdscr):
        """The core event loop running inside curses.wrapper."""
        renderer = Renderer(stdscr)
        
        while self.running:
            # Update scrolling based on cursor position
            screen_rows, screen_cols = renderer.get_dimensions()
            self.cursor.update_scroll(screen_rows, screen_cols)
            
            # Render the UI
            renderer.render(self.buffer, self.cursor, self.message)
            
            # Wait for input
            try:
                key = stdscr.getch()
            except KeyboardInterrupt:
                self.running = False
                break
                
            if key == Key.RESIZE:
                continue # Curses handles resize, just redraw on next loop

            self.handle_input(key, screen_rows, screen_cols)

    def run(self):
        """Entry point to start the curses application."""
        try:
            curses.wrapper(self.main_loop)
        except Exception as e:
            print(f"Femto crashed: {e}")
