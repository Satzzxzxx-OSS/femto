"""Help content and viewport math, independent of curses.

Run ``python -m femto.help`` to generate the README keybinding tables.
"""

import textwrap


# Categories also state where their bindings apply. Keep descriptions here
# when adding commands, then regenerate the marked section in README.md.
# Behavioral tests decode these labels and exercise the real input handlers.
KEYBINDINGS = {
    "Help (editing only)": (
        ("F1", "Open read-only help; Esc or q returns to editing"),
    ),
    "Terminal (outside help)": (
        ("Ctrl+C", "Interrupt and exit without save confirmation"),
    ),
    "File and buffers (editing)": (
        ("Ctrl+X", "Exit; asks to save modified buffers"),
        ("Ctrl+S", "Save; Save As if unnamed"),
        ("Ctrl+F / Ctrl+L", "Next / previous buffer"),
    ),
    "Navigation (editing)": (
        ("Arrows", "Move cursor"),
        ("Ctrl+Left / Ctrl+Right", "Previous / next word"),
        ("Shift+Left / Shift+Right", "Previous / next word"),
        ("Home / Ctrl+A", "Line start"),
        ("End / Ctrl+E", "Line end"),
        ("PgUp / PgDn", "Move cursor one page up / down"),
        ("Ctrl+T", "Go to line"),
    ),
    "Editing": (
        ("Enter", "Insert newline"),
        ("Tab", "Insert indentation at cursor"),
        ("Shift+Tab", "Remove leading indentation from current line"),
        ("Backspace / Ctrl+H", "Delete before cursor; join at line start"),
        ("Delete", "Delete at cursor; join at line end"),
        ("Ctrl+Z / Ctrl+Y", "Undo / redo"),
    ),
    "Clipboard and selection (editing)": (
        ("Ctrl+B", "Set / clear selection mark; move cursor to select"),
        ("Ctrl+K", "Cut selection, or current line if selection is empty"),
        ("Ctrl+P", "Copy selection, or current line if selection is empty"),
        ("Ctrl+U", "Paste internal clipboard"),
    ),
    "Search and replace (editing)": (
        ("Ctrl+W", "Open search; Enter finds next (wraps at end of buffer)"),
        ("Ctrl+\\", "Replace: search term, replacement, then confirmation"),
    ),
    "View and mouse (editing)": (
        ("Ctrl+N", "Toggle line numbers"),
        ("Ctrl+D", "Toggle mouse support"),
        ("Mouse click", "Move cursor to clicked position (mouse enabled)"),
        ("Mouse wheel", "Move cursor three lines up / down (mouse enabled)"),
    ),
    "Prompts (Save As, Search, Replace, Go To Line)": (
        ("Enter", "Confirm current prompt"),
        ("Ctrl+G / Esc", "Cancel prompt"),
        ("Left / Right", "Move prompt cursor"),
        ("Home / End", "Start / end of prompt text"),
        ("Backspace / Ctrl+H", "Delete before prompt cursor"),
        ("Delete", "Delete at prompt cursor"),
    ),
    "Search options (Search and Replace search prompts only)": (
        ("Ctrl+O", "Toggle case-insensitive search"),
        ("Ctrl+R", "Toggle regular expressions"),
    ),
    "Replace confirmation": (
        ("Y / N / A", "Replace current match / skip match / replace all"),
        ("C / Ctrl+G / Esc", "Cancel remaining replacements"),
    ),
    "Exit confirmation": (
        ("Y / N", "Save modified buffers and exit / exit without saving"),
        ("C / Ctrl+G / Esc", "Cancel exit"),
    ),
    "Help navigation (help only)": (
        ("Esc / q", "Close help and return to editing"),
        ("Up / Down", "Scroll one help row"),
        ("PgUp / PgDn", "Scroll one help page"),
        ("Home / End", "First / last help page"),
    ),
}


def help_lines(width):
    """Wrap all categories and bindings to fit an ASCII help viewport."""
    lines = []
    for category, bindings in KEYBINDINGS.items():
        if lines:
            lines.append("")
        lines.extend(textwrap.wrap(category, max(1, width)))
        for keys, action in bindings:
            lines.extend(textwrap.wrap(f"  {keys}: {action}", max(1, width)))
    return lines


def keybindings_markdown():
    """Return the README tables from the same catalog as the help view."""
    lines = []
    for category, bindings in KEYBINDINGS.items():
        lines.extend((f"### {category}", "", "| Key | Action |",
                      "|---|---|"))
        lines.extend(f"| `{keys}` | {action} |" for keys, action in bindings)
        lines.append("")
    return "\n".join(lines).rstrip()


class HelpView:
    """Own only a help scroll offset; never reference an editor document."""

    def __init__(self, offset=0):
        self.offset = offset

    def move(self, action, rows, width):
        """Apply navigation and clamp against the current viewport size."""
        page = max(1, rows)
        limit = max(0, len(help_lines(width)) - page)
        steps = {"up": -1, "down": 1, "page_up": -page,
                 "page_down": page}
        if action == "home":
            self.offset = 0
        elif action == "end":
            self.offset = limit
        else:
            self.offset += steps.get(action, 0)
        self.offset = max(0, min(self.offset, limit))

    def render_rows(self, height, width):
        """Return bounded rows with a fixed exit hint, even at 1x1."""
        if height <= 0 or width <= 0:
            return []
        rows = max(0, height - 2)
        self.move(None, rows, width)
        lines = help_lines(width)
        visible = lines[self.offset:self.offset + rows]
        footer = ("q/Esc Close | Up/Down PgUp/PgDn Home/End | "
                  f"{self.offset + 1}-{self.offset + len(visible)}"
                  f"/{len(lines)}")
        if len(footer) > width:
            footer = "q/Esc Close | Up/Down PgUp/PgDn"
        if len(footer) > width:
            footer = "q/Esc Close"
        if height == 1:
            return [footer[:width]]
        title = "Femto Help - keybindings by context"
        return ([title[:width]] + visible + [""] * (rows - len(visible))
                + [footer[:width]])


if __name__ == "__main__":
    print(keybindings_markdown())
