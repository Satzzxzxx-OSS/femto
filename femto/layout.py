"""
Pure visual-layout mathematics for Femto.

Contains NO curses import so it can be unit-tested on any platform,
including CI runners without a terminal.

All columns are *display* columns: East Asian Wide and Fullwidth
characters (CJK, most emoji, ...) occupy two of them.
"""

import unicodedata


def char_width(ch):
    """Number of terminal columns used by a single character."""

    if unicodedata.combining(ch) or ch in ("\u200d", "\ufe0f"):
        return 0
    return 2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1


def _iter_graphemes(s):
    i = 0
    while i < len(s):
        start = i
        i += 1

        while i < len(s) and s[i] == "\ufe0f":
            i += 1

        while i < len(s) and s[i] == "\u200d":
            i += 1
            if i < len(s):
                i += 1
                while i < len(s) and s[i] == "\ufe0f":
                    i += 1

        yield start, i
        
def str_width(s):
    """Number of terminal columns a string occupies when displayed."""
    return sum(char_width(s[start]) for start, _ in _iter_graphemes(s))


def line_row_count(line_len, width):
    """Number of visual rows occupied by a line of `line_len` display columns."""
    if width < 1:
        width = 1
    return max(1, (line_len + width - 1) // width)


def chunk_line(line, width):
    """Split a line into visual chunks of at most `width` columns.

    Chunks are cut on display width, so a wide character is never
    split across two rows: it moves whole to the next chunk.
    """
    if not line:
        return [""]
    if width < 1:
        width = 1
    chunks = []
    start = 0
    cols = 0
    for i, _ in _iter_graphemes(line):
        w = char_width(line[i])
        if cols and cols + w > width:
            chunks.append(line[start:i])
            start = i
            cols = 0
        cols += w
    chunks.append(line[start:])
    return chunks


def get_visual_position(x, y, lines, width, soft_wrap=True):
    """
    Map logical (x, y) to visual (vx, vy).

    With soft_wrap on, vy counts wrapped rows and vx is the column
    inside the wrapped row.  With soft_wrap off the mapping is the
    identity (horizontal scrolling handles overflow).

    Columns are counted in display width, so a wide character
    advances the cursor by two columns.
    """
    if not soft_wrap:
        return x, y

    vy = 0
    for i in range(y):
        vy += line_row_count(str_width(lines[i]), width)

    line = lines[y] if 0 <= y < len(lines) else ""
    cols = str_width(line)
    if cols == 0:
        return 0, vy

    if x > len(line):
        x = len(line)
    offset_cols = str_width(line[:x])
    offset_rows = offset_cols // width
    vx = offset_cols % width

    # Cursor at the exact end of a full-width line sits at column 0
    # of the next visual row.
    if x == len(line) and cols % width == 0:
        offset_rows = cols // width
        vx = 0

    return vx, vy + offset_rows

def col_to_index(line, display_col):
    """Convert a display-column offset into a character index in `line`.

    A display column that falls inside a wide character maps to the
    start of the character.
    """
    col = 0
    for i, _ in _iter_graphemes(line):
        w = char_width(line[i])
        if display_col < col + w:
            return i
        col += w
    return len(line)


def get_logical_from_visual(target_vy, lines, width, soft_wrap=True):
    """Inverse of get_visual_position on the row axis."""
    if not soft_wrap:
        return target_vy

    vy = 0
    for y, line in enumerate(lines):
        rows = line_row_count(str_width(line), width)
        if vy + rows > target_vy:
            return y
        vy += rows
    return max(0, len(lines) - 1)

def get_logical_from_visual_point(target_vy, target_vx, lines, width,
                                  soft_wrap=True):
    """
    Map a visual (row, display-column) point to logical (x, y).

    Used by mouse click-to-cursor.  In hard-wrap mode the mapping is
    the identity (the caller has already added scroll offsets).
    """
    if not soft_wrap:
        return target_vx, target_vy

    vy = 0
    for y, line in enumerate(lines):
        chunks = chunk_line(line, width)
        rows = len(chunks)
        if vy + rows > target_vy:
            i = target_vy - vy
            offset = sum(str_width(c) for c in chunks[:i])
            return col_to_index(line, offset + target_vx), y
        vy += rows
    y = max(0, len(lines) - 1)
    return len(lines[y]), y
