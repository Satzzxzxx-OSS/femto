"""
Configuration file parser for Femto.
Looks for ~/.femtorc or ./.femtorc
"""

import os

class Config:
    def __init__(self):
        self.tab_size = 4
        self.smooth_scroll_margin = 3
        self.soft_wrap = True
        self.load()

    def load(self):
        paths = [
            os.path.expanduser("~/.femtorc"),
            ".femtorc"
        ]
        for path in paths:
            if os.path.exists(path):
                self._parse(path)
                break

    def _parse(self, path):
        try:
            with open(path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    if "=" in line:
                        key, val = line.split("=", 1)
                        key = key.strip()
                        val = val.strip()
                        if key == "tab_size":
                            self.tab_size = max(1, int(val))
                        elif key == "smooth_scroll_margin":
                            self.smooth_scroll_margin = max(0, int(val))
                        elif key == "soft_wrap":
                            self.soft_wrap = val.lower() in ("true", "1", "yes")
        except Exception:
            pass
