"""
Crash recovery via swap files (stdlib only).

Swap files are written to the system temp directory using a hash of the
absolute file path to arovid collisions.
"""

import os
import tempfile
import hashlib
import json


def get_swap_path(filepath):
    """Return the swap file for a given document."""
    abs_path = os.path.abspath(filepath)
    h = hashlib.md5(abs_path.encode('utf-8')).hexdigest()[:12]
    name = os.path.basename(filepath)
    return os.path.join(tempfile.gettempdir(), f".{name}.{h}.swp")
    
    
def write_swap(filepath, lines, cursor_x, cursor_y):
    """Write buffer state to the swap file."""
    path = get_swap_path(filepath)
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump({'lines': lines, 'x': cursor_x, 'y': cursor_y}, f)
    except Exception:
        pass
        
        
def read_swap(filepath):
    """Read buffer state from the swap file. Return None if missing/corrupt."""
    path = get_swap_path(filepath)
    if os.path.exists(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return None
    
    
def delete_swap(filepath):
    """Delete the swap file for given document."""
    path = get_swap_path(filepath)
    try:
        os.remove(path)
    except OSError:
        pass
