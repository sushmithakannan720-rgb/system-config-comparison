"""comparison.py — compare two system configurations.

Pure logic: no GUI, no psutil — which is why it is easy to unit test
(see tests/test_comparison.py).

Comparison rules:
    * both values present and equal        -> SAME
    * both present and different           -> DIFFERENT (+ factual note)
    * missing on one or both systems       -> MISSING  (never a crash)

Difference notes are deliberately factual (e.g. "System B has 8 GB more
RAM than System A") — the tool never claims which computer is "better".
"""

from __future__ import annotations

from .utils import NOT_AVAILABLE, bytes_to_str, clean_value, get_path

# ---------------------------------------------------------------- parameters
# Each entry: key, table display name, (section, field) path, kind.
# kind: "text"  -> string equality
#       "number"-> integer comparison (cores, logical processors)
#       "bytes" -> byte-count comparison (RAM, storage)

COMPARE_PARAMS = [
    ("operating_system", "Operating System", ("system", "operating_system"), "text"),
    ("os_version", "OS Version", ("system", "version"), "text"),
    ("architecture", "Architecture", ("system", "architecture"), "text"),
    ("hostname", "Hostname", ("system", "hostname"), "text"),
    ("cpu_name", "Processor", ("cpu", "name"), "text"),
    ("cores", "CPU Cores", ("cpu", "cores"), "number"),
    ("logical_processors", "Logical Processors", ("cpu", "logical_processors"), "number"),
    ("ram_total", "RAM (Total)", ("memory", "total"), "bytes"),
    ("storage_total", "Storage (Total)", ("storage", "total"), "bytes"),
    ("storage_free", "Storage (Free)", ("storage", "free"), "bytes"),
    ("ip_address", "IP Address", ("network", "ip_address"), "text"),
]

# factual, non-judgemental wording per parameter
TEXT_NOTES = {
    "operating_system": "The operating systems are different.",
    "os_version": "The operating system versions are different.",
    "architecture": "The architectures are different.",
    "hostname": "The hostnames are different.",
    "cpu_name": "The processors are different.",
    "ip_address": "The IP addresses are different.",
}

SAME_NOTES = {
    "operating_system": "Same operating system.",
    "os_version": "Same OS version.",
    "architecture": "Same architecture.",
    "hostname": "Same hostname.",
    "cpu_name": "Same processor.",
    "ip_address": "Same IP address.",
}

NUMBER_LABELS = {
    "cores": "physical cores",
    "logical_processors": "logical processors",
}

BYTES_LABELS = {
    "ram_total": "RAM",
    "storage_total": "total storage",
    "storage_free": "free storage",
}

SUMMARY_LABELS = {
    "operating_system": "operating systems",
    "os_version": "OS versions",
    "architecture": "architecture",
    "hostname": "hostname",
    "cpu_name": "processors",
    "cores": "CPU core count",
    "logical_processors": "logical processor count",
    "ram_total": "RAM capacity",
    "storage_total": "storage capacity",
    "storage_free": "free storage",
    "ip_address": "IP address",
}

STATUS_SAME = "SAME"
STATUS_DIFFERENT = "DIFFERENT"
STATUS_MISSING = "MISSING"


# ------------------------------------------------------------------ helpers

def _to_number(value):
    try:
        number = float(value)
        return int(number) if number.is_integer() else number
    except (TypeError, ValueError):
        return None


def _display(key, kind, raw):
    """Human-readable cell text for the comparison table."""
    if raw is None:
        return NOT_AVAILABLE
    if kind == "bytes":
        return bytes_to_str(raw)
    if kind == "number":
        number = _to_number(raw)
        return str(number) if number is not None else str(raw)
    return str(raw)


def _row(key, name, raw_a, raw_b, kind, status, note):
    return {
        "key": key,
        "name": name,
        "value_a": _display(key, kind, raw_a),
        "value_b": _display(key, kind, raw_b),
        "status": status,
        "note": note,
    }


# ------------------------------------------------------------------ compare

def compare_configs(config_a, config_b):
    """Compare two configuration dicts and return a list of row dicts.

    Row dict: {key, name, value_a, value_b, status, note}
    """
    rows = []
    for key, name, path, kind in COMPARE_PARAMS:
        raw_a = clean_value(get_path(config_a, path))
        raw_b = clean_value(get_path(config_b, path))

        # missing data -> report it, never crash
        if raw_a is None and raw_b is None:
            rows.append(_row(key, name, None, None, kind, STATUS_MISSING,
                             "Value not available on either system."))
            continue
        if raw_a is None or raw_b is None:
            missing_on = "System A" if raw_a is None else "System B"
            rows.append(_row(key, name, raw_a, raw_b, kind, STATUS_MISSING,
                             f"Value not available on {missing_on}."))
            continue

        if kind == "text":
            if raw_a == raw_b:
                rows.append(_row(key, name, raw_a, raw_b, kind, STATUS_SAME,
                                 SAME_NOTES.get(key, "Same.")))
            else:
                rows.append(_row(key, name, raw_a, raw_b, kind, STATUS_DIFFERENT,
                                 TEXT_NOTES.get(key, "The values are different.")))

        elif kind == "number":
            number_a, number_b = _to_number(raw_a), _to_number(raw_b)
            if number_a is None or number_b is None:
                rows.append(_row(key, name, raw_a, raw_b, kind, STATUS_MISSING,
                                 "Value is not numeric."))
                continue
            if number_a == number_b:
                rows.append(_row(key, name, raw_a, raw_b, kind, STATUS_SAME, "Same."))
            else:
                more_less = "more" if number_b > number_a else "less"
                note = (f"System B has {abs(number_b - number_a)} {more_less} "
                        f"{NUMBER_LABELS[key]} than System A.")
                rows.append(_row(key, name, raw_a, raw_b, kind, STATUS_DIFFERENT, note))

        else:  # kind == "bytes"
            number_a, number_b = _to_number(raw_a), _to_number(raw_b)
            if number_a is None or number_b is None:
                rows.append(_row(key, name, raw_a, raw_b, kind, STATUS_MISSING,
                                 "Value is not numeric."))
                continue
            if number_a == number_b:
                rows.append(_row(key, name, raw_a, raw_b, kind, STATUS_SAME, "Same."))
            else:
                more_less = "more" if number_b > number_a else "less"
                note = (f"System B has {bytes_to_str(abs(number_b - number_a))} "
                        f"{more_less} {BYTES_LABELS[key]} than System A.")
                rows.append(_row(key, name, raw_a, raw_b, kind, STATUS_DIFFERENT, note))

    return rows


def summarize(rows):
    """Build the comparison summary.

    Returns:
        {
          total, same, different, missing, total_differences,
          lines: ["✓ Same architecture.", "✗ Different RAM capacity.", ...]
        }
    """
    counts = {STATUS_SAME: 0, STATUS_DIFFERENT: 0, STATUS_MISSING: 0}
    lines = []
    for row in rows:
        counts[row["status"]] += 1
        label = SUMMARY_LABELS.get(row["key"], row["name"].lower())
        if row["status"] == STATUS_SAME:
            lines.append(f"✓ Same {label}.")
        elif row["status"] == STATUS_DIFFERENT:
            lines.append(f"✗ Different {label}.")
        else:
            lines.append(f"⚠ {label} not available on one or both systems.")

    return {
        "total": len(rows),
        "same": counts[STATUS_SAME],
        "different": counts[STATUS_DIFFERENT],
        "missing": counts[STATUS_MISSING],
        "total_differences": counts[STATUS_DIFFERENT],
        "lines": lines,
    }
