"""
Keybindings and input mapping for Femto.
"""

import curses

# Alt-modified keys are encoded with this bit so they never collide
# with printable ASCII (0-255) or curses KEY_* codes (< 512).
ALT_MASK = 0x1000


def alt(code):
    """Encode an Alt-modified key."""
    return code | ALT_MASK


def is_alt(key):
    return (key & ALT_MASK) != 0


def alt_code(key):
    return key & ~ALT_MASK


class Key:
    # File / mode commands
    CTRL_X = 24      # Exit
    CTRL_S = 19      # Save
    CTRL_G = 7       # Cancel prompt

    # Navigation helpers (nano-style)
    CTRL_A = 1       # Home
    CTRL_E = 5       # End

    # Search / goto / undo
    CTRL_W = 23      # Search
    CTRL_T = 20      # Go To Line
    CTRL_Z = 26      # Undo
    CTRL_Y = 25      # Redo

    # Clipboard (new in 0.0.2a01)
    CTRL_K = 11           # Cut line / selection
    CTRL_U = 21           # Paste
    ALT_A = alt(ord('a')) # Set / clear mark
    ALT_6 = alt(ord('6')) # Copy line / selection

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
