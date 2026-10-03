# Changelog

All notable changes to Femto are documented in this file.

## [0.0.2] - Stable

- **Multi-buffer editing:** Open multiple files (`femto a b c`), switch with `Ctrl+F` / `Ctrl+L`.
- **Selection & Clipboard:** `Ctrl+B` (mark), `Ctrl+K` (cut), `Ctrl+P` (copy), `Ctrl+U` (paste).
- **Search & Replace:** `Ctrl+\` flow with per-match `Y/N/A/C` confirm. Regex and case-insensitive toggles (`Ctrl+R`, `Ctrl+O`).
- **Readability:** Dynamic line-number gutter (`Ctrl+N`), pure-Python syntax highlighting for `.py` files.
- **Mouse Support:** Wheel scrolling and click-to-cursor (`Ctrl+D` toggle).
- **Unicode Fidelity:** Width-aware layout math for CJK and Emoji characters (no more broken soft-wrap).
- **Platform Hardening:** Windows `Shift+Tab` / `Ctrl+Arrow` fallbacks, robust Alt/Ctrl key decoding.
- **Performance & Safety:** Atomic saves (`fsync` + `os.replace`), optional `name~` backups, frame-signature redraw skip, memoised syntax highlighting.

## [0.0.1] - Stable
- Packaging: `pyproject.toml`, console script `femto`, `python -m femto`
- CLI flags: `--version`, `--tab-size`, `--scroll-margin`, `--no-wrap`
- New `layout.py` (curses-free visual mapping) + unittest regression suite
- `soft_wrap = false` now works (horizontal-scroll fallback)
- Page Up/Down respect soft-wrapped visual rows
- Scroll clamping for very small terminals; ASCII-safe status messages
- MIT license, finalized README
- Visual soft line wrapping, smooth scrolling, `.femtorc` config parsing
- Search (Ctrl+W), Go-To-Line (Ctrl+T), snapshot Undo/Redo (Ctrl+Z / Ctrl+Y)
- Mode state machine, Save-As prompt, exit confirmation (Y/N/C)
- Word jump, Page Up/Down, Home/End, Tab / Shift-Tab indentation
- Initial alpha: load/save, arrows, insert/delete, nano-style status bar