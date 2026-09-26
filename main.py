"""main.py — entry point for the System Configuration Comparison Tool.

Run:
    python main.py          (any OS)
    start.bat               (Windows one-click)
    ./run.sh                (Linux / macOS)

Only local data is used; the application works fully offline.
"""

from __future__ import annotations

import sys


def _missing_dependency(exc: ImportError) -> None:
    print("=" * 62)
    print("  System Configuration Comparison Tool")
    print()
    print(f"  Missing Python dependency: {exc.name or 'unknown'}")
    print()
    print("  Install all dependencies with:")
    print("      pip install -r requirements.txt")
    print()
    print("  (On Windows you can simply double-click start.bat,")
    print("   which sets everything up automatically.)")
    print("=" * 62)


def main() -> None:
    try:
        from app.gui import run
    except ImportError as exc:
        _missing_dependency(exc)
        sys.exit(1)
    run()


if __name__ == "__main__":
    main()
