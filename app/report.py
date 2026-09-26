"""report.py — generate a self-contained HTML report.

HTML (instead of PDF) was chosen on purpose: it needs no extra libraries,
opens in any browser, and can be printed to PDF with "File > Print > Save
as PDF". The report is fully offline — no external fonts, scripts or images.
"""

from __future__ import annotations

import html
import os
import subprocess
import sys
from datetime import datetime

from .utils import APP_TITLE, APP_VERSION, REPORTS_DIR, ensure_dir, format_field

# (section, key, label) — the order used in the per-system tables
SYSTEM_ROWS = [
    ("system", "operating_system", "Operating System"),
    ("system", "version", "Version"),
    ("system", "build", "Build"),
    ("system", "architecture", "Architecture"),
    ("system", "machine", "Machine Type"),
    ("system", "hostname", "Hostname"),
]
CPU_ROWS = [
    ("cpu", "name", "Processor"),
    ("cpu", "cores", "Physical Cores"),
    ("cpu", "logical_processors", "Logical Processors"),
    ("cpu", "usage_percent", "CPU Usage (at capture)"),
]
MEMORY_ROWS = [
    ("memory", "total", "Total RAM"),
    ("memory", "used", "Used RAM"),
    ("memory", "available", "Available RAM"),
    ("memory", "usage_percent", "RAM Usage (at capture)"),
]
STORAGE_ROWS = [
    ("storage", "total", "Total Storage"),
    ("storage", "used", "Used Storage"),
    ("storage", "free", "Free Storage"),
    ("storage", "usage_percent", "Storage Usage (at capture)"),
]
NETWORK_ROWS = [
    ("network", "hostname", "Hostname"),
    ("network", "ip_address", "IP Address"),
]

STATUS_CLASS = {
    "SAME": "same",
    "DIFFERENT": "diff",
    "MISSING": "missing",
}

_CSS = """
body { font-family: 'Segoe UI', Arial, sans-serif; margin: 40px auto;
       max-width: 920px; color: #1f2430; line-height: 1.5; }
h1 { border-bottom: 3px solid #0d6efd; padding-bottom: 8px; }
h2 { margin-top: 32px; color: #0b5ed7; }
.meta { color: #6c757d; }
table { border-collapse: collapse; width: 100%; margin: 12px 0 24px; }
th, td { border: 1px solid #d6dbe4; padding: 8px 12px; text-align: left;
         font-size: 14px; }
th { background: #eef2f8; }
.sys td:first-child { width: 40%; background: #f7f9fc; font-weight: 600; }
tr.same td { background: #d4edda; }
tr.diff td { background: #fff3cd; }
tr.missing td { background: #f8d7da; }
.badge { font-weight: 700; }
ul { margin: 8px 0; }
.summary li { margin: 2px 0; }
.footer { margin-top: 40px; padding-top: 12px; border-top: 1px solid #d6dbe4;
          color: #6c757d; font-size: 12px; }
.cols { display: flex; gap: 24px; }
.cols > div { flex: 1; }
"""


def _system_table(config, title):
    """One <table> with all detected details of one system."""
    def block(rows):
        out = ["<table class='sys'>"]
        for section, key, label in rows:
            value = html.escape(format_field(config, section, key))
            out.append(f"<tr><td>{html.escape(label)}</td><td>{value}</td></tr>")
        out.append("</table>")
        return "".join(out)

    parts = [f"<h3>{html.escape(title)}</h3>"]
    parts.append("<div class='cols'>")
    parts.append(f"<div><h4>System</h4>{block(SYSTEM_ROWS)}</div>"
                 f"<div><h4>CPU</h4>{block(CPU_ROWS)}</div></div>")
    parts.append("<div class='cols'>")
    parts.append(f"<div><h4>Memory</h4>{block(MEMORY_ROWS)}</div>"
                 f"<div><h4>Storage</h4>{block(STORAGE_ROWS)}</div></div>")
    parts.append(f"<h4>Network</h4>{block(NETWORK_ROWS)}")
    parts.append("</div>")
    return "".join(parts)


def build_html(config_a, config_b, rows, summary):
    """Return the full HTML document as a string."""
    from .utils import get_path

    def title(cfg, fallback):
        name = get_path(cfg, ("system", "hostname")) or get_path(cfg, ("meta", "hostname"))
        return str(name) if name else fallback

    e = html.escape
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    h = []
    h.append("<!DOCTYPE html><html lang='en'><head><meta charset='utf-8'>")
    h.append(f"<title>{e(APP_TITLE)} — Comparison Report</title>")
    h.append(f"<style>{_CSS}</style></head><body>")
    h.append(f"<h1>{e(APP_TITLE)}</h1>")
    h.append(f"<p class='meta'>Report generated on {e(now)} • "
             f"Version {e(APP_VERSION)}</p>")

    # 1. system details
    h.append("<h2>1. System Information</h2>")
    h.append("<div class='cols'>")
    h.append(f"<div>{_system_table(config_a, 'System A: ' + title(config_a, 'Unnamed'))}</div>")
    h.append(f"<div>{_system_table(config_b, 'System B: ' + title(config_b, 'Unnamed'))}</div>")
    h.append("</div>")

    # 2. comparison table
    h.append("<h2>2. Comparison Table</h2>")
    h.append("<table><tr><th>Parameter</th><th>System A</th><th>System B</th>"
             "<th>Status</th></tr>")
    for row in rows:
        cls = STATUS_CLASS.get(row["status"], "")
        h.append(
            f"<tr class='{cls}'><td>{e(row['name'])}</td>"
            f"<td>{e(row['value_a'])}</td><td>{e(row['value_b'])}</td>"
            f"<td class='badge'>{e(row['status'])}</td></tr>"
        )
    h.append("</table>")

    # 3. detected differences
    h.append("<h2>3. Detected Differences</h2>")
    diffs = [row for row in rows if row["status"] != "SAME"]
    if diffs:
        h.append("<ul>")
        for row in diffs:
            h.append(f"<li><b>{e(row['name'])}:</b> {e(row['note'])}</li>")
        h.append("</ul>")
    else:
        h.append("<p>No differences detected — the two configurations are identical "
                 "for all compared parameters.</p>")

    # 4. summary
    h.append("<h2>4. Comparison Summary</h2>")
    h.append("<ul class='summary'>")
    for line in summary["lines"]:
        h.append(f"<li>{e(line)}</li>")
    h.append("</ul>")
    h.append(f"<p><b>Total differences: {summary['total_differences']}</b> "
             f"({summary['same']} same, {summary['different']} different, "
             f"{summary['missing']} not available out of {summary['total']} parameters)</p>")

    h.append("<p class='footer'>Generated by " + e(APP_TITLE) +
             " (academic project, LPU EDU-Revolution example). "
             "All data was processed locally on the user's computer; "
             "nothing was sent to any external server.</p>")
    h.append("</body></html>")
    return "".join(h)


def generate_html_report(config_a, config_b, rows, summary, output_path):
    """Write the HTML report and return the path that was written."""
    output_path = os.path.abspath(output_path)
    ensure_dir(os.path.dirname(output_path))
    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(build_html(config_a, config_b, rows, summary))
    return output_path


def open_report(path):
    """Best-effort: open the report in the default browser/viewer."""
    try:
        if sys.platform == "win32":
            os.startfile(path)  # type: ignore[attr-defined]
        elif sys.platform == "darwin":
            subprocess.Popen(["open", path])
        else:
            subprocess.Popen(["xdg-open", path])
    except Exception:
        pass  # opening is a convenience, never required
