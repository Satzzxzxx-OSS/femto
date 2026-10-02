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
|`Alt+A`|Set / clear mark|`Ctrl+K`|Cut line or selection|
|`Alt+6`|Copy line or selection|`Ctrl+U`|Paste clipboard|

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