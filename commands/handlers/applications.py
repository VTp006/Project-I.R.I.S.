"""Application handlers.

Apps are found on PATH or through the OS's registered app names. No install
paths are hard-coded. Install and uninstall go through the software module,
and the executor confirms them.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import time

from commands.executor import CommandResult
from commands.handlers.processes import find_processes, is_protected
from commands.handlers.software import install_software, uninstall_software
from commands.handlers.system import IS_WINDOWS
from commands.handlers.windows import window_action


# region LAUNCH AND CLOSE

def open_app(app: str) -> CommandResult:
    """Launch an application by name, using PATH or the OS's registered app names."""
    name = app.strip()
    if not name:
        return CommandResult(success=False, error="Application name cannot be empty.")
    executable = shutil.which(name)
    try:
        if executable:
            subprocess.Popen([executable], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif IS_WINDOWS:
            os.startfile(name)  # resolves registered names such as "calc" or "chrome"
        else:
            return CommandResult(success=False, error=f"Could not find an application called '{name}'.")
    except OSError as exc:
        return CommandResult(success=False, error=f"Could not open '{name}': {exc}")
    return CommandResult(success=True, message=f"Opened {name}.", data={"app": name})


def close_app(app: str) -> CommandResult:
    """Close an application gracefully through its window. Falls back to ending its processes."""
    closed = window_action(app, "close", "Closed")
    if closed.success:
        return closed
    processes = [p for p in find_processes(app) if not is_protected(_name(p), p.pid)]
    if not processes:
        return CommandResult(success=False, error=f"'{app}' is not running.")
    stopped = 0
    for process in processes:
        try:
            process.terminate()
            stopped += 1
        except Exception:
            continue
    if stopped == 0:
        return CommandResult(success=False, error=f"Could not stop '{app}'.")
    return CommandResult(success=True, message=f"Stopped {stopped} process(es) for '{app}'.")


def _name(process) -> str:
    try:
        return process.name()
    except Exception:
        return ""


def restart_app(app: str) -> CommandResult:
    """Close an application if it is running, then open it again."""
    close_app(app)  # a "not running" result is fine here
    time.sleep(1)
    opened = open_app(app)
    if opened.success:
        opened.message = f"Restarted {app}."
    return opened

# endregion


# region WINDOW STATE

def minimize_app(app: str) -> CommandResult:
    """Minimize an application's window."""
    return window_action(app, "minimize", "Minimized")


def maximize_app(app: str) -> CommandResult:
    """Maximize an application's window."""
    return window_action(app, "maximize", "Maximized")


def focus_app(app: str) -> CommandResult:
    """Bring an application to the front."""
    return window_action(app, "activate", "Focused")


def switch_app(app: str) -> CommandResult:
    """Switch to an application. Same action as focus."""
    return window_action(app, "activate", "Switched to")

# endregion


# region INSTALL AND STATUS

def install_app(app: str) -> CommandResult:
    """Install an application. The executor has already confirmed this command."""
    return install_software(app)


def uninstall_app(app: str) -> CommandResult:
    """Uninstall an application. The executor has already confirmed this command."""
    return uninstall_software(app)


def check_app_status(app: str) -> CommandResult:
    """Whether an application is running, and how many of its processes are alive."""
    count = len(find_processes(app))
    state = "running" if count else "not running"
    return CommandResult(
        success=True,
        message=f"{app} is {state}.",
        data={"app": app, "running": count > 0, "process_count": count},
    )

# endregion
