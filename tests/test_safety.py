"""
Regression tests for safety features (swap files and session restore).
"""

import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from femto.swap import get_swap_path, write_swap, read_swap, delete_swap
from femto.session import save_session, load_session, get_session_path


class TestSwapFiles(unittest.TestCase):
    def test_write_and_read_swap(self):
        with tempfile.TemporaryDirectory() as td:
            filepath = os.path.join(td, "test.txt")
            lines = ["hello", "world"]
            
            write_swap(filepath, lines, 5, 1)
            data = read_swap(filepath)
            
            self.assertIsNotNone(data)
            self.assertEqual(data['lines'], lines)
            self.assertEqual(data['x'], 5)
            self.assertEqual(data['y'], 1)
            
            delete_swap(filepath)
            self.assertIsNone(read_swap(filepath))

    def test_swap_path_is_unique(self):
        path1 = get_swap_path("/foo/bar.txt")
        path2 = get_swap_path("/foo/baz.txt")
        self.assertNotEqual(path1, path2)


class TestSessionRestore(unittest.TestCase):
    def test_save_and_load_session(self):
        # Mock document objects
        class MockBuffer:
            def __init__(self, fn, mod):
                self.filename = fn
                self.modified = mod
                
        class MockCursor:
            def __init__(self, x, y):
                self.x = x
                self.y = y
                
        class MockDoc:
            def __init__(self, fn, x, y, mod):
                self.buffer = MockBuffer(fn, mod)
                self.cursor = MockCursor(x, y)

        docs = [
            MockDoc("/a.txt", 1, 2, False),
            MockDoc("/b.txt", 5, 10, True)
        ]
        
        save_session(docs, 1)
        session = load_session()
        
        self.assertIsNotNone(session)
        self.assertEqual(session['current'], 1)
        self.assertEqual(len(session['buffers']), 2)
        self.assertEqual(session['buffers'][1]['filename'], "/b.txt")
        self.assertTrue(session['buffers'][1]['modified'])


if __name__ == "__main__":
    unittest.main()
