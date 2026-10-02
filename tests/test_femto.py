from femto.clipboard import Clipboard, Selection   # add to imports


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
        self.assertEqual(self.buf.lines, ["hellosecond line", "third"])
        self.assertEqual((nx, ny), (5, 0))

    def test_bounds_clamped_after_shrink(self):
        self.sel.toggle(10, 2)
        self.buf.lines = ["ab"]          # buffer shrank (e.g. undo)
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
