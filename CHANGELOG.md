# Changelog

All notable changes to Femto are documented in this file.

## [0.0.2a03]
- Line number gutter (dynamic width, `Alt+N` toggle, `.femtorc` & CLI flags)
- Basic Python syntax highlighting (keywords, strings, comments, numbers)
- Overlay rendering engine (syntax < search match < selection priority)
- Full integration with width-aware layout match (PR #8)
- **Unicode Fix:** Width-aware layout math for CJK/emoji via `unicodedata` (Thanks @masterwusama!)
- Replace flow: Ctrl+\ (search -> replacement -> per-match Y/N/All/Cancel)
- Case-insensitive and regex search modes (Alt+C / Alt+R in prompts, .femtorc keys, --ignore-case / --regex CLI flags)
- New search.py engine (line-based, wrap control, zero-length-match safety)
- Live match highlighting (yellow) independent of selection highlight
- "Replaced N occurrence(s)" reporting
- Anchor-based selection: Alt+A sets/clears the mark, reverse-video highlight
- Cut (Ctrl+K), Copy (Alt+6), Paste (Ctrl+U) with nano line-fallback semantics
- New clipboard.py (Selection + Clipboard); typing replaces an active selection
- Alt-key input decoding (ESC-prefix and 8-bit meta); [Mark] status indicator

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