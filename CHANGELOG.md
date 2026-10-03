# Changelog

All notable changes to Femto are documented in this file.

## [0.0.2rc1]

- Multi-buffer: `femto a b c`, Ctrl+F / Ctrl+L switcher, [i/n] indicator, per-buffer cursor/undo/selection/match (new documents.py)
- Exit flow saves all modified buffers, chaining Save-As prompts for unnamed ones
- Atomic saves (temp + fsync + os.replace) with  optional `name~` backups
- Performance: frame-signature skip, memoised wrap chunks and highlight spans; Buffer.revision invalidation
- All Alt bindings moved to Ctrl for terminal reliability (esp, Windows): Mark Ctrl+B, Copy Ctrl+P, Case Ctrl+O, Regex Ctrl+R, Lines Ctrl+N, Mouse Ctrl+D
- Alt decoding machinery retained for calibration but ships unbound
- Mouse support: wheel scrolling + click-to-cursor (Alt+M / --mouse / .femtorc)
- Click mapping is width-aware (CJK-safe) and soft-wrap aware
- Windows conhost fallbacks: raw CSI parser restores Shift+Tab (ESC[Z) and Ctrl+Arrow (ESC[1;5C/D) on legacy consoles (closes seeded Shift+Tab issue)
- Resize resilience: mouse reporting re-armed after terminal resize; pointer events ignored while prompts/confirmations are open
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