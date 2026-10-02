#!/usr/bin/env python3
"""
Convenience launcher kept for backwards compatibility.
Prefer:  python -m femto   or   femto   (after pip install).
"""

import sys
from femto.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
