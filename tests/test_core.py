"""test_core.py — tests for scanning, storage and report generation.

Run:
    python tests/test_core.py
"""

from __future__ import annotations

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import comparison, report, storage, system_info  # noqa: E402

GB = 1024 ** 3
FAILURES = []


def check(name, fn):
    try:
        fn()
        print(f"PASS  {name}")
    except Exception as exc:  # noqa: BLE001 - report any failure
        FAILURES.append(name)
        print(f"FAIL  {name}: {exc!r}")


def test_scan_returns_all_sections():
    config = system_info.get_system_config()
    for section in ("meta", "system", "cpu", "memory", "storage", "network"):
        assert section in config, f"missing section '{section}'"
        assert isinstance(config[section], dict)
    # fields that must always exist (value may be None, key must not)
    for key in ("operating_system", "version", "architecture", "hostname"):
        assert key in config["system"]
    for key in ("name", "cores", "logical_processors"):
        assert key in config["cpu"]
    for key in ("total", "used", "available", "usage_percent"):
        assert key in config["memory"]
    for key in ("total", "used", "free", "usage_percent"):
        assert key in config["storage"]
    # byte fields, when available, are real numbers
    if config["memory"]["total"] is not None:
        assert config["memory"]["total"] > 0
        assert config["memory"]["used"] + config["memory"]["available"] \
            <= config["memory"]["total"] + GB  # allow rounding slack


def test_save_load_roundtrip():
    config = system_info.get_system_config()
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "system_test.json")
        storage.save_config(config, path)
        assert os.path.exists(path)
        loaded = storage.load_config(path)
        assert loaded == config
        # file is valid JSON readable by plain json too
        with open(path, encoding="utf-8") as fh:
            json.load(fh)


def test_load_invalid_file():
    with tempfile.TemporaryDirectory() as tmp:
        bad = os.path.join(tmp, "bad.json")
        with open(bad, "w", encoding="utf-8") as fh:
            fh.write("this is not json {")
        try:
            storage.load_config(bad)
            raise AssertionError("expected ValueError for invalid JSON")
        except ValueError:
            pass

        not_config = os.path.join(tmp, "notconfig.json")
        with open(not_config, "w", encoding="utf-8") as fh:
            json.dump({"foo": 1}, fh)
        try:
            storage.load_config(not_config)
            raise AssertionError("expected ValueError for non-configuration file")
        except ValueError:
            pass


def test_report_generation():
    a = system_info.get_system_config()
    b = storage.load_config(
        os.path.join(os.path.dirname(__file__), "..",
                     "data", "sample", "system_b.json"))
    rows = comparison.compare_configs(a, b)
    summary = comparison.summarize(rows)
    with tempfile.TemporaryDirectory() as tmp:
        path = report.generate_html_report(a, b, rows, summary,
                                           os.path.join(tmp, "out", "r.html"))
        assert os.path.exists(path)
        with open(path, encoding="utf-8") as fh:
            html_text = fh.read()
        assert "System Configuration Comparison Tool" in html_text
        assert "Comparison Table" in html_text
        assert "Comparison Summary" in html_text
        assert "Total differences:" in html_text
        assert "<html" in html_text and html_text.rstrip().endswith("</html>")


def test_empty_configs_do_not_crash():
    rows = comparison.compare_configs(storage.empty_config(), storage.empty_config())
    summary = comparison.summarize(rows)
    report_html = report.build_html(storage.empty_config(), storage.empty_config(),
                                    rows, summary)
    assert "Not available" in report_html
    assert summary["missing"] == len(rows)


def main():
    check("scan returns all sections", test_scan_returns_all_sections)
    check("save/load roundtrip", test_save_load_roundtrip)
    check("invalid file rejected cleanly", test_load_invalid_file)
    check("HTML report generation", test_report_generation)
    check("empty configs do not crash", test_empty_configs_do_not_crash)
    print()
    if FAILURES:
        print(f"{len(FAILURES)} core test(s) FAILED: {FAILURES}")
        sys.exit(1)
    print("All core tests passed.")


if __name__ == "__main__":
    main()
