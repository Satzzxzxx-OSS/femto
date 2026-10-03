"""
Basic Python syntax highlighter using stdlib regex and keyword modules.
Uses a single regex with named groups to prevent overlapping matches.
"""

import re
import keyword

# Order matters: comments and strings first, then keywords/numbers
_TOKEN_RE = re.compile(
    r'(?P<COMMENT>\#.*)|'
    r'(?P<STRING>\"\"\".*?\"\"\"|\'\'\'.*?\'\'\'|\"[^\n\"\\]*(?:\\.[^\n\"\\]*)*\"|\'[^\n\'\\]*(?:\\.[^\n\'\\]*)*\')|'
    r'(?P<KEYWORD>\b(?:' + '|'.join(keyword.kwlist) + r')\b)|'
    r'(?P<NUMBER>\b\d+(?:\.\d+)?\b)'
)

# Map group names to color pair IDs (defined in renderer.py)
_COLOR_MAP = {
    'COMMENT': 3,   # Green
    'STRING': 4,    # Magenta
    'KEYWORD': 5,   # Cyan
    'NUMBER': 6,    # Yellow
}

def get_spans(line):
    """Returns a list of (start, end, color_pair_id) for the given line."""
    spans = []
    for m in _TOKEN_RE.finditer(line):
        for group, color_id in _COLOR_MAP.items():
            if m.group(group) is not None:
                spans.append((m.start(), m.end(), color_id))
                break
    return spans
