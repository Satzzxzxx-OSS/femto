"""
Session restore and recent-files tracking (stdlib only).

Stores session state in XDG_CONFIG_HOME/femto/session.json.
"""

import os
import json


def get_session_path():
    """Return the path to the session file."""
    config_dir = os.environ.get('XDG_CONFIG_HOME', os.path.expanduser('~/.config'))
    femto_dir = os.path.join(config_dir, 'femto')
    os.makedirs(femto_dir, exist_ok=True)
    return os.path.join(femto_dir, 'session.json')
    
    
def save_session(documents, current_index):
    """Persist the current session state."""
    session = {
        'current': current_index,
        'buffers': []
    }
    for doc in documents:
        session['buffers'].append({
            'filename': doc.buffer.filename,
            'x': doc.cursor.x,
            'y': doc.cursor.y,
            'modified': doc.buffer.modified
        })
    try:
        with open(get_session_path(), 'w', encoding='utf-8') as f:
            json.dump(session, f)
    except Exception:
        pass
        
        
def load_session():
    """Load the previous session state. Returns None if missing/corrupt."""
    try:
        with open(get_session_path(), 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None
