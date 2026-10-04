import unittest

from femto.layout import (
    char_width,
    chunk_line,
    get_logical_from_visual,
    get_visual_position,
    str_width,
)


class TestCharWidth(unittest.TestCase):
    def test_narrow_chars(self):
        self.assertEqual(char_width("a"), 1)
        self.assertEqual(char_width(" "), 1)

    def test_wide_chars(self):
        self.assertEqual(char_width("漢"), 2)
        self.assertEqual(char_width("Ａ"), 2)      # fullwidth latin
        self.assertEqual(char_width("🚀"), 2)      # emoji

    def test_str_width(self):
        self.assertEqual(str_width(""), 0)
        self.assertEqual(str_width("abc"), 3)
        self.assertEqual(str_width("漢字"), 4)
        self.assertEqual(str_width("a🚀b"), 4)
    
    def test_zwj_emoji_width(self):
        self.assertEqual(str_width("👨‍👩‍👧‍👦"), 2)   

class TestChunkLine(unittest.TestCase):
    def test_ascii_unchanged(self):
        self.assertEqual(chunk_line("abcdef", 3), ["abc", "def"])

    def test_empty_line(self):
        self.assertEqual(chunk_line("", 4), [""])

    def test_wide_char_never_split(self):
        self.assertEqual(chunk_line("ab漢c", 3), ["ab", "漢c"])
        self.assertEqual(chunk_line("漢c", 2), ["漢", "c"])
        self.assertEqual(chunk_line("漢漢漢", 4), ["漢漢", "漢"])

    def test_emoji_chunking(self):
        self.assertEqual(chunk_line("a🚀b", 2), ["a", "🚀", "b"])


class TestVisualPosition(unittest.TestCase):
    WIDTH = 4

    def test_ascii_regression(self):
        lines = ["abcdefg"]
        self.assertEqual(get_visual_position(4, 0, lines, 3), (1, 1))
        self.assertEqual(get_visual_position(0, 0, lines, 3), (0, 0))

    def test_empty_line(self):
        self.assertEqual(get_visual_position(0, 0, [""], self.WIDTH), (0, 0))

    def test_wide_chars_advance_two_columns(self):
        lines = ["漢字"]
        self.assertEqual(get_visual_position(1, 0, lines, self.WIDTH), (2, 0))
        # End of the line: 4 columns exactly fill one row, so the cursor
        # wraps to column 0 of the next visual row.
        self.assertEqual(get_visual_position(2, 0, lines, self.WIDTH), (0, 1))

    def test_cursor_at_end_of_full_width_line(self):
        self.assertEqual(get_visual_position(4, 0, ["abcd"], self.WIDTH), (0, 1))
        self.assertEqual(get_visual_position(2, 0, ["漢漢"], self.WIDTH), (0, 1))

    def test_cursor_at_end_of_partial_last_row(self):
        # "漢漢漢" is 6 columns wide in a 4-column row: rows 0-1.
        lines = ["漢漢漢"]
        self.assertEqual(get_visual_position(3, 0, lines, self.WIDTH), (2, 1))

    def test_row_count_uses_display_width(self):
        # "漢字漢字" spans 8 columns: two rows, not one.
        lines = ["漢字漢字", "ab"]
        self.assertEqual(get_visual_position(0, 1, lines, self.WIDTH), (0, 2))

    def test_hard_wrap_identity(self):
        lines = ["hello", "world"]
        self.assertEqual(
            get_visual_position(5, 1, lines, 3, soft_wrap=False),
            (5, 1),
        )

class TestLogicalFromVisual(unittest.TestCase):
    def test_ascii_regression(self):
        lines = ["abcdefg"]
        self.assertEqual(get_logical_from_visual(0, lines, 3), 0)
        self.assertEqual(get_logical_from_visual(2, lines, 3), 0)
        self.assertEqual(get_logical_from_visual(3, lines, 3), 0)

    def test_row_count_uses_display_width(self):
        lines = ["漢字漢字", "ab"]
        self.assertEqual(get_logical_from_visual(0, lines, 4), 0)
        self.assertEqual(get_logical_from_visual(1, lines, 4), 0)
        self.assertEqual(get_logical_from_visual(2, lines, 4), 1)

    def test_boundary_row_maps_to_starting_line(self):
        # A line that exactly fills its last row shares that visual row
        # with the next logical line; the inverse maps the row to the
        # line that starts on it.
        self.assertEqual(get_logical_from_visual(2, ["漢字漢字", "ab"], 4), 1)

    def test_roundtrip_from_end_of_wrapped_line(self):
        lines = ["漢字漢a", "ab"]  # 7 display columns: two rows, last one partial
        vx, vy = get_visual_position(4, 0, lines, 4)
        self.assertEqual((vx, vy), (3, 1))
        self.assertEqual(get_logical_from_visual(vy, lines, 4), 0)


if __name__ == "__main__":
    unittest.main()
