"""
Keybindings and input mapping for Femto.
"""

import curses


class Key:
    """Constants for keyboard inputs."""

    # File / mode commands
    CTRL_X = 24      # Exit
    CTRL_S = 19      # Save
    CTRL_G = 7       # Cancel prompt

    # Navigation helpers (nano-style)
    CTRL_A = 1       # Home
    CTRL_E = 5       # End

    # New in a04
    CTRL_W = 23      # Search / Find
    CTRL_T = 20      # Go To Line
    CTRL_Z = 26      # Undo
    CTRL_Y = 25      # Redo

    # Arrows
    ARROW_UP = curses.KEY_UP
    ARROW_DOWN = curses.KEY_DOWN
    ARROW_LEFT = curses.KEY_LEFT
    ARROW_RIGHT = curses.KEY_RIGHT

    # Word navigation
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
    ESCAPE = 27


def is_backspace(key):
    return key in Key.BACKSPACE


def is_enter(key):
    return key in Key.ENTER
