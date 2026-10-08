"""Process handlers.

Processes are targeted by name or PID. Protected system processes and IRIS
itself are never stopped or killed. No user text reaches a shell.
"""

from __future__ import annotations

import datetime
import os

from commands.executor import CommandResult
from commands.handlers.system import load_optional

PROTECTED_NAMES = {
    "system", "system idle process", "init", "systemd", "explorer.exe", "csrss.exe",
    "wininit.exe", "winlogon.exe", "services.exe", "lsass.exe", "smss.exe",
}


# region HELPERS

def is_protected(name: str, pid: int) -> bool:
    """True for PIDs 0-4, IRIS's own process, and core operating system processes."""
    if pid <= 4 or pid == os.getpid():
        return True
    return (name or "").lower() in PROTECTED_NAMES


def _base(name: str) -> str:
    return name[:-4] if name.endswith(".exe") else name


def _name_of(proc) -> str:
    """Process name for either a name-scan result or a PID lookup."""
    try:
        return proc.name()
    except Exception:
        return ""


def find_processes(query: str, exact: bool = False) -> list:
    """Return psutil.Process objects matching a name, or a single process for a numeric PID.

    With exact=False, a name matches when it appears inside the process name.
    """
    psutil = load_optional("psutil")
    if psutil is None:
        return []
    needle = query.strip().lower()
    if not needle:
        return []
    if needle.isdigit():
        try:
            return [psutil.Process(int(needle))]
        except psutil.Error:
            return []
    matches = []
    for proc in psutil.process_iter(["pid", "name"]):
        lowered = (proc.info.get("name") or "").lower()
        same = lowered == needle or _base(lowered) == _base(needle)
        if same or (not exact and needle in lowered):
            matches.append(proc)
    return matches


def _single(query: str):
    """Return (process, None) for the best match, or (None, CommandResult) when nothing matches."""
    matches = find_processes(query, exact=True) or find_processes(query)
    if not matches:
        return None, CommandResult(success=False, error=f"No running process matches '{query}'.")
    return matches[0], None


def _signal(query: str, action: str, done: str, exact: bool) -> CommandResult:
    """Terminate or kill every matching process that is not protected."""
    if not query.strip():
        return CommandResult(success=False, error="Process name cannot be empty.")
    matches = find_processes(query, exact=exact)
    if not matches:
        return CommandResult(success=False, error=f"No running process matches '{query}'.")
    acted = 0
    skipped = 0
    for proc in matches:
        try:
            if is_protected(_name_of(proc), proc.pid):
                skipped += 1
                continue
            getattr(proc, action)()
            acted += 1
        except Exception:
            skipped += 1
    if acted == 0:
        return CommandResult(success=False, error=f"Could not {action} '{query}' ({skipped} process(es) skipped).")
    note = f" {skipped} protected or inaccessible process(es) skipped." if skipped else ""
    return CommandResult(success=True, message=f"{done} {acted} process(es) for '{query}'.{note}")

# endregion


# region LISTING AND INFO

def list_processes() -> CommandResult:
    """All running processes, sorted by name."""
    psutil = load_optional("psutil")
    if psutil is None:
        return CommandResult(success=False, error="Process listing needs the 'psutil' package.")
    listing = sorted(
        ({"pid": p.info["pid"], "name": p.info["name"] or ""} for p in psutil.process_iter(["pid", "name"])),
        key=lambda item: item["name"].lower(),
    )
    return CommandResult(success=True, message=f"{len(listing)} process(es) running.", data=listing)


def find_process(query: str) -> CommandResult:
    """Find processes whose names contain query."""
    if not query.strip():
        return CommandResult(success=False, error="Search text cannot be empty.")
    matches = find_processes(query)
    listing = [{"pid": p.pid, "name": _name_of(p)} for p in matches]
    return CommandResult(success=True, message=f"Found {len(listing)} matching process(es).", data=listing)


def process_info(process: str) -> CommandResult:
    """Details for one process: PID, status, memory, start time and executable path."""
    psutil = load_optional("psutil")
    if psutil is None:
        return CommandResult(success=False, error="Process details need the 'psutil' package.")
    proc, error = _single(process)
    if error is not None:
        return error
    try:
        with proc.oneshot():
            data = {
                "pid": proc.pid,
                "name": proc.name(),
                "status": proc.status(),
                "memory_mb": round(proc.memory_info().rss / 1024**2, 1),
                "started": datetime.datetime.fromtimestamp(proc.create_time()).isoformat(timespec="seconds"),
            }
        try:
            data["executable"] = proc.exe()
        except psutil.AccessDenied:
            data["executable"] = None
    except psutil.Error as exc:
        return CommandResult(success=False, error=f"Could not read process details: {exc}")
    return CommandResult(success=True, message=f"{data['name']} (PID {data['pid']}) is {data['status']}.", data=data)


def check_process_status(process: str) -> CommandResult:
    """Whether a process with this name or PID is running."""
    matches = find_processes(process)
    running = bool(matches)
    message = f"'{process}' is running ({len(matches)} process(es))." if running else f"'{process}' is not running."
    return CommandResult(success=True, message=message, data={"running": running, "count": len(matches)})

# endregion


# region START, STOP, KILL

def start_process(process: str) -> CommandResult:
    """Start a program by name. No arguments are passed, and no shell is used."""
    from commands.handlers.applications import open_app  # local import avoids a circular import

    return open_app(process)


def stop_process(process: str) -> CommandResult:
    """Ask a process to terminate, matching by exact name or PID."""
    return _signal(process, "terminate", "Stopped", exact=True)


def kill_process(process: str) -> CommandResult:
    """Forcefully terminate a process. The executor has already confirmed this command."""
    return _signal(process, "kill", "Killed", exact=True)

# endregion
