"""
Basic Python syntax highlighter using stdlib regex and keyword modules.
Results are memoised per line content: redraws of unchanged lines cost
a dict lookup instead of a regex pass.
"""

import re
import keyword

_TOKEN_RE = re.compile(
    r'(?P<COMMENT>\#.*)|'
    r'(?P<STRING>\"\"\".*?\"\"\"|\'\'\'.*?\'\'\'|\"[^\n\"\\]*(?:\\.[^\n\"\\]*)*\"|\'[^\n\'\\]*(?:\\.[^\n\'\\]*)*\')|'
    r'(?P<KEYWORD>\b(?:' + '|'.join(keyword.kwlist) + r')\b)|'
    r'(?P<NUMBER>\b\d+(?:\.\d+)?\b)'
)

_COLOR_MAP = {
    'COMMENT': 3,
    'STRING': 4,
    'KEYWORD': 5,
    'NUMBER': 6,
}

_CACHE = {}
_CACHE_MAX = 4096


def get_spans(line):
    """Return [(start, end, color_pair_id)] for a line (memoised)."""
    hit = _CACHE.get(line)
    if hit is not None:
        return hit

    spans = []
    for m in _TOKEN_RE.finditer(line):
        for group, color_id in _COLOR_MAP.items():
            if m.group(group) is not None:
                spans.append((m.start(), m.end(), color_id))
                break

    if len(_CACHE) >= _CACHE_MAX:
        _CACHE.clear()
    _CACHE[line] = spans
    return spans
