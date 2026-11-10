import os
import platform
import shutil
import time

import psutil


def get_cpu_usage():
    """Current CPU usage."""
    return {
        "cpu_percent": psutil.cpu_percent(interval=1),
        "cpu_cores": psutil.cpu_count(logical=True),
    }


def get_memory_usage():
    """Current RAM usage."""
    m = psutil.virtual_memory()
    gb = 1024 ** 3
    return {
        "total_gb": round(m.total / gb, 1),
        "used_gb": round(m.used / gb, 1),
        "available_gb": round(m.available / gb, 1),
        "percent_used": m.percent,
    }


def get_disk_usage():
    """Disk usage of the volume that holds your home folder."""
    d = shutil.disk_usage(os.path.expanduser("~"))
    gb = 1024 ** 3
    return {
        "total_gb": round(d.total / gb, 1),
        "used_gb": round(d.used / gb, 1),
        "free_gb": round(d.free / gb, 1),
        "percent_used": round(d.used / d.total * 100, 1),
    }


def get_system_info():
    """Basic facts about this machine."""
    return {
        "hostname": platform.node(),
        "os": platform.system(),
        "os_version": platform.release(),
        "machine": platform.machine(),
        "uptime_hours": round((time.time() - psutil.boot_time()) / 3600, 1),
    }


# The allowlist: Gemini can ONLY call functions listed here.
TOOLS = {
    "get_cpu_usage": get_cpu_usage,
    "get_memory_usage": get_memory_usage,
    "get_disk_usage": get_disk_usage,
    "get_system_info": get_system_info,
}

# The menu we show Gemini: a name and a plain-English description for each tool.
TOOL_DECLARATIONS = [
    {
        "name": "get_cpu_usage",
        "description": "Get the current CPU usage percentage and number of CPU cores of the server.",
    },
    {
        "name": "get_memory_usage",
        "description": "Get the current RAM memory usage of the server: total, used, available and percent used.",
    },
    {
        "name": "get_disk_usage",
        "description": "Get the disk space usage of the server: total, used, free and percent used.",
    },
    {
        "name": "get_system_info",
        "description": "Get basic information about the server: hostname, operating system and uptime.",
    },
]


def run_tool(name, args=None):
    """Run an allowlisted tool by name. Unknown names are refused."""
    func = TOOLS.get(name)
    if func is None:
        return {"error": f"Unknown tool: {name}"}
    try:
        return func(**(args or {}))
    except Exception as e:
        return {"error": f"{type(e).__name__}: {e}"}
