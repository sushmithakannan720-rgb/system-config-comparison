"""make_screenshots.py — capture PNG screenshots of the running app.

Requires:
    * a display (a normal desktop, or Xvfb:  Xvfb :99 &  DISPLAY=:99 ...)
    * ImageMagick's `import` command (Linux: apt install imagemagick)

Saves screenshots/01_dashboard.png, 02_details.png, 03_comparison.png.

Run:
    python tests/make_screenshots.py
"""

from __future__ import annotations

import os
import subprocess
import sys
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import storage  # noqa: E402
from app.gui import SystemConfigApp  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OUT = os.path.join(ROOT, "screenshots")


def grab(app, name):
    app.update_idletasks()
    app.update()
    time.sleep(0.4)  # let the widgets finish drawing
    path = os.path.join(OUT, name)
    subprocess.run(["import", "-window", str(app.winfo_id()), path], check=True)
    print("saved", path)


def wait_for_scan(app, timeout=20):
    deadline = time.time() + timeout
    while time.time() < deadline and app.last_scan is None:
        app.update()
        time.sleep(0.05)


def main():
    os.makedirs(OUT, exist_ok=True)
    app = SystemConfigApp()
    app.geometry("1150x720")
    app.update()

    # dashboard after a real scan (background thread -> wait for it)
    app.scan_system()
    wait_for_scan(app)
    assert app.last_scan is not None, "scan did not finish"
    app.show_page("dashboard")
    grab(app, "01_dashboard.png")

    # system details page
    app.show_page("details")
    grab(app, "02_details.png")

    # comparison with the two bundled sample systems
    app._assign("A", storage.load_config(
        os.path.join(ROOT, "data", "sample", "system_a.json")))
    app._assign("B", storage.load_config(
        os.path.join(ROOT, "data", "sample", "system_b.json")))
    app.refresh_slot_labels()
    app.compare()
    app.show_page("compare")
    grab(app, "03_comparison.png")

    app.destroy()
    print("done")


if __name__ == "__main__":
    main()
