"""storage.py — save and load system configurations as JSON files.

JSON was chosen because it is:
    * human readable (easy to inspect in Notepad)
    * native in Python (json module, no extra packages)
    * easy to move between machines (plain text)

All files stay on the local computer — nothing is ever uploaded.
"""

from __future__ import annotations

import json
import os

from .utils import SAMPLE_DATA_DIR, ensure_dir


def save_config(config, path):
    """Write a configuration dict to a JSON file. Returns the path."""
    path = os.path.abspath(path)
    ensure_dir(os.path.dirname(path))
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(config, fh, indent=4, ensure_ascii=False)
    return path


def load_config(path):
    """Read and validate a configuration JSON file.

    Raises ValueError with a clear message when the file is not a valid
    configuration, so the GUI can show a friendly error instead of crashing.
    """
    try:
        with open(path, "r", encoding="utf-8") as fh:
            data = json.load(fh)
    except json.JSONDecodeError:
        raise ValueError(f"'{os.path.basename(path)}' is not a valid JSON file.")
    except OSError as exc:
        raise ValueError(f"Could not read file: {exc}")

    if not isinstance(data, dict):
        raise ValueError("The file does not contain a system configuration.")
    # at least one known section must be present
    known = ("system", "cpu", "memory", "storage", "network")
    if not any(section in data for section in known):
        raise ValueError("The file does not look like a system configuration "
                         "(no 'system'/'cpu'/'memory' section found).")
    return data


def config_name(config, fallback="Unnamed system"):
    """Friendly name for display: the hostname, or the fallback."""
    from .utils import get_path  # local import to avoid a cycle

    name = get_path(config, ("system", "hostname"))
    if name is None:
        name = get_path(config, ("meta", "hostname"))
    return str(name) if name else fallback


def empty_config():
    """A fully structured configuration with no values (all None).

    Useful for testing: comparing two empty configs must not crash.
    """
    return {
        "meta": {"tool": None, "app_version": None, "captured_at": None, "hostname": None},
        "system": {
            "operating_system": None, "version": None, "build": None,
            "architecture": None, "machine": None, "hostname": None,
        },
        "cpu": {"name": None, "cores": None, "logical_processors": None,
                "usage_percent": None},
        "memory": {"total": None, "used": None, "available": None,
                   "usage_percent": None},
        "storage": {"total": None, "used": None, "free": None,
                    "usage_percent": None},
        "network": {"hostname": None, "ip_address": None},
    }


def sample_paths():
    """Paths of the bundled demonstration files (data/sample/)."""
    return {
        "system_a": os.path.join(SAMPLE_DATA_DIR, "system_a.json"),
        "system_b": os.path.join(SAMPLE_DATA_DIR, "system_b.json"),
    }
