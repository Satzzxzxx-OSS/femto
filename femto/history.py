"""
Snapshot-based undo / redo history for Femto.

Every mutating edit pushes a deep-copy of the buffer lines and cursor
position onto the undo stack.  Undoing moves the current state to the
redo stack and restores the previous snapshot (and vice-versa).
"""

import copy


class History:
    """Fixed-size undo / redo stack."""

    def __init__(self, max_size=1000):
        self.undo_stack = []
        self.redo_stack = []
        self.max_size = max_size

    # ── public API ────────────────────────────────────────────

    def push(self, lines, x, y):
        """Record the state *before* an edit. Clears the redo stack."""
        self.undo_stack.append((copy.deepcopy(lines), x, y))
        if len(self.undo_stack) > self.max_size:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self, current_lines, current_x, current_y):
        """
        Undo the last edit.

        Returns (lines, x, y) to restore, or None if nothing to undo.
        """
        if not self.undo_stack:
            return None
        # stash current state so it can be redone later
        self.redo_stack.append(
            (copy.deepcopy(current_lines), current_x, current_y)
        )
        return self.undo_stack.pop()

    def redo(self, current_lines, current_x, current_y):
        """
        Redo the last undone edit.

        Returns (lines, x, y) to restore, or None if nothing to redo.
        """
        if not self.redo_stack:
            return None
        self.undo_stack.append(
            (copy.deepcopy(current_lines), current_x, current_y)
        )
        return self.redo_stack.pop()

    # ── helpers ───────────────────────────────────────────────

    @property
    def can_undo(self):
        return bool(self.undo_stack)

    @property
    def can_redo(self):
        return bool(self.redo_stack)
