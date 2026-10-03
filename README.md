# Femto v0.0.2
     
Femto is a tiny, nano-style terminal text editor written in **pure Python**.
It ships with zero runtime dependencies on POSIX system (standard-library `curses` only) and automatically pulls `windows-curses` on Windows.

Femto supports multi-buffer editing, soft line wrapping, syntax highlighting, regex search & replace, mouse support, and is fully Unicode (CJK/Emoji) aware.

## Install

```bash
# From PyPI (Recommended)
pipx install femto-editor
# or
pip install femto-editor

# From source
git clone https://github.com/codewithzaqar/femto.git
cd femto
pip install .
```

After installation, the `femto` command is available globally.

## Usage
```bash
femto [file ...]        # open one or multiple files
femto --line-numbers a.py x.py
femto --tab-size 2 --regex x.py
femto --version
```

## Keybindings

|Key|Action|Key|Action|
|---|---|---|---|
|`Ctrl+X`|Exit (asks to save)|`Ctrl+W`|Search / find next|
|`Ctrl+S`|Save (Save-As if unnamed)|`Ctrl+T`|Go to line|
|`Ctrl+Z`/`Ctrl+Y`|Undo / Redo|`Ctrl+G`/`Esc`|Cancel prompt|
|`Arrows`|Move|`Ctrl+<-/->`|Word jump|
|`Home/End`, `Ctrl+A/E`|Line start/end|`PgUp/PgDn`|Page scroll|
|`Tab`/`Shift+Tab`|Indent / unindent|`Enter`|New line|
|`Ctrl+B`|Set / clear mark|`Ctrl+K`|Cut line or selection|
|`Ctrl+P`|Copy line or selection|`Ctrl+U`|Paste clipboard|
|`Ctrl+\`|Replace (search -> with -> Y/N/A/C)|`Ctrl+O`|Toggle case-insensitive (in search prompt)|
|`Ctrl+R`|Toggle regex mode (in search prompt)|||
|`Ctrl+N`|Toggle line numbers|||
|`Ctrl+D`|Toggle mouse support|Mouse wheel|Scroll viewport|
|`Ctrl+F` / `Ctrl+L`|Next / previous buffer|||
|`Mouse click`|Move cursor to click point|||

## Configuration (`~/.femtorc` or `./.femtorc`)

Femto is highly customizable via a simple `key = value` configuration file.

```ini
# Indentation
tab_size = 4

# Viewport
smooth_scroll_margin = 3
soft_wrap = true
show_line_numbers = false
syntax_highlight = true

# Search
ignore_case = false
regex_search = false

# Input & I/O
mouse = false
make_backup = false
# auto keeps the ending detected on load (LF for new files); lf or crlf forces it
line_ending = auto
final_newline = true  # ensure POSIX trailing newline
```

## Running the tests

Femto includes a comprehensive `unittest` regression suite that runs headlessely (no terminal required).

```bash
python -m unittest discover -s tests -v
```

## Building a release

```bash
pip install build twine
python -m build          # creates dist/femto_editor-0.0.1-*.whl
python -m twine upload dist/* # publish to PyPI
```

## License

MIT - see [LICENSE](LICENSE).