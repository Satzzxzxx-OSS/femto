"""
Entry point for Femto editor.

Usage:
    femto [file1 [file2 ...]]
    python -m femto [file1 [file2 ...]]
"""

import curses
import sys
from femto.app import Application


def main():
    initial_files = sys.argv[1:] if len(sys.argv) > 1 else []

    def run(stdscr):
        app = Application(stdscr, initial_files=initial_files)
        app.main_loop()

    try:
        curses.wrapper(run)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
