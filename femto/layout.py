"""
Pure visual-layout mathematics for Femto.

Contains NO curses import so it can be unit-tested on any platform,
including CI runners without a terminal.
"""


def line_row_count(line_len, width):
    """Number of visual rows occupied by a line of `line_len` chars."""
    if width < 1:
        width = 1
    return max(1, (line_len + width - 1) // width)


def chunk_line(line, width):
    """Split a line into visual chunks of at most `width` columns."""
    if not line:
        return [""]
    if width < 1:
        width = 1
    return [line[i:i + width] for i in range(0, len(line), width)]


def get_visual_position(x, y, lines, width, soft_wrap=True):
    """
    Map logical (x, y) to visual (vx, vy).

    With soft_wrap on, vy counts wrapped rows and vx is the column
    inside the wrapped row.  With soft_wrap off the mapping is the
    identity (horizontal scrolling handles overflow).
    """
    if not soft_wrap:
        return x, y

    vy = 0
    for i in range(y):
        vy += line_row_count(len(lines[i]), width)

    length = len(lines[y]) if 0 <= y < len(lines) else 0
    if length == 0:
        return 0, vy

    offset_rows = x // width
    vx = x % width

    # Cursor at the exact end of a full-width line sits at column 0
    # of the next visual row.
    if x == length and length % width == 0:
        offset_rows = length // width
        vx = 0

    return vx, vy + offset_rows


def get_logical_from_visual(target_vy, lines, width, soft_wrap=True):
    """Inverse of get_visual_position on the row axis."""
    if not soft_wrap:
        return target_vy

    vy = 0
    for y, line in enumerate(lines):
        rows = line_row_count(len(line), width)
        if vy + rows > target_vy:
            return y
        vy += rows
    return max(0, len(lines) - 1)
