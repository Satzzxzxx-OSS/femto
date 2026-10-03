# Femto v0.0.1
     
Femto is a tiny, nano-style terminal text editor written in **pure Python**.
It ships with zero runtime dependencies on POSIX system (standard-library `curses` only) and automatically pulls `windows-curses` on Windows.

## Install

```bash
# From source
pip install .

# Or directly from the repository
pip install git+https://github.com/codewithzaqar/femto

# Developers: run without installing
python -m femto myfile.txt
```

After installation the `femto` command is available globally.

## Usage
```bash
femto [file]        # open or create a file
femto --tab=size 2 x.py # override tab width
femto --no-wrap long.log # horizontal scrolling instead of soft wrap
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
|Mouse click|Move cursor to click point|||

```bash
femto a.py b.py c.py  # open multiple buffers; [1/3] shown in status bar
```

`.femtorc`: `make_backup = true` keeps a `name~` backup on every save.

## Configuration (`~/.femtorc` or `./.femtorc`)

```ini
# comment
tab_size = 4
smooth_scroll_margin = 3
soft_wrap = true
```

## Running the tests

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