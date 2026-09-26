"""test_comparison.py — unit tests for the comparison logic.

Covers the required test cases:
    1. identical configurations
    2. different RAM
    3. different storage
    4. different CPU
    5. different operating systems
    6. missing configuration value
    7. empty configuration

Run:
    python tests/test_comparison.py
"""

from __future__ import annotations

import copy
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app import comparison  # noqa: E402

GB = 1024 ** 3


def base_config():
    """A complete, valid configuration (System A baseline)."""
    return {
        "meta": {"hostname": "DESKTOP-1", "captured_at": "2026-09-21 10:00:00"},
        "system": {
            "operating_system": "Windows",
            "version": "11",
            "build": "10.0.22631",
            "architecture": "64-bit",
            "machine": "AMD64",
            "hostname": "DESKTOP-1",
        },
        "cpu": {
            "name": "Intel(R) Core(TM) i5-12400 CPU @ 2.50GHz",
            "cores": 6,
            "logical_processors": 12,
            "usage_percent": 20.0,
        },
        "memory": {
            "total": 8 * GB,
            "used": 3 * GB,
            "available": 5 * GB,
            "usage_percent": 37.5,
        },
        "storage": {
            "total": 512 * GB,
            "used": 250 * GB,
            "free": 262 * GB,
            "usage_percent": 48.8,
        },
        "network": {
            "hostname": "DESKTOP-1",
            "ip_address": "192.168.1.101",
        },
    }


def set_path(config, path, value):
    node = config
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value


def row(rows, key):
    for r in rows:
        if r["key"] == key:
            return r
    raise AssertionError(f"row '{key}' not found")


# ----------------------------------------------------------------- test cases

def test_identical_configs():
    a, b = base_config(), copy.deepcopy(base_config())
    rows = comparison.compare_configs(a, b)
    summary = comparison.summarize(rows)
    assert len(rows) >= 10
    assert all(r["status"] == "SAME" for r in rows)
    assert summary["total_differences"] == 0
    assert all(line.startswith("✓") for line in summary["lines"])


def test_different_ram():
    a, b = base_config(), copy.deepcopy(base_config())
    set_path(b, ("memory", "total"), 16 * GB)
    r = row(comparison.compare_configs(a, b), "ram_total")
    assert r["status"] == "DIFFERENT"
    assert r["note"] == "System B has 8 GB more RAM than System A."


def test_different_storage():
    a, b = base_config(), copy.deepcopy(base_config())
    set_path(b, ("storage", "total"), 1024 * GB)  # 1 TB
    r = row(comparison.compare_configs(a, b), "storage_total")
    assert r["status"] == "DIFFERENT"
    assert r["note"] == "System B has 512 GB more total storage than System A."


def test_different_cpu():
    a, b = base_config(), copy.deepcopy(base_config())
    set_path(b, ("cpu", "name"), "Intel(R) Core(TM) i7-9700 CPU @ 3.00GHz")
    r = row(comparison.compare_configs(a, b), "cpu_name")
    assert r["status"] == "DIFFERENT"
    assert r["note"] == "The processors are different."


def test_different_operating_systems():
    a, b = base_config(), copy.deepcopy(base_config())
    set_path(b, ("system", "operating_system"), "Linux")
    r = row(comparison.compare_configs(a, b), "operating_system")
    assert r["status"] == "DIFFERENT"
    assert r["note"] == "The operating systems are different."


def test_missing_value():
    a, b = base_config(), copy.deepcopy(base_config())
    set_path(b, ("cpu", "name"), "")          # empty string
    set_path(b, ("memory", "total"), None)    # explicit None
    rows = comparison.compare_configs(a, b)
    cpu = row(rows, "cpu_name")
    ram = row(rows, "ram_total")
    assert cpu["status"] == "MISSING" and "System B" in cpu["note"]
    assert ram["status"] == "MISSING" and "System B" in ram["note"]
    # summary must not crash and must mention the missing values
    summary = comparison.summarize(rows)
    assert summary["missing"] == 2


def test_empty_configuration():
    rows = comparison.compare_configs({}, {})
    summary = comparison.summarize(rows)
    assert len(rows) == len(comparison.COMPARE_PARAMS)
    assert all(r["status"] == "MISSING" for r in rows)
    assert summary["same"] == 0
    assert summary["total_differences"] == 0


# --------------------------------------------------------------------- runner

def main():
    tests = [
        ("1. identical configurations", test_identical_configs),
        ("2. different RAM", test_different_ram),
        ("3. different storage", test_different_storage),
        ("4. different CPU", test_different_cpu),
        ("5. different operating systems", test_different_operating_systems),
        ("6. missing configuration value", test_missing_value),
        ("7. empty configuration", test_empty_configuration),
    ]
    failures = 0
    for name, fn in tests:
        try:
            fn()
            print(f"PASS  {name}")
        except AssertionError as exc:
            failures += 1
            print(f"FAIL  {name}: {exc}")
    print()
    if failures:
        print(f"{failures}/{len(tests)} tests FAILED")
        sys.exit(1)
    print(f"All {len(tests)} comparison tests passed.")


if __name__ == "__main__":
    main()
