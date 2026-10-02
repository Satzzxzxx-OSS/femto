#!/usr/bin/env python3
"""
Femto: A tiny nano-style terminal text editor in pure Python.
Entry point script.
"""

import sys
from femto.app import Application

def main():
    filename = sys.argv[1] if len(sys.argv) > 1 else None
    app = Application(filename)
    app.run()

if __name__ == "__main__":
    main()