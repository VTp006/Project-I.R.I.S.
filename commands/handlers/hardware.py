"""Hardware handlers.

Metrics that are shared with the system domain delegate to system.py. Anything
psutil cannot report on a platform returns a clear failure, not an exception.
"""

from __future__ import annotations

import platform

from commands.executor import CommandResult
from commands.handlers.system import (
    IS_WINDOWS,
    battery_status,
    disk_usage,
    gpu_usage,
    load_optional,
    missing_dependency,
    ram_usage,
    run_command,
)


# region PROCESSOR, MEMORY, GPU

def battery_health() -> CommandResult:
    """Charge state. Wear level is not exposed by psutil, so the result says so."""
    result = battery_status()
    if result.success:
        result.message += " Battery wear level is not available through psutil."
    return result


def cpu_status() -> CommandResult:
    """CPU name, core counts, frequency and current load."""
    psutil = load_optional("psutil")
    if psutil is None:
        return missing_dependency("psutil")
    freq = psutil.cpu_freq()
    data = {
        "name": platform.processor() or "unknown",
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(),
        "usage_percent": psutil.cpu_percent(interval=0.5),
        "frequency_mhz": round(freq.current) if freq else None,
    }
    message = f"CPU at {data['usage_percent']:.0f}% on {data['logical_cores']} logical cores."
    return CommandResult(success=True, message=message, data=data)


def gpu_status() -> CommandResult:
    """GPU status through nvidia-smi (NVIDIA only)."""
    return gpu_usage()


def ram_status() -> CommandResult:
    """Memory status."""
    return ram_usage()


def disk_status() -> CommandResult:
    """Usage of the system drive, plus the mounted partitions."""
    result = disk_usage()
    psutil = load_optional("psutil")
    if result.success and psutil is not None:
        partitions = [p.mountpoint for p in psutil.disk_partitions(all=False)]
        result.data = {**result.data, "partitions": partitions}
    return result

# endregion


# region SENSORS AND DISPLAYS

def temperature_status() -> CommandResult:
    """Hardware temperature readings. psutil reports these on Linux only."""
    psutil = load_optional("psutil")
    if psutil is None:
        return missing_dependency("psutil")
    if not hasattr(psutil, "sensors_temperatures"):
        return CommandResult(success=False, error="Temperature sensors are not available through psutil on this platform.")
    temps = psutil.sensors_temperatures()
    readings = {name: [round(t.current, 1) for t in items] for name, items in temps.items()}
    values = [value for group in readings.values() for value in group]
    if not values:
        return CommandResult(success=False, error="No temperature sensors were found.")
    return CommandResult(success=True, message=f"Hottest sensor reads {max(values)} °C.", data=readings)


def display_info() -> CommandResult:
    """Connected displays with their resolution. Uses screeninfo, or the primary display on Windows."""
    monitors: list[dict] = []
    screeninfo = load_optional("screeninfo")
    if screeninfo is not None:
        try:
            monitors = [
                {"name": m.name, "width": m.width, "height": m.height, "primary": bool(m.is_primary)}
                for m in screeninfo.get_monitors()
            ]
        except Exception:
            monitors = []
    if not monitors and IS_WINDOWS:
        import ctypes

        user32 = ctypes.windll.user32
        monitors = [{
            "name": "primary",
            "width": user32.GetSystemMetrics(0),
            "height": user32.GetSystemMetrics(1),
            "primary": True,
        }]
    if not monitors:
        return CommandResult(success=False, error="Display information needs the 'screeninfo' package, or Windows.")
    return CommandResult(success=True, message=f"{len(monitors)} display(s) detected.", data=monitors)


def audio_device_info() -> CommandResult:
    """Audio output devices. Uses PowerShell on Windows and pactl on Linux."""
    if IS_WINDOWS:
        return run_command(
            ["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_SoundDevice | Select-Object -ExpandProperty Name"]
        )
    return run_command(["pactl", "list", "short", "sinks"])


def microphone_status() -> CommandResult:
    """Whether a default microphone input device is available, checked with PyAudio."""
    pyaudio = load_optional("pyaudio")
    if pyaudio is None:
        return missing_dependency("pyaudio")
    audio = pyaudio.PyAudio()
    try:
        info = audio.get_default_input_device_info()
        return CommandResult(success=True, message=f"Microphone available: {info['name']}.", data={"name": info["name"]})
    except OSError:
        return CommandResult(success=False, error="No microphone input device was found.")
    finally:
        audio.terminate()

# endregion
