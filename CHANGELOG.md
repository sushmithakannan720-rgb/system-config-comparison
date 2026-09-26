# Changelog

All notable changes to this project are documented here.

## [1.1.0] — 2026-09-22 · Production hardening

* **Background scanning** — the system scan now runs in a worker thread; the
  UI stays fully responsive (previously the window was busy for ~1–2 s).
* **Application logging** — every scan, save, load, comparison and report is
  logged to the console and to `logs/app.log`.
* **Global error handling** — an uncaught-exception hook logs the traceback
  and shows a dialog; the app keeps running instead of crashing.
* **Graceful startup** — `main.py` shows a clear "install dependencies"
  message when a package is missing, instead of a traceback.
* **Packaging** — `pyproject.toml` (installable package + console script),
  MIT `LICENSE`, this `CHANGELOG.md`.
* **One-click launchers** — `start.bat` (Windows) and `run.sh`
  (Linux/macOS) create a virtual environment, install dependencies and start
  the app automatically.
* **Hardened tests** — GUI smoke test stubs dialogs and waits for the async
  scan; a fresh-dependency install was verified end to end.

## [1.0.0] — 2026-09-21 · Initial release

* System scanner (OS, CPU, RAM, storage, network) with psutil + platform
* JSON configuration save / load with validation
* Comparison table (11 parameters) with SAME / DIFFERENT / MISSING states
* Factual difference analysis and auto-generated ✓/✗ summary
* Text-bar visualization for RAM and storage
* Self-contained HTML report generation
* CustomTkinter dashboard, details, compare and about pages with
  light/dark/System appearance modes
* Sample configurations, unit tests, core tests and a GUI smoke test
* README, viva question bank and screenshots
