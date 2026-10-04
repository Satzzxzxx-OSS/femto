"""
Regression test-suite for Femto (stdlib unittest, no curses required).

Run from the project root with either:
    python -m unittest discover -s tests -v
    python tests/test_femto.py
"""

import os
import sys
import tempfile
import unittest

# MUST run before any femto import: put the LOCAL source tree on sys.path
# so we never accidentally test a pip-installed copy.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from femto.buffer import Buffer, detect_newline, resolve_newline
from femto.clipboard import Clipboard, Selection
from femto.config import Config
from femto.cursor import Cursor
from femto.history import History
from femto.layout import col_to_index, get_logical_from_visual_point
from femto.layout import (
    chunk_line,
    get_logical_from_visual,
    get_visual_position,
    line_row_count,
)
from femto.search import SearchOptions, find_in_line, find_next, find_all
from femto.documents import Document


class TestBuffer(unittest.TestCase):
    def setUp(self):
        self.buf = Buffer(Config())

    def test_insert_and_delete(self):
        self.buf.insert_char(0, 0, "a")
        self.buf.insert_char(1, 0, "b")
        self.assertEqual(self.buf.lines[0], "ab")
        self.buf.delete_char(0, 0)
        self.assertEqual(self.buf.lines[0], "b")

    def test_backspace_merges_lines(self):
        self.buf.lines = ["foo", "bar"]
        x, y = self.buf.backspace(0, 1)
        self.assertEqual((x, y), (3, 0))
        self.assertEqual(self.buf.lines, ["foobar"])

    def test_tab_uses_config_size(self):
        cfg = Config()
        cfg.tab_size = 2
        buf = Buffer(cfg)
        new_x = buf.insert_tab(0, 0)
        self.assertEqual(new_x, 2)
        self.assertEqual(buf.lines[0], "  ")

    def test_word_navigation(self):
        self.buf.lines = ["hello world foo"]
        self.assertEqual(self.buf.get_next_word_pos(0, 0), 6)
        self.assertEqual(self.buf.get_prev_word_pos(0, 11), 6)

    def test_search_wraps(self):
        self.buf.lines = ["abc", "xxx", "abc"]
        self.assertEqual(self.buf.find_text("abc", 0, 0), (0, 0))
        self.assertEqual(self.buf.find_text("abc", 1, 0), (0, 2))

    def test_save_load_roundtrip(self):
        with tempfile.NamedTemporaryFile("w", suffix=".txt",
                                         delete=False) as fh:
            path = fh.name
        try:
            self.buf.lines = ["one", "two"]
            self.buf.filename = path
            self.assertTrue(self.buf.save())
            other = Buffer(Config())
            other.load_file(path)
            self.assertEqual(other.lines, ["one", "two"])
        finally:
            os.unlink(path)


class TestHistory(unittest.TestCase):
    def test_undo_redo(self):
        h = History()
        h.push(["a"], 1, 0)
        lines, x, y = h.undo(["ab"], 2, 0)
        self.assertEqual((lines, x, y), (["a"], 1, 0))
        lines, x, y = h.redo(["a"], 1, 0)
        self.assertEqual((lines, x, y), (["ab"], 2, 0))

    def test_new_edit_clears_redo(self):
        h = History()
        h.push(["a"], 1, 0)
        h.undo(["ab"], 2, 0)
        h.push(["a"], 1, 0)
        self.assertFalse(h.can_redo)


class TestLayout(unittest.TestCase):
    def test_row_count(self):
        self.assertEqual(line_row_count(0, 10), 1)
        self.assertEqual(line_row_count(10, 10), 1)
        self.assertEqual(line_row_count(11, 10), 2)

    def test_visual_position_wrap(self):
        lines = ["0123456789ABCDE"]
        vx, vy = get_visual_position(12, 0, lines, 10)
        self.assertEqual((vx, vy), (2, 1))

    def test_visual_position_line_end_wrap(self):
        lines = ["0123456789"]
        vx, vy = get_visual_position(10, 0, lines, 10)
        self.assertEqual((vx, vy), (0, 1))

    def test_logical_from_visual_roundtrip(self):
        lines = ["0123456789ABCDE", "short", ""]
        for y in range(len(lines)):
            vx, vy = get_visual_position(0, y, lines, 10)
            self.assertEqual(get_logical_from_visual(vy, lines, 10), y)

    def test_chunk_line(self):
        self.assertEqual(chunk_line("", 5), [""])
        self.assertEqual(chunk_line("abcdefg", 3), ["abc", "def", "g"])


class TestCursorScroll(unittest.TestCase):
    def test_smooth_scroll_clamps(self):
        c = Cursor()
        c.update_scroll(0, 0, 20, 80, 3)
        self.assertEqual(c.scroll_y, 0)
        c.update_scroll(50, 0, 20, 80, 3)
        self.assertGreater(c.scroll_y, 0)
        self.assertLessEqual(50, c.scroll_y + 20 - 1)

    def test_hard_wrap_horizontal(self):
        c = Cursor()
        c.update_scroll(0, 100, 20, 80, 3, soft_wrap=False)
        self.assertGreater(c.scroll_x, 0)
        self.assertLessEqual(100, c.scroll_x + 80 - 1)


class TestConfig(unittest.TestCase):
    def test_parse(self):
        with tempfile.NamedTemporaryFile("w", suffix="rc",
                                         delete=False) as fh:
            fh.write("# comment\ntab_size = 8\nsoft_wrap = false\n")
            path = fh.name
        try:
            cfg = Config()
            cfg._parse(path)
            self.assertEqual(cfg.tab_size, 8)
            self.assertFalse(cfg.soft_wrap)
        finally:
            os.unlink(path)


class TestSelectionClipboard(unittest.TestCase):
    def setUp(self):
        self.buf = Buffer(Config())
        self.buf.lines = ["hello world", "second line", "third"]
        self.sel = Selection()
        self.clip = Clipboard()

    def test_extract_multiline(self):
        self.sel.toggle(5, 0)
        bounds = self.sel.bounds(self.buf, 6, 1)
        self.assertEqual(self.sel.extract(self.buf, bounds),
                         " world\nsecond")

    def test_delete_range(self):
        self.sel.toggle(5, 0)
        bounds = self.sel.bounds(self.buf, 6, 1)
        nx, ny = self.sel.delete_range(self.buf, bounds)
        self.assertEqual(self.buf.lines, ["hello line", "third"])
        self.assertEqual((nx, ny), (5, 0))

    def test_bounds_clamped_after_shrink(self):
        self.sel.toggle(10, 2)
        self.buf.lines = ["ab"]          # buffer shrank (e.g. after undo)
        bounds = self.sel.bounds(self.buf, 0, 0)
        self.assertEqual(bounds, ((0, 0), (2, 0)))

    def test_paste_single_line(self):
        self.clip.store("AB")
        x, y = self.clip.paste_into(self.buf, 5, 0)
        self.assertEqual(self.buf.lines[0], "helloAB world")
        self.assertEqual((x, y), (7, 0))

    def test_paste_multiline(self):
        self.clip.store("L1\nL2")
        x, y = self.clip.paste_into(self.buf, 0, 2)
        self.assertEqual(self.buf.lines[2:4], ["L1", "L2third"])
        self.assertEqual((x, y), (2, 3))


class TestSearch(unittest.TestCase):
    def setUp(self):
        self.buf = Buffer(Config())
        self.buf.lines = ["Hello WORLD", "world peace", "wrap up"]

    def test_plain_case_sensitive(self):
        self.assertEqual(find_next(self.buf, "world", SearchOptions(), 0, 0),
                         (0, 1, 5))

    def test_ignore_case(self):
        opt = SearchOptions(ignore_case=True)
        self.assertEqual(find_next(self.buf, "world", opt, 0, 0), (6, 0, 5))
    def test_find_all(self):
        opt = SearchOptions(ignore_case=True)
        self.assertEqual(
            find_all(self.buf, "world", opt),
            [(6, 0, 5), (0, 1, 5)]
        )
    def test_regex(self):
        opt = SearchOptions(regex=True)
        self.assertEqual(find_next(self.buf, r"w.rld", opt, 0, 0), (0, 1, 5))

    def test_invalid_regex_returns_none(self):
        self.assertIsNone(find_in_line("abc", "(", SearchOptions(regex=True)))

    def test_no_wrap_stops_at_eof(self):
        self.assertIsNone(
            find_next(self.buf, "Hello", SearchOptions(), 0, 1, wrap=False))

    def test_zero_length_regex_match(self):
        self.assertEqual(
            find_in_line("abc", "x*", SearchOptions(regex=True), 0), (0, 0))

    def test_flag_label(self):
        self.assertEqual(SearchOptions(True, True).flag_label(), " [ir]")
        self.assertEqual(SearchOptions().flag_label(), "")


class TestMouseMapping(unittest.TestCase):
    def test_col_to_index_ascii(self):
        self.assertEqual(col_to_index("hello", 3), 3)
        self.assertEqual(col_to_index("hello", 99), 5)

    def test_col_to_index_wide(self):
        # Each CJK char occupies 2 display columns
        self.assertEqual(col_to_index("漢字", 0), 0)
        self.assertEqual(col_to_index("漢字", 2), 1)
        self.assertEqual(col_to_index("漢字", 3), 1)   # mid-char clamps left

    def test_visual_point_roundtrip(self):
        lines = ["0123456789ABCDE"]
        x, y = get_logical_from_visual_point(1, 2, lines, 10)
        self.assertEqual((x, y), (12, 0))

    def test_visual_point_beyond_eof(self):
        x, y = get_logical_from_visual_point(99, 99, ["ab", "cd"], 80)
        self.assertEqual((x, y), (2, 1))

    def test_visual_point_hard_wrap_identity(self):
        self.assertEqual(
            get_logical_from_visual_point(4, 7, ["ab"], 80, soft_wrap=False),
            (7, 4))

class TestMultiBuffer(unittest.TestCase):
    def test_documents_isolated(self):
        cfg = Config()
        d1 = Document(cfg)
        d2 = Document(cfg)
        d1.buffer.insert_char(0, 0, "x")
        d1.cursor.x = 1
        d1.history.push(["x"], 1, 0)
        self.assertEqual(d2.buffer.lines, [""])
        self.assertEqual(d2.cursor.x, 0)
        self.assertFalse(d2.history.can_undo)

    def test_atomic_save_and_backup(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "out.txt")
            cfg = Config()
            cfg.make_backup = True
            d = Document(cfg, path)
            d.buffer.lines = ["one"]
            self.assertTrue(d.buffer.save())
            d.buffer.lines = ["two"]
            self.assertTrue(d.buffer.save())
            with open(path) as f:
                self.assertEqual(f.read(), "two")
            with open(path + "~") as f:
                self.assertEqual(f.read(), "one")
            self.assertFalse(os.path.exists(path + ".femto-tmp"))

    def test_crlf_roundtrip_preserves_endings(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "note.txt")
            original = "hello\r\nworld\r\n"
            with open(path, "wb") as fh:
                fh.write(original.encode("utf-8"))
            cfg = Config()
            buf = Buffer(cfg)
            buf.load_file(path)
            self.assertEqual(buf.lines, ["hello", "world"])
            self.assertEqual(buf.newline, "\r\n")
            self.assertTrue(buf.ends_with_newline)
            buf.lines[0] = "hello!"
            self.assertTrue(buf.save())
            with open(path, "rb") as fh:
                self.assertEqual(fh.read(), b"hello!\r\nworld\r\n")

    def test_line_ending_config_overrides_detected(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "note.txt")
            with open(path, "wb") as fh:
                fh.write(b"hello\r\nworld\r\n")
            cfg = Config()
            cfg.line_ending = "lf"
            buf = Buffer(cfg)
            buf.load_file(path)
            self.assertTrue(buf.save())
            with open(path, "rb") as fh:
                self.assertEqual(fh.read(), b"hello\nworld\n")

    def test_detect_and_resolve_newline(self):
        self.assertEqual(detect_newline("a\r\nb\r\n"), "\r\n")
        self.assertEqual(detect_newline("a\nb\n"), "\n")
        self.assertEqual(detect_newline("a\r\nb\nc\n"), "\n")
        self.assertEqual(resolve_newline("auto", "\r\n"), "\r\n")
        self.assertEqual(resolve_newline("lf", "\r\n"), "\n")
        self.assertEqual(resolve_newline("crlf", "\n"), "\r\n")
        self.assertEqual(resolve_newline("nope", "\r\n"), "\r\n")

    def test_revision_bumps_on_edit(self):
        d = Document(Config())
        r0 = d.buffer.revision
        d.buffer.insert_char(0, 0, "a")
        self.assertEqual(d.buffer.revision, r0 + 1)

    def test_highlight_cache_stable(self):
        from femto.highlight import get_spans
        self.assertEqual(get_spans("def f(): pass"),
                         get_spans("def f(): pass"))

if __name__ == "__main__":
    unittest.main()
