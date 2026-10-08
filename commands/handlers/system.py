"""System handlers: power and session control, system metrics, and shared helpers.

Power and session commands run fixed system programs. User text is never
placed into a shell command.
"""

from __future__ import annotations

import getpass
import importlib
import os
import platform
import shutil
import subprocess
from typing import Any

from commands.executor import CommandResult

IS_WINDOWS = platform.system() == "Windows"


# region SHARED HELPERS

def load_optional(module_name: str) -> Any:
    """Import an optional package. Returns None if it is missing or unusable.

    GUI packages such as pyautogui can fail with errors other than ImportError
    when there is no display, so every failure counts as "not available".
    """
    try:
        return importlib.import_module(module_name)
    except Exception:
        return None


def missing_dependency(package: str) -> CommandResult:
    """Standard failure for a feature whose optional package is not installed."""
    return CommandResult(
        success=False,
        error=f"This feature needs the '{package}' package. Install it with: pip install {package}",
    )


def with_message(result: CommandResult, message: str) -> CommandResult:
    """Replace the message of a successful result. Failures keep their error."""
    if result.success:
        result.message = message
    return result


def run_command(argv: list[str], timeout: int = 20) -> CommandResult:
    """Run a fixed program with an argument list. Never uses a shell."""
    if shutil.which(argv[0]) is None:
        return CommandResult(success=False, error=f"'{argv[0]}' is not available on this system.")
    try:
        proc = subprocess.run(argv, capture_output=True, text=True, timeout=timeout, check=False)
    except subprocess.TimeoutExpired:
        return CommandResult(success=False, error=f"'{argv[0]}' timed out.")
    output = (proc.stdout or "").strip()
    if proc.returncode != 0:
        detail = (proc.stderr or output).strip() or f"exit code {proc.returncode}"
        return CommandResult(success=False, error=detail, data=output)
    return CommandResult(success=True, message=output or "Done.", data=output)


def current_user() -> str:
    """Return the logged-in user name, or an empty string if it cannot be read."""
    try:
        return getpass.getuser()
    except Exception:
        return ""

# endregion


# region POWER AND SESSION

def _power(windows_argv: list[str], linux_argv: list[str], message: str) -> CommandResult:
    """Run the platform's power command and report a clean message."""
    return with_message(run_command(windows_argv if IS_WINDOWS else linux_argv), message)


def shutdown() -> CommandResult:
    """Shut the computer down after a 30 second delay. The executor confirms first."""
    return _power(["shutdown", "/s", "/t", "30"], ["systemctl", "poweroff"], "Shutdown started.")


def restart() -> CommandResult:
    """Restart the computer after a 30 second delay. The executor confirms first."""
    return _power(["shutdown", "/r", "/t", "30"], ["systemctl", "reboot"], "Restart started.")


def sleep() -> CommandResult:
    """Put the computer to sleep."""
    return _power(
        ["rundll32.exe", "powrprof.dll,SetSuspendState", "0,1,0"],
        ["systemctl", "suspend"],
        "Going to sleep.",
    )


def hibernate() -> CommandResult:
    """Hibernate the computer. Requires hibernation to be enabled on the machine."""
    return _power(["shutdown", "/h"], ["systemctl", "hibernate"], "Hibernating.")


def lock_pc() -> CommandResult:
    """Lock the computer."""
    return _power(
        ["rundll32.exe", "user32.dll,LockWorkStation"],
        ["loginctl", "lock-session"],
        "Computer locked.",
    )


def log_out() -> CommandResult:
    """Log out the current user. The executor confirms first."""
    return _power(["shutdown", "/l"], ["loginctl", "terminate-user", current_user()], "Logging out.")


def cancel_shutdown() -> CommandResult:
    """Cancel a pending shutdown or restart."""
    return _power(["shutdown", "/a"], ["shutdown", "-c"], "Pending shutdown cancelled.")


def exit_iris() -> CommandResult:
    """Ask the main IRIS loop to exit. The loop reads data['action']."""
    return CommandResult(success=True, message="Exiting IRIS.", data={"action": "exit"})

# endregion


# region SYSTEM METRICS

def system_info() -> CommandResult:
    """Operating system, hardware identity and Python version."""
    data = {
        "os": platform.system(),
        "release": platform.release(),
        "version": platform.version(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "hostname": platform.node(),
        "python": platform.python_version(),
    }
    return CommandResult(success=True, message=f"{data['os']} {data['release']} on {data['hostname']}.", data=data)


def os_info() -> CommandResult:
    """Operating system name and version."""
    data = {"os": platform.system(), "release": platform.release(), "version": platform.version()}
    return CommandResult(success=True, message=f"{data['os']} {data['release']}.", data=data)


def cpu_usage() -> CommandResult:
    """Current CPU load as a percentage, sampled over half a second."""
    psutil = load_optional("psutil")
    if psutil is None:
        return missing_dependency("psutil")
    percent = psutil.cpu_percent(interval=0.5)
    return CommandResult(success=True, message=f"CPU usage is {percent:.0f}%.", data={"percent": percent})


def gpu_usage() -> CommandResult:
    """GPU name, utilisation and memory through nvidia-smi (NVIDIA GPUs only)."""
    result = run_command(
        ["nvidia-smi", "--query-gpu=name,utilization.gpu,memory.used,memory.total", "--format=csv,noheader,nounits"]
    )
    if not result.success:
        return CommandResult(success=False, error="GPU usage needs an NVIDIA GPU with nvidia-smi installed.")
    return CommandResult(success=True, message=f"GPU: {result.data}", data=result.data)


def ram_usage() -> CommandResult:
    """Memory use in percent and gigabytes."""
    psutil = load_optional("psutil")
    if psutil is None:
        return missing_dependency("psutil")
    memory = psutil.virtual_memory()
    data = {
        "percent": memory.percent,
        "used_gb": round(memory.used / 1024**3, 2),
        "total_gb": round(memory.total / 1024**3, 2),
    }
    message = f"RAM is {memory.percent:.0f}% used ({data['used_gb']} of {data['total_gb']} GB)."
    return CommandResult(success=True, message=message, data=data)


def disk_usage() -> CommandResult:
    """Usage of the system drive (C: on Windows, / on Linux)."""
    root = os.path.abspath(os.sep)
    usage = shutil.disk_usage(root)
    data = {
        "path": root,
        "total_gb": round(usage.total / 1024**3, 1),
        "used_gb": round(usage.used / 1024**3, 1),
        "free_gb": round(usage.free / 1024**3, 1),
    }
    percent = usage.used / usage.total * 100 if usage.total else 0
    return CommandResult(
        success=True,
        message=f"{root} is {percent:.0f}% full ({data['free_gb']} GB free).",
        data=data,
    )


def battery_status() -> CommandResult:
    """Battery charge and whether the charger is connected."""
    psutil = load_optional("psutil")
    if psutil is None:
        return missing_dependency("psutil")
    battery = psutil.sensors_battery()
    if battery is None:
        return CommandResult(success=False, error="No battery was detected on this computer.")
    data = {
        "percent": round(battery.percent, 1),
        "plugged_in": bool(battery.power_plugged),
        "seconds_left": battery.secsleft if battery.secsleft > 0 else None,
    }
    state = "plugged in" if data["plugged_in"] else "on battery"
    return CommandResult(success=True, message=f"Battery is at {data['percent']}% and {state}.", data=data)


def network_status() -> CommandResult:
    """Network interfaces that are currently up."""
    psutil = load_optional("psutil")
    if psutil is None:
        return missing_dependency("psutil")
    up = sorted(name for name, stats in psutil.net_if_stats().items() if stats.isup)
    message = f"{len(up)} network interface(s) up: {', '.join(up) or 'none'}."
    return CommandResult(success=True, message=message, data={"up": up})

# endregion
