"""utils.py — small shared helpers: constants, formatting, paths.

Kept free of GUI and psutil imports so every other module (and the tests)
can use it without side effects.
"""

from __future__ import annotations

import logging
import os

# ---------------------------------------------------------------- constants

APP_TITLE = "System Configuration Comparison Tool"
APP_VERSION = "1.1"
NOT_AVAILABLE = "Not available"

# project folders (project root = parent of the app/ package)
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLE_DATA_DIR = os.path.join(PROJECT_ROOT, "data", "sample")
REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")
LOGS_DIR = os.path.join(PROJECT_ROOT, "logs")


# --------------------------------------------------------------- logging

_log_configured = False


def get_logger(name: str = "scct") -> logging.Logger:
    """Return the shared application logger.

    Logs to the console AND to logs/app.log (UTF-8, one line per event).
    Configuration happens once; all modules call this to get the same logger.
    """
    global _log_configured
    logger = logging.getLogger(name)
    if _log_configured:
        return logger

    logger.setLevel(logging.INFO)
    logger.propagate = False
    formatter = logging.Formatter(
        "%(asctime)s  %(levelname)-7s  %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)
    try:
        ensure_dir(LOGS_DIR)
        file_handler = logging.FileHandler(
            os.path.join(LOGS_DIR, "app.log"), encoding="utf-8"
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    except OSError:
        pass  # logging to file is a convenience, never fatal
    _log_configured = True
    return logger


# ------------------------------------------------------------------ helpers

def get_path(config, path):
    """Safely read config[section][key]; returns None if anything is missing.

    This is what makes the app crash-proof: a missing section or key simply
    yields None, which the UI displays as "Not available".
    """
    value = config
    for key in path:
        if not isinstance(value, dict):
            return None
        value = value.get(key)
    return value


def clean_value(value):
    """Return a non-empty string for a raw value, or None if it is empty."""
    if value is None:
        return None
    text = str(value).strip()
    return text if text else None


def ensure_dir(path):
    """Create a folder (and parents) if it does not exist yet."""
    os.makedirs(path, exist_ok=True)
    return path


def bytes_to_str(value, default=NOT_AVAILABLE):
    """Convert a byte count to a human string: 8589934592 -> '8 GB'."""
    try:
        number = float(value)
    except (TypeError, ValueError):
        return default
    for unit in ("B", "KB", "MB", "GB", "TB", "PB"):
        if abs(number) < 1024 or unit == "PB":
            if unit == "B":
                return f"{int(number)} {unit}"
            text = f"{number:.1f}".rstrip("0").rstrip(".")
            return f"{text} {unit}"
        number /= 1024
    return default  # pragma: no cover


def percent_str(value, default=NOT_AVAILABLE):
    """25.0 -> '25.0%'"""
    try:
        return f"{float(value):.1f}%"
    except (TypeError, ValueError):
        return default


def format_field(config, section, key, default=NOT_AVAILABLE):
    """Format one configuration field for display, never raising."""
    raw = get_path(config, (section, key))
    if raw is None:
        return default
    kind = FIELD_FORMATS.get((section, key), "text")
    if kind == "bytes":
        return bytes_to_str(raw, default)
    if kind == "percent":
        return percent_str(raw, default)
    if kind == "number":
        try:
            return str(int(float(raw)))
        except (TypeError, ValueError):
            return str(raw)
    text = str(raw).strip()
    return text or default


# (section, key) pairs that hold raw byte counts / percents / numbers
FIELD_FORMATS = {
    ("memory", "total"): "bytes",
    ("memory", "used"): "bytes",
    ("memory", "available"): "bytes",
    ("memory", "usage_percent"): "percent",
    ("storage", "total"): "bytes",
    ("storage", "used"): "bytes",
    ("storage", "free"): "bytes",
    ("storage", "usage_percent"): "percent",
    ("cpu", "cores"): "number",
    ("cpu", "logical_processors"): "number",
    ("cpu", "usage_percent"): "percent",
}


def bar(value, max_value, width=30):
    """Text bar used by the simple visualization:

        bar(8, 16, 10) -> '██████░░░░'

    If the scale cannot be computed, returns an empty bar (no crash).
    """
    try:
        value = float(value)
        max_value = float(max_value)
        if max_value <= 0:
            return "░" * width
        filled = int(round(width * value / max_value))
        filled = max(0, min(width, filled))
    except (TypeError, ValueError):
        return "░" * width
    return "█" * filled + "░" * (width - filled)
