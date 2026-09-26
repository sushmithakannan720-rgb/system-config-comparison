"""test_gui_smoke.py — GUI smoke test (requires a display / X server).

Starts the real application, then programmatically exercises every feature:
    navigation, scan, save, load, compare, difference detection, report.

Run (on a normal desktop):
    python tests/test_gui_smoke.py

Run headless (Linux, needs Xvfb):
    xvfb-run -a python tests/test_gui_smoke.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

ROOT = os.path.join(os.path.dirname(__file__), "..")
from app import report, storage, system_info  # noqa: E402
from app.gui import SystemConfigApp  # noqa: E402
from app.utils import LOGS_DIR, get_logger  # noqa: E402


def wait_for(app, condition, timeout=15):
    """Pump the Tk event loop until `condition()` is true (or timeout)."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        app.update()
        if condition():
            return True
        time.sleep(0.05)
    return False


def main():
    tmp = tempfile.mkdtemp(prefix="scct_smoke_")

    # never let a real dialog block the headless test run
    import tkinter.messagebox as mb
    dialogs = []
    mb.showerror = lambda *a, **k: dialogs.append(("error", a))
    mb.showinfo = lambda *a, **k: dialogs.append(("info", a))
    mb.askopenfilename = None  # not exercised here

    app = SystemConfigApp()
    app.update()

    # 1. navigate to every page without errors
    for page in ("dashboard", "details", "compare", "about"):
        app.show_page(page)
        app.update()
    print("PASS  navigation (dashboard/details/compare/about)")

    # 2. scan the current system (runs on a background thread)
    app.scan_system()
    assert wait_for(app, lambda: app.last_scan is not None or not app._scanning), \
        "scan did not finish in time"
    assert app.last_scan is not None, "scan produced no configuration"
    assert get_hostname(app.last_scan), "scan returned no hostname"
    print("PASS  scan current system (background thread)")

    # 3. save configuration A to JSON
    path_a = os.path.join(tmp, "system_a.json")
    storage.save_config(app.last_scan, path_a)
    assert json.load(open(path_a, encoding="utf-8")) == app.last_scan
    print("PASS  save configuration")

    # 4. load configuration B (bundled sample)
    path_b = os.path.join(ROOT, "data", "sample", "system_b.json")
    app._assign("A", app.last_scan)
    app._assign("B", storage.load_config(path_b))
    app.refresh_slot_labels()
    app.update()
    assert app.config_a is not None and app.config_b is not None
    print("PASS  load configuration")

    # 5. compare + difference detection
    app.compare()
    app.update()
    assert app.rows is not None and len(app.rows) >= 10
    assert any(r["status"] == "DIFFERENT" for r in app.rows)
    assert app.summary["total_differences"] >= 1
    print(f"PASS  comparison ({app.summary['total_differences']} differences detected)")

    # 6. report generation
    out = os.path.join(tmp, "report.html")
    report.generate_html_report(app.config_a, app.config_b, app.rows,
                                app.summary, out)
    size = os.path.getsize(out)
    assert size > 2000
    print(f"PASS  report generation ({size} bytes)")

    # 7. invalid JSON must not crash the GUI (error dialog suppressed here)
    bad = os.path.join(tmp, "bad.json")
    with open(bad, "w", encoding="utf-8") as fh:
        fh.write("not json")
    try:
        storage.load_config(bad)
        raise AssertionError("expected ValueError")
    except ValueError:
        pass
    print("PASS  invalid JSON handled")

    # 8. dark mode toggle
    app._toggle_appearance()
    app.update()
    print("PASS  appearance toggle")

    # 9. logging wrote to logs/app.log
    log_file = os.path.join(LOGS_DIR, "app.log")
    assert os.path.exists(log_file), "logs/app.log was not created"
    content = open(log_file, encoding="utf-8").read()
    assert "System scan complete" in content
    assert "Comparison done" in content
    get_logger().info("smoke test finished")
    print("PASS  application logging (logs/app.log)")

    # 10. no unexpected error dialogs appeared
    errors = [d for d in dialogs if d[0] == "error"]
    assert not errors, f"unexpected error dialog: {errors[0]}"
    print("PASS  no error dialogs appeared")

    app.destroy()
    print()
    print("GUI SMOKE TEST PASSED — all features exercised without crashes.")


def get_hostname(config):
    return (config.get("system") or {}).get("hostname") \
        or (config.get("meta") or {}).get("hostname")


if __name__ == "__main__":
    main()
