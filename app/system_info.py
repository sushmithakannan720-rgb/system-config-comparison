"""system_info.py — retrieve the current system configuration.

Uses:
    * psutil     – CPU, RAM, disk, hostname
    * platform   – operating system details
    * socket     – hostname / local IP address
    * subprocess – CPU model name (PowerShell on Windows, /proc on Linux)

Design rule: every field is wrapped so an unavailable hardware detail
falls back to None / "Not available" instead of crashing the app.
No value ever leaves this computer.
"""

from __future__ import annotations

import os
import platform
import socket
import subprocess
import sys
from datetime import datetime

import psutil

from .utils import APP_TITLE, APP_VERSION, NOT_AVAILABLE


# ------------------------------------------------------------------- helpers

def _run(cmd, timeout=10):
    """Run a command and return stripped stdout, or '' on any failure."""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        return (result.stdout or "").strip()
    except Exception:
        return ""


def get_cpu_name():
    """Best-effort CPU model name; returns None when it cannot be read."""
    if sys.platform == "win32":
        # PowerShell is present on every modern Windows (wmic is deprecated)
        out = _run([
            "powershell", "-NoProfile", "-Command",
            "(Get-CimInstance Win32_Processor).Name",
        ])
        if out:
            return out.splitlines()[0].strip()
        out = _run(["wmic", "cpu", "get", "name"])  # older Windows fallback
        for line in out.splitlines():
            line = line.strip()
            if line and "Processor Id" not in line:
                return line
        return None

    if sys.platform.startswith("linux"):
        try:
            with open("/proc/cpuinfo", encoding="utf-8", errors="replace") as fh:
                for line in fh:
                    if line.lower().startswith(("model name", "hardware")):
                        return line.split(":", 1)[1].strip()
        except OSError:
            pass
        return None

    if sys.platform == "darwin":
        out = _run(["sysctl", "-n", "machdep.cpu.brand_string"])
        return out or None

    return None


def get_local_ip():
    """Local (non-loopback) IPv4 address, or None if not found.

    Works offline: it only inspects the addresses assigned to this machine.
    """
    try:
        for family, _, _, _, sockaddr in socket.getaddrinfo(socket.gethostname(), None):
            ip = sockaddr[0]
            if family == socket.AF_INET and not ip.startswith("127."):
                return ip
    except OSError:
        pass
    return None


# --------------------------------------------------------------- main scan

def get_system_config():
    """Collect the full system configuration as a plain dict.

    Structure (also the JSON structure saved to disk):

        {
          "meta":    { hostname, captured_at, app_version, tool },
          "system":  { operating_system, version, build, architecture, machine, hostname },
          "cpu":     { name, cores, logical_processors, usage_percent },
          "memory":  { total, used, available, usage_percent },   (bytes)
          "storage": { total, used, free, usage_percent },        (bytes)
          "network": { hostname, ip_address }
        }
    """
    config = {
        "meta": {
            "tool": APP_TITLE,
            "app_version": APP_VERSION,
            "captured_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "hostname": None,
        },
        "system": {
            "operating_system": None,
            "version": None,
            "build": None,
            "architecture": None,
            "machine": None,
            "hostname": None,
        },
        "cpu": {
            "name": None,
            "cores": None,
            "logical_processors": None,
            "usage_percent": None,
        },
        "memory": {
            "total": None, "used": None, "available": None, "usage_percent": None,
        },
        "storage": {
            "total": None, "used": None, "free": None, "usage_percent": None,
        },
        "network": {
            "hostname": None,
            "ip_address": None,
        },
    }

    # --- system ----------------------------------------------------------
    try:
        bits = platform.architecture()[0].replace("bit", "")
        config["system"].update({
            "operating_system": platform.system(),
            "version": platform.release(),
            "build": platform.version() or None,
            "architecture": f"{bits}-bit" if bits else None,
            "machine": platform.machine() or None,
            "hostname": socket.gethostname(),
        })
    except Exception:
        pass

    # --- cpu ---------------------------------------------------------------
    try:
        config["cpu"]["name"] = get_cpu_name()
        config["cpu"]["cores"] = psutil.cpu_count(logical=False)
        config["cpu"]["logical_processors"] = psutil.cpu_count(logical=True)
        # interval=0.5 measures real usage over half a second
        config["cpu"]["usage_percent"] = round(psutil.cpu_percent(interval=0.5), 1)
    except Exception:
        pass

    # --- memory ----------------------------------------------------------
    try:
        vm = psutil.virtual_memory()
        config["memory"] = {
            "total": vm.total,
            "used": vm.used,
            "available": vm.available,
            "usage_percent": round(vm.percent, 1),
        }
    except Exception:
        pass

    # --- storage (system drive) ------------------------------------------
    try:
        if sys.platform == "win32":
            drive = os.environ.get("SystemDrive", "C") + "\\"
        else:
            drive = "/"
        du = psutil.disk_usage(drive)
        config["storage"] = {
            "total": du.total,
            "used": du.used,
            "free": du.free,
            "usage_percent": round(du.percent, 1),
        }
    except Exception:
        pass

    # --- network -----------------------------------------------------------
    try:
        config["network"]["hostname"] = socket.gethostname()
        config["network"]["ip_address"] = get_local_ip()
    except Exception:
        pass

    # --- meta hostname (shared) -------------------------------------------
    try:
        config["meta"]["hostname"] = socket.gethostname()
    except Exception:
        pass

    return config
