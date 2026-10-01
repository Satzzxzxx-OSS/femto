"""
Keybindings and input mapping for Femto.
"""

import curses

class Key:
    """Constants for keyboard inputs."""
    CTRL_X = 24   # Exit
    CTRL_S = 19   # Save

    ARROW_UP = curses.KEY_UP
    ARROW_DOWN = curses.KEY_DOWN
    ARROW_LEFT = curses.KEY_LEFT
    ARROW_RIGHT = curses.KEY_RIGHT

    BACKSPACE = (curses.KEY_BACKSPACE, 127, 8)
    DELETE = curses.KEY_DC

    ENTER = (curses.KEY_ENTER, 10, 13)

    RESIZE = curses.KEY_RESIZE

def is_backspace(key):
    return key in Key.BACKSPACE

def is_enter(key):
    return key in Key.ENTER
