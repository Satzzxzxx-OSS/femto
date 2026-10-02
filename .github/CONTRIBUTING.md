# Contributing to Femto

First off, thank you for considering contributing to Femto! 🚀

Femto is designed to be a tiny, zero-dependency (on POSIX) text editor. When contributing, please keep the "pure Python standard library" philosophy in mind.

## 🛠️ Development Setup

1. **Fork and clone** the repository.
2. **Create a virtual environment**:
```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate  # On Windows: .venv\Scripts\activate
```
3. **Install in editable mode**:
```bash
pip install -e.
```
*(Note: On Windows, this will automatically install `windows-curses`).*
4. **Run the test suite** to ensure everything is working:
```bash
python -m unittest discover -s tests -v
```

## 📝 Coding Standards

* **No external dependencies:** Core features must rely solely on the Python standard library.
* **PEP 8:** Follow standard Python formatting conventions.
* **Testability:** Keep curses-specific code isolated in `renderer.py` and `app.py`. Visual and buffer math should live in pure modules (like `layout.py` and `buffer.py`) so they can be unit-tested headlessly.
* **Type hints:** Encouraged but not strictly enforced for internal logic.

## 🚀 Pull Request Process

1. Create a new branch (`git checkout -b feature/amazing-feature`).
2. Make your changes and add tests if applicable.
3. Ensure the test suite passes (`python -m unittest discover -s tests -v`).
4. Commit your changes using a descriptive commit message (we like [Conventional Commits](https://www.conventionalcommits.org/)).
5. Push to your fork and open a Pull Request against the `main` branch of the upstream repo.

Thank you for helping make Femto better!