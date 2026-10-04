"""Headless help tests, including the controller and bounded rendering."""

import ast
import copy
import curses
import inspect
from pathlib import Path
import textwrap
import unittest
from unittest.mock import Mock, patch

from femto.app import Application, Mode
from femto.help import (
    HelpView, KEYBINDINGS, help_lines, keybindings_markdown,
)
from femto.keys import Key, alt, is_backspace, is_enter
from femto.renderer import Renderer


def editor_state(app):
    """Snapshot editing state, excluding HELP mode and its scroll offset."""
    state = {
        "current": app.current, "message": app.message,
        "running": app.running, "prompt": vars(app.prompt),
        "clipboard": vars(app.clipboard), "config": vars(app.config),
        "search_options": vars(app.search_options),
        "pending_exit": app.pending_exit, "last_search": app.last_search,
        "replace": (app.replace_term, app.replace_with, app.replace_count),
        "prompt_base": app._prompt_base,
        "save_target": app.documents.index(app._save_target),
        "save_queue": [app.documents.index(d) for d in app._save_queue],
        "documents": [],
    }
    for doc in app.documents:
        buffer_state = dict(vars(doc.buffer))
        buffer_state.pop("config")
        state["documents"].append((
            buffer_state, vars(doc.cursor), vars(doc.selection),
            vars(doc.history), doc.last_match, doc.last_found_pos,
        ))
    return copy.deepcopy(state)


class TestHelpController(unittest.TestCase):
    def setUp(self):
        with patch("femto.config.Config.load"):
            self.app = Application([None, None])
        self.app.current = 1
        self.app.buffer.lines = ["alpha beta"] * 30
        self.app.handle_input(ord('!'), 20, 80)
        self.app.cursor.set_pos(5, 12, self.app.buffer.get_line_length, 29)
        self.app.cursor.scroll_y = 7
        self.app.selection.toggle(1, 10)
        self.app.clipboard.store("clipboard")
        self.app.last_match = (5, 12, 4)
        self.app.message = "Existing message"

    def test_f1_and_both_exit_keys_preserve_editor_state(self):
        for modified in (False, True):
            for close in (Key.ESCAPE, ord('q')):
                with self.subTest(modified=modified, close=close):
                    self.app.buffer.modified = modified
                    before = editor_state(self.app)
                    self.app.handle_input(Key.F1, 20, 80)
                    self.assertEqual(self.app.mode, Mode.HELP)
                    for key in (Key.ARROW_DOWN, Key.PAGE_DOWN, Key.END,
                                Key.ARROW_UP, Key.PAGE_UP, Key.HOME):
                        self.app.handle_input(key, 20, 80)
                        self.assertEqual(editor_state(self.app), before)
                    self.app.handle_input(close, 20, 80)
                    self.assertEqual(self.app.mode, Mode.NORMAL)
                    self.assertEqual(editor_state(self.app), before)

    def test_editing_commands_are_ignored_in_help(self):
        before = editor_state(self.app)
        self.app.handle_input(Key.F1, 5, 20)
        for key in (Key.CTRL_X, Key.CTRL_S, Key.CTRL_F, Key.CTRL_L,
                    Key.CTRL_K, Key.CTRL_U, Key.CTRL_B, Key.CTRL_N,
                    Key.CTRL_D, Key.CTRL_Z, Key.CTRL_Y, Key.CTRL_W,
                    Key.TAB, Key.DELETE, Key.ENTER[0], ord('y'), Key.F1,
                    Key.CTRL_G, Key.CTRL_BACKSLASH, Key.CTRL_O, Key.CTRL_R,
                    3, ord('Q')):
            offset = self.app.help_scroll_y
            self.app.handle_input(key, 5, 20)
            self.assertEqual(self.app.mode, Mode.HELP)
            self.assertEqual(self.app.help_scroll_y, offset)
            self.assertEqual(editor_state(self.app), before)
        with patch("femto.app.curses.getmouse") as getmouse:
            self.app._handle_mouse(None)
            getmouse.assert_not_called()

    def test_f1_is_ignored_in_every_prompt_and_confirmation(self):
        modes = (Mode.SAVE_AS, Mode.SEARCH, Mode.REPLACE_SEARCH,
                 Mode.REPLACE_WITH, Mode.REPLACE_CONFIRM, Mode.GOTO_LINE,
                 Mode.EXIT_CONFIRM)
        for mode in modes:
            with self.subTest(mode=mode):
                self.app.mode = mode
                self.app.prompt.start("Pending: ", "partially typed")
                self.app.prompt.cursor_pos = 3
                self.app.pending_exit = True
                self.app._save_queue = [self.app.doc]
                before = editor_state(self.app)
                self.app.handle_input(Key.F1, 20, 80)
                self.assertEqual(self.app.mode, mode)
                self.assertEqual(editor_state(self.app), before)

    def test_application_owns_scroll_and_reopening_resets_it(self):
        self.app.handle_input(Key.F1, 6, 40)
        self.app.handle_input(Key.PAGE_DOWN, 6, 40)
        self.assertEqual(self.app.help_scroll_y, 6)
        self.app.handle_input(Key.ARROW_DOWN, 6, 40)
        self.assertEqual(self.app.help_scroll_y, 7)
        self.app.handle_input(ord('q'), 6, 40)
        self.app.handle_input(Key.F1, 6, 40)
        self.assertEqual(self.app.help_scroll_y, 0)

    def test_interrupt_is_ignored_in_help(self):
        self.app.handle_input(Key.F1, 20, 80)
        with patch("femto.app.Renderer") as renderer, \
                patch("femto.app._ignore_suspend"), \
                patch.object(self.app, "_set_mouse"), \
                patch.object(self.app, "_read_key",
                             side_effect=(KeyboardInterrupt, Key.ESCAPE,
                                          KeyboardInterrupt)):
            renderer.return_value.get_dimensions.return_value = (20, 80)
            self.app.main_loop(Mock())
        self.assertEqual(self.app.mode, Mode.NORMAL)
        self.assertFalse(self.app.running)
        self.assertEqual(renderer.return_value.render.call_count, 3)

    def test_main_loop_does_not_update_document_scroll_in_help(self):
        self.app.handle_input(Key.F1, 20, 80)
        self.app.help_scroll_y = 10000
        before = editor_state(self.app)
        renderer = Mock()
        renderer.get_dimensions.side_effect = [(20, 80), (1, 1), (5, 15)]

        def read_key(stdscr):
            self.assertEqual(self.app.mode, Mode.HELP)
            self.assertEqual(editor_state(self.app), before)
            return next(keys)

        keys = iter((Key.RESIZE, Key.PAGE_DOWN, Key.CTRL_X))

        def handle_input(key, rows, cols):
            Application.handle_input(self.app, key, rows, cols)
            if key == Key.CTRL_X:
                self.app.running = False

        with patch("femto.app.Renderer", return_value=renderer), \
                patch("femto.app._ignore_suspend"), \
                patch.object(self.app, "_set_mouse"), \
                patch.object(self.app, "_read_key", side_effect=read_key), \
                patch.object(self.app, "handle_input",
                             side_effect=handle_input):
            self.app.main_loop(Mock())
        self.assertEqual(renderer.render.call_count, 3)
        for call in renderer.render.call_args_list:
            self.assertEqual(call.kwargs["mode"], Mode.HELP)
        for call, (rows, width) in zip(renderer.render.call_args_list,
                                      ((20, 80), (1, 1), (5, 15))):
            self.assertLessEqual(call.kwargs["help_scroll_y"],
                                 max(0, len(help_lines(width)) - rows))


class TestHelpInputReading(unittest.TestCase):
    def setUp(self):
        with patch("femto.config.Config.load"):
            self.app = Application()
        self.app.mode = Mode.HELP

    def test_bare_escape_has_bounded_waits_and_closes_help(self):
        screen = Mock()
        screen.getch.side_effect = (27, -1)
        with patch("femto.app.curses.get_escdelay", return_value=1000,
                   create=True), \
                patch("femto.app.curses.set_escdelay", create=True) as delay, \
                patch("femto.app.curses.halfdelay") as halfdelay:
            key = self.app._read_key(screen)
        self.assertEqual(key, Key.ESCAPE)
        short_delay = delay.call_args_list[0].args[0]
        self.assertLessEqual(short_delay, 100)
        self.assertEqual(delay.call_args_list[-1].args[0], 1000)
        self.assertLessEqual(screen.timeout.call_args_list[0].args[0], 100)
        screen.timeout.assert_called_with(-1)
        halfdelay.assert_not_called()
        self.app.handle_input(key, 20, 80)
        self.assertEqual(self.app.mode, Mode.NORMAL)

    def test_faster_user_delay_and_navigation_are_preserved(self):
        for code in (Key.ARROW_DOWN, Key.PAGE_DOWN, Key.F1):
            screen = Mock()
            screen.getch.return_value = code
            with patch("femto.app.curses.get_escdelay", return_value=25,
                       create=True), \
                    patch("femto.app.curses.set_escdelay",
                          create=True) as delay:
                self.assertEqual(self.app._read_key(screen), code)
            self.assertEqual(delay.call_args_list[0].args[0], 25)
            delay.assert_called_with(25)
            screen.timeout.assert_not_called()

    def test_alt_input_is_still_ignored_in_help(self):
        screen = Mock()
        screen.getch.side_effect = (27, ord('a'))
        with patch("femto.app.curses.get_escdelay", return_value=1000,
                   create=True), \
                patch("femto.app.curses.set_escdelay", create=True):
            key = self.app._read_key(screen)
        self.assertEqual(key, alt(ord('a')))
        self.app.handle_input(key, 20, 80)
        self.assertEqual(self.app.mode, Mode.HELP)
        self.assertEqual(self.app.buffer.lines, [""])

    def test_timeouts_are_restored_when_reading_is_interrupted(self):
        for reads in ((KeyboardInterrupt,), (27, KeyboardInterrupt)):
            screen = Mock()
            screen.getch.side_effect = reads
            with patch("femto.app.curses.get_escdelay", return_value=1000,
                       create=True), \
                    patch("femto.app.curses.set_escdelay",
                          create=True) as delay:
                with self.assertRaises(KeyboardInterrupt):
                    self.app._read_key(screen)
            delay.assert_called_with(1000)
            if len(reads) == 2:
                screen.timeout.assert_called_with(-1)

    def test_editing_and_prompt_escape_reading_remains_unchanged(self):
        for mode in (Mode.NORMAL, Mode.SEARCH):
            screen = Mock()
            screen.getch.side_effect = (27, -1)
            self.app.mode = mode
            with patch("femto.app.curses.set_escdelay",
                       create=True) as delay, \
                    patch("femto.app.curses.halfdelay") as halfdelay, \
                    patch("femto.app.curses.cbreak") as cbreak:
                self.assertEqual(self.app._read_key(screen), Key.ESCAPE)
            delay.assert_not_called()
            screen.timeout.assert_not_called()
            halfdelay.assert_called_once_with(2)
            cbreak.assert_called_once_with()

    def test_escape_works_without_python39_delay_apis(self):
        screen = Mock()
        screen.getch.side_effect = (27, -1)
        with patch("femto.app.curses.get_escdelay", None, create=True), \
                patch("femto.app.curses.set_escdelay", None, create=True):
            self.assertEqual(self.app._read_key(screen), Key.ESCAPE)
        screen.timeout.assert_called_with(-1)


class TestHelpContent(unittest.TestCase):
    def test_catalog_produces_categories_and_bindings(self):
        content = "\n".join(help_lines(160))
        self.assertIn("Ctrl+\\: Replace:", content)
        self.assertIn(
            "Search options (Search and Replace search prompts only)", content)
        self.assertIn("Replace confirmation", content)
        self.assertIn("Exit confirmation", content)
        self.assertIn("mouse enabled", content)
        self.assertIn("Help navigation (help only)", content)

    def test_help_and_markdown_use_catalog_changes(self):
        with patch.dict(KEYBINDINGS,
                        {"Extra context": (("Test key", "New action"),)}):
            self.assertIn("Test key: New action", "\n".join(help_lines(160)))
            self.assertIn("| `Test key` | New action |",
                          keybindings_markdown())

    def test_readme_tables_match_the_catalog(self):
        path = Path(__file__).resolve().parents[1] / "README.md"
        readme = path.read_text()
        start = "<!-- KEYBINDINGS:START -->\n"
        end = "\n<!-- KEYBINDINGS:END -->"
        tables = readme.split(start, 1)[1].split(end, 1)[0]
        self.assertEqual(tables, keybindings_markdown())


class TestHelpViewport(unittest.TestCase):
    def test_line_page_and_end_navigation_are_bounded(self):
        view = HelpView()
        view.move("up", 6, 40)
        self.assertEqual(view.offset, 0)
        view.move("down", 6, 40)
        self.assertEqual(view.offset, 1)
        view.move("page_down", 6, 40)
        self.assertEqual(view.offset, 7)
        view.move("page_up", 6, 40)
        self.assertEqual(view.offset, 1)
        view.move("end", 6, 40)
        last = view.render_rows(8, 40)
        self.assertIn("First / last help page", "\n".join(last))
        offset = view.offset
        view.move("down", 6, 40)
        self.assertEqual(view.offset, offset)
        view.move("home", 6, 40)
        self.assertEqual(view.offset, 0)

    def test_scrolling_reaches_all_content(self):
        view = HelpView()
        visited = []
        for _ in range(len(help_lines(40))):
            visited.extend(view.render_rows(5, 40)[1:-1])
            view.move("down", 3, 40)
        for line in help_lines(40):
            self.assertIn(line, visited)

    def test_resize_clamps_offset_and_rewraps(self):
        view = HelpView()
        view.move("end", 3, 12)
        self.assertGreater(view.offset, len(help_lines(80)))
        rows = view.render_rows(24, 80)
        self.assertEqual(len(rows), 24)
        self.assertEqual(view.offset, len(help_lines(80)) - 22)
        self.assertIn("First / last help page", "\n".join(rows))
        self.assertIn("q/Esc Close", rows[-1])
        self.assertTrue(all(len(row) <= 80 for row in rows))

    def test_tiny_and_empty_viewports(self):
        view = HelpView()
        for height in (0, 1, 2, 3, 6):
            for width in (0, 1, 2, 5, 15):
                with self.subTest(height=height, width=width):
                    rows = view.render_rows(height, width)
                    self.assertEqual(len(rows), height if width else 0)
                    self.assertTrue(all(len(row) <= width for row in rows))
                    if rows:
                        self.assertTrue(rows[-1].startswith("q"))

    def test_large_viewport_shows_all_bindings_without_scrolling(self):
        view = HelpView()
        view.move("end", 1000, 160)
        self.assertEqual(view.offset, 0)
        self.assertEqual(view.render_rows(1002, 160)[1:-1]
                         [:len(help_lines(160))], help_lines(160))


class StrictScreen:
    """Fail on any write beyond the measured terminal, not just curses."""

    def __init__(self, height, width):
        self.height, self.width = height, width
        self.writes = []
        self.erased = False

    def getmaxyx(self):
        return self.height, self.width

    def erase(self):
        self.erased = True
        self.writes.clear()

    def addstr(self, row, col, text, attr=0):
        assert self.erased, "The frame must be erased before help is drawn"
        assert 0 <= row < self.height
        assert 0 <= col < self.width
        assert len(text) <= self.width - col
        self.writes.append((row, col, text))

    def refresh(self):
        pass


class TestHelpRenderer(unittest.TestCase):
    def test_can_close_help_while_terminal_is_too_small_to_edit(self):
        with patch("femto.config.Config.load"):
            app = Application()
        app.config.show_line_numbers = True
        with patch.object(Renderer, "setup_colors"), \
                patch("femto.renderer.curses.curs_set"):
            for height, width in ((1, 1), (2, 2), (6, 1)):
                with self.subTest(height=height, width=width):
                    screen = StrictScreen(height, width)
                    renderer = Renderer(screen, app.config)
                    app.handle_input(Key.F1, 1, width)
                    renderer.render(app.buffer, app.cursor, mode=app.mode,
                                    help_scroll_y=app.help_scroll_y)
                    app.handle_input(ord('q'), 1, width)
                    renderer.render(app.buffer, app.cursor)
                    self.assertEqual(app.mode, Mode.NORMAL)
                    self.assertTrue(screen.writes[0][2].startswith("F"))
                    self.assertIsNone(renderer._last_sig)

    def test_draws_only_within_bounds_and_invalidates_editor_frame(self):
        screen = StrictScreen(24, 80)
        with patch.object(Renderer, "setup_colors"), \
                patch("femto.renderer.curses.curs_set") as curs_set:
            renderer = Renderer(screen, Mock())
            renderer.draw_text = Mock()
            for height, width in ((24, 80), (3, 10), (2, 2), (1, 1),
                                  (6, 15), (40, 100)):
                screen.height, screen.width = height, width
                renderer._last_sig = ("old editor frame",)
                renderer.render(Mock(), Mock(), mode=Mode.HELP)
                self.assertEqual(len(screen.writes), height)
                self.assertTrue(screen.writes[-1][2].startswith("q"))
                self.assertIsNone(renderer._last_sig)
                renderer.draw_text.assert_not_called()
            curs_set.assert_called_with(0)

    def test_handles_terminal_errors_and_restores_cursor_on_return(self):
        screen = Mock()
        screen.getmaxyx.return_value = (4, 20)
        screen.addstr.side_effect = curses.error
        screen.refresh.side_effect = curses.error
        with patch.object(Renderer, "setup_colors"), \
                patch("femto.renderer.curses.curs_set",
                      side_effect=curses.error):
            renderer = Renderer(screen, Mock())
            renderer.render(Mock(), Mock(), mode=Mode.HELP)
        with patch("femto.renderer.curses.curs_set") as curs_set:
            # Isolate text rendering: check the overlay-to-editor handoff.
            renderer.draw_text = Mock()
            renderer.draw_status_bar = Mock()
            renderer.draw_cursor = Mock()
            screen.refresh.side_effect = None
            with patch("femto.config.Config.load"):
                app = Application()
            renderer.render(app.buffer, app.cursor)
            curs_set.assert_called_with(1)
            renderer.draw_text.assert_called_once()


def documented_codes(category_prefix):
    """Decode displayed keys independently of controller Key constants."""
    special = {
        "F1": (curses.KEY_F1,), "Esc": (27,),
        "Arrows": (curses.KEY_UP, curses.KEY_DOWN,
                   curses.KEY_LEFT, curses.KEY_RIGHT),
        "Home": (curses.KEY_HOME,), "End": (curses.KEY_END,),
        "PgUp": (curses.KEY_PPAGE,), "PgDn": (curses.KEY_NPAGE,),
        "Tab": (9,), "Shift+Tab": (curses.KEY_BTAB,),
        "Backspace": (curses.KEY_BACKSPACE, 127),
        "Delete": (curses.KEY_DC,), "Enter": (curses.KEY_ENTER, 10, 13),
        "Ctrl+Left": (curses.KEY_SLEFT,),
        "Ctrl+Right": (curses.KEY_SRIGHT,),
        "Shift+Left": (curses.KEY_SLEFT,),
        "Shift+Right": (curses.KEY_SRIGHT,),
        "Left": (curses.KEY_LEFT,), "Right": (curses.KEY_RIGHT,),
        "Up": (curses.KEY_UP,), "Down": (curses.KEY_DOWN,),
    }
    result = {}
    for category, bindings in KEYBINDINGS.items():
        if not category.startswith(category_prefix):
            continue
        for label, _ in bindings:
            for token in label.split(" / "):
                if token in special:
                    result[token] = special[token]
                elif token.startswith("Ctrl+") and len(token) == 6:
                    result[token] = (ord(token[-1]) & 31,)
                elif len(token) == 1:
                    result[token] = tuple({ord(token), ord(token.lower())})
    return result


class TestDocumentedKeyBehavior(unittest.TestCase):
    """Exercise actual handlers with codes decoded from the help labels.

    Removing a documented entry, changing its displayed key, or changing
    its handler without updating the behavioral contract must fail a test.
    These checks do not attempt to prove arbitrary description semantics.
    """

    def make_app(self):
        with patch("femto.config.Config.load"):
            return Application([None, None, None])

    def test_normal_command_key_references_are_covered_by_the_catalog(self):
        documented = set()
        for prefix in ("Help (editing", "File", "Navigation", "Editing",
                       "Clipboard", "Search and", "View"):
            for codes in documented_codes(prefix).values():
                documented.update(codes)
        implemented = set()
        for handler in (Application.handle_input, Application._handle_normal,
                        is_backspace, is_enter):
            tree = ast.parse(textwrap.dedent(inspect.getsource(handler)))
            for node in ast.walk(tree):
                if (isinstance(node, ast.Attribute)
                        and isinstance(node.value, ast.Name)
                        and node.value.id == "Key"):
                    value = getattr(Key, node.attr)
                    implemented.update(value if isinstance(value, tuple)
                                       else (value,))
        self.assertFalse(implemented - documented,
                         f"Undocumented command codes: "
                         f"{implemented - documented}")

    def test_documented_commands_enter_the_expected_mode_or_toggle(self):
        cases = (
            ("Help (editing", "F1", "mode", Mode.HELP),
            ("File", "Ctrl+X", "running", False),
            ("File", "Ctrl+S", "mode", Mode.SAVE_AS),
            ("File", "Ctrl+F", "current", 1),
            ("File", "Ctrl+L", "current", 2),
            ("Navigation", "Ctrl+T", "mode", Mode.GOTO_LINE),
            ("Search and", "Ctrl+W", "mode", Mode.SEARCH),
            ("Search and", "Ctrl+\\", "mode", Mode.REPLACE_SEARCH),
            ("Clipboard", "Ctrl+B", "selection.active", True),
            ("View", "Ctrl+N", "config.show_line_numbers", True),
            ("View", "Ctrl+D", "config.mouse", True),
        )
        for category, token, field, expected in cases:
            for code in documented_codes(category)[token]:
                with self.subTest(key=token, code=code):
                    app = self.make_app()
                    with patch.object(app, "_set_mouse"):
                        app.handle_input(code, 10, 80)
                    value = app
                    for attribute in field.split('.'):
                        value = getattr(value, attribute)
                    self.assertEqual(value, expected)

    def test_documented_edits_and_clipboard_have_the_described_effect(self):
        cases = (
            ("Editing", "Tab", ["      alpha beta", "tail"], (6, 0)),
            ("Editing", "Shift+Tab", ["alpha beta", "tail"], (0, 0)),
            ("Editing", "Enter", ["  ", "alpha beta", "tail"], (0, 1)),
            ("Editing", "Backspace", [" alpha beta", "tail"], (1, 0)),
            ("Editing", "Ctrl+H", [" alpha beta", "tail"], (1, 0)),
            ("Editing", "Delete", ["  lpha beta", "tail"], (2, 0)),
            ("Clipboard", "Ctrl+K", ["tail"], (0, 0)),
            ("Clipboard", "Ctrl+P", ["  alpha beta", "tail"], (2, 0)),
            ("Clipboard", "Ctrl+U", ["  XYalpha beta", "tail"], (4, 0)),
            ("Editing", "Ctrl+Z", ["  alpha beta", "tail"], (2, 0)),
            ("Editing", "Ctrl+Y", ["  !alpha beta", "tail"], (3, 0)),
        )
        for category, token, lines, cursor in cases:
            for code in documented_codes(category)[token]:
                with self.subTest(key=token, code=code):
                    app = self.make_app()
                    app.buffer.lines = ["  alpha beta", "tail"]
                    app.cursor.x = 2
                    app.clipboard.store("XY")
                    if token in ("Ctrl+Z", "Ctrl+Y"):
                        app._snapshot()
                        app.buffer.insert_char(2, 0, "!")
                        app.cursor.x = 3
                        if token == "Ctrl+Y":
                            app._do_undo()
                    app.handle_input(code, 10, 80)
                    self.assertEqual(app.buffer.lines, lines)
                    self.assertEqual((app.cursor.x, app.cursor.y), cursor)
                    if token in ("Ctrl+K", "Ctrl+P"):
                        self.assertEqual(app.clipboard.text,
                                         "  alpha beta\n")

    def test_documented_navigation_moves_the_real_cursor(self):
        codes = documented_codes("Navigation")
        cases = (
            ("Home", (0, 20)), ("Ctrl+A", (0, 20)),
            ("End", (10, 20)), ("Ctrl+E", (10, 20)),
            ("Ctrl+Left", (0, 20)), ("Shift+Left", (0, 20)),
            ("Ctrl+Right", (6, 20)), ("Shift+Right", (6, 20)),
            ("PgUp", (5, 10)), ("PgDn", (5, 30)),
        )
        arrow_positions = ((5, 19), (5, 21), (4, 20), (6, 20))
        cases += tuple((code, position) for code, position
                       in zip(codes["Arrows"], arrow_positions))
        for token, position in cases:
            for code in ((token,) if isinstance(token, int) else codes[token]):
                with self.subTest(key=token):
                    app = self.make_app()
                    app.buffer.lines = ["alpha beta"] * 50
                    app.cursor.x, app.cursor.y = 5, 20
                    app.handle_input(code, 10, 80)
                    self.assertEqual((app.cursor.x, app.cursor.y), position)

    def test_documented_prompt_keys_and_search_options_use_their_context(self):
        codes = documented_codes("Prompts")
        cases = (("Left", "abcd", 1), ("Right", "abcd", 3),
                 ("Home", "abcd", 0), ("End", "abcd", 4),
                 ("Backspace", "acd", 1), ("Ctrl+H", "acd", 1),
                 ("Delete", "abd", 2))
        for token, text, cursor in cases:
            for code in codes[token]:
                app = self.make_app()
                app.mode = Mode.SEARCH
                app.prompt.start("Search: ", "abcd")
                app.prompt.cursor_pos = 2
                app.handle_input(code, 10, 80)
                self.assertEqual((app.prompt.text, app.prompt.cursor_pos),
                                 (text, cursor))
        for token in ("Esc", "Ctrl+G", "Enter"):
            for code in codes[token]:
                app = self.make_app()
                app.mode = Mode.SEARCH
                app.prompt.start("Search: ")
                app.handle_input(code, 10, 80)
                self.assertEqual(app.mode, Mode.NORMAL)
                self.assertFalse(app.prompt.active)
        for token, attribute in (("Ctrl+O", "ignore_case"),
                                 ("Ctrl+R", "regex")):
            code = documented_codes("Search options")[token][0]
            for mode in (Mode.SEARCH, Mode.REPLACE_SEARCH):
                app = self.make_app()
                app.mode = mode
                app.prompt.start("Search: ")
                app.handle_input(code, 10, 80)
                self.assertTrue(getattr(app.search_options, attribute))
            app = self.make_app()
            app.mode = Mode.REPLACE_WITH
            app.prompt.start("With: ")
            app.handle_input(code, 10, 80)
            self.assertFalse(getattr(app.search_options, attribute))

    def test_documented_help_keys_route_to_scroll_and_exit(self):
        codes = documented_codes("Help navigation")
        steps = (("Down", 11), ("Up", 9), ("PgDn", 16), ("PgUp", 4),
                 ("Home", 0), ("End", len(help_lines(40)) - 6))
        for token, offset in steps:
            app = self.make_app()
            app.mode = Mode.HELP
            app.help_scroll_y = 10
            app.handle_input(codes[token][0], 6, 40)
            self.assertEqual(app.help_scroll_y, offset)
            self.assertEqual(app.mode, Mode.HELP)
        for token in ("Esc", "q"):
            app = self.make_app()
            app.mode = Mode.HELP
            app.handle_input(codes[token][0], 6, 40)
            self.assertEqual(app.mode, Mode.NORMAL)

    def test_documented_confirmation_choices_reach_the_real_handlers(self):
        codes = documented_codes("Replace confirmation")
        for token in ("Y", "N", "A", "C", "Ctrl+G", "Esc"):
            for code in codes[token]:
                with self.subTest(context="replace", key=token, code=code):
                    app = self.make_app()
                    app.buffer.lines = ["cat cat"]
                    app.mode = Mode.REPLACE_CONFIRM
                    app.replace_term, app.replace_with = "cat", "dog"
                    app.last_match = (0, 0, 3)
                    app.handle_input(code, 10, 80)
                    expected = {"Y": "dog cat", "A": "dog dog"}
                    self.assertEqual(app.buffer.lines,
                                     [expected.get(token, "cat cat")])
                    if token in ("Y", "N"):
                        self.assertEqual(app.mode, Mode.REPLACE_CONFIRM)
                        self.assertEqual(app.last_match, (4, 0, 3))
                    else:
                        self.assertEqual(app.mode, Mode.NORMAL)
        codes = documented_codes("Exit confirmation")
        for token in ("Y", "N", "C", "Ctrl+G", "Esc"):
            for code in codes[token]:
                with self.subTest(context="exit", key=token, code=code):
                    app = self.make_app()
                    app.buffer.touch()
                    app.mode = Mode.EXIT_CONFIRM
                    app.handle_input(code, 10, 80)
                    if token == "Y":
                        self.assertEqual(app.mode, Mode.SAVE_AS)
                        self.assertTrue(app.pending_exit)
                        self.assertTrue(app.prompt.active)
                    elif token == "N":
                        self.assertFalse(app.running)
                    else:
                        self.assertEqual(app.mode, Mode.NORMAL)
                        self.assertTrue(app.running)

    def test_documented_mouse_actions_and_context(self):
        labels = [label for category, bindings in KEYBINDINGS.items()
                  if category.startswith("View") for label, _ in bindings]
        self.assertIn("Mouse click", labels)
        self.assertIn("Mouse wheel", labels)
        app = self.make_app()
        app.buffer.lines = ["alpha beta"] * 50
        app.cursor.x, app.cursor.y = 5, 20
        app.config.mouse = True
        app.renderer = Mock()
        app.renderer.get_dimensions.return_value = (22, 80)
        events = ((curses.BUTTON1_CLICKED, 4, 2, (4, 2)),
                  (curses.BUTTON4_PRESSED, 0, 0, (5, 17)))
        for button, x, y, position in events:
            app.cursor.x, app.cursor.y = 5, 20
            with patch("femto.app.curses.getmouse",
                       return_value=(0, x, y, 0, button)):
                app._handle_mouse(Mock())
            self.assertEqual((app.cursor.x, app.cursor.y), position)
        app.mode = Mode.HELP
        before = editor_state(app)
        with patch("femto.app.curses.getmouse") as getmouse:
            app._handle_mouse(Mock())
            getmouse.assert_not_called()
        self.assertEqual(editor_state(app), before)


if __name__ == "__main__":
    unittest.main()
