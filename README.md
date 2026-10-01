# Femto v0.0.1a01

Femto is a tiny, nano-style terminal text editor written in pure Python.
It relies solely on the Python standard library (`curses`) to provide a lightweight text editing experience directly in your terminal.

## Features (v0.0.1a01)
- Open, edit, and save text files
- Nano-style bottom status bar and help prompt
- Arrow key nabigation
- Basic text insertion and deletion (Backspace/Delete)
- Pure Python, no external dependencies

## Usage
```bash
python femto.py [filename]
```

## Controls
- `Ctrl+S`: Save
- `Ctrl+X`: Exit
- `Arrow Keys`: Move cursor
- `Backspace / Delete`: Remove characters