"""
Command-line entry point for Femto.

Enables:
    python -m femto [file]
    femto [file]            (console script installed by pip)
"""

import argparse
import sys

from femto import __version__, __app_name__
from femto.app import Application


def build_parser():
    parser = argparse.ArgumentParser(
        prog="femto",
        description="Femto - a tiny nano-style terminal text editor.",
    )
    parser.add_argument(
        "filename", nargs="?", default=None,
        help="file to open (created on save if it does not exist)",
    )
    parser.add_argument(
        "--version", action="version",
        version=f"{__app_name__} {__version__}",
    )
    parser.add_argument("--tab-size", type=int, default=None, metavar="N",
                        help="spaces inserted by Tab (overrides .femtorc)")
    parser.add_argument("--scroll-margin", type=int, default=None,
                        metavar="N",
                        help="smooth-scroll margin in rows")
    parser.add_argument("--no-wrap", action="store_true",
                        help="disable soft line wrapping")
    parser.add_argument("--ignore-case", action="store_true",
                        help="case-insensitive search by default")
    parser.add_argument("--regex", action="store_true",
                        help="treat search terms as regular expressions")
    parser.add_argument("--line-numbers", action="store_true",
                        help="show line number gutter")
    parser.add_argument("--no-highlight", action="store_true",
                        help="disable syntax highlighting")
    parser.add_argument("--mouse", action="store_true",
                        help="enable mouse wheel and click-to-cursor")
    parser.add_argument("--key-debug", action="store_true",
                        help="print raw key codes (for calibrating Alt keys)")
    return parser


def key_debug():
    """Show raw codes for every keypress - used to calibrate Alt maps."""
    import curses

    def _run(stdscr):
        stdscr.addstr(0, 0,
                      "Femto key debugger - press Alt combos, 'q' quits")
        row = 1
        stdscr.refresh()
        while True:
            k = stdscr.getch()
            if k in (ord('q'), 3):
                break
            try:
                name = curses.keyname(k).decode("ascii", "replace")
            except Exception:
                name = "?"
            hex_part = f"0x{k:X}" if k >= 0 else "neg"
            line = f"code={k:<6} hex={hex_part:<8} keyname={name}"
            stdscr.addstr(row % 22, 0, line.ljust(70))
            row += 1
            stdscr.refresh()

    curses.wrapper(_run)


def main(argv=None):
    args = build_parser().parse_args(argv)

    if args.key_debug:
        key_debug()
        return 0

    app = Application(args.filename)
    if args.tab_size is not None and args.tab_size >= 1:
        app.config.tab_size = args.tab_size
    if args.scroll_margin is not None and args.scroll_margin >= 0:
        app.config.smooth_scroll_margin = args.scroll_margin
    if args.no_wrap:
        app.config.soft_wrap = False
    if args.ignore_case:
        app.search_options.ignore_case = True
    if args.regex:
        app.search_options.regex = True
    if args.line_numbers:
        app.config.show_line_numbers = True
    if args.no_highlight:
        app.config.syntax_highlight = False
    if args.mouse:
        app.config.mouse = True

    app.run()
    return 0


if __name__ == "__main__":
    sys.exit(main())
