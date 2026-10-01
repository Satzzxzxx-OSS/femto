"""
Keybindings and input mapping for Femto.
"""

import curses

class Key:
    """Constants for keyboard inputs."""
    # Commands
    CTRL_X = 24      # Exit
    CTRL_S = 19      # Save
    CTRL_A = 1       # Home (nano-style)
    CTRL_E = 5       # End (nano-style)

    # Arrows
    ARROW_UP = curses.KEY_UP
    ARROW_DOWN = curses.KEY_DOWN
    ARROW_LEFT = curses.KEY_LEFT
    ARROW_RIGHT = curses.KEY_RIGHT

    # Word navigation (Ctrl+Left / Ctrl+Right)
    CTRL_LEFT = curses.KEY_SLEFT
    CTRL_RIGHT = curses.KEY_SRIGHT

    # Page navigation
    PAGE_UP = curses.KEY_PPAGE
    PAGE_DOWN = curses.KEY_NPAGE

    # Home / End
    HOME = curses.KEY_HOME
    END = curses.KEY_END

    # Editing keys
    BACKSPACE = (curses.KEY_BACKSPACE, 127, 8)
    DELETE = curses.KEY_DC
    ENTER = (curses.KEY_ENTER, 10, 13)
    TAB = 9
    SHIFT_TAB = curses.KEY_BTAB

    # Terminal
    RESIZE = curses.KEY_RESIZE


def is_backspace(key):
    return key in Key.BACKSPACE

def is_enter(key):
    return key in Key.ENTER
