"""Software management through the system package manager.

Windows uses winget. Linux uses apt-get. The package manager is detected at
runtime, not hard-coded. Names are validated and passed as separate arguments,
never through a shell. The executor confirms installs, uninstalls and updates.
"""

from __future__ import annotations

import re
import shutil

from commands.executor import CommandResult
from commands.handlers.system import IS_WINDOWS, run_command

NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+\- ]{0,127}$")
INSTALL_TIMEOUT = 900

# Each action maps to the argument list for each supported package manager.
_ACTIONS = {
    "install": {
        "winget": ["winget", "install", "--name", "{name}", "--accept-package-agreements", "--accept-source-agreements"],
        "apt": ["apt-get", "install", "-y", "{name}"],
    },
    "uninstall": {
        "winget": ["winget", "uninstall", "--name", "{name}"],
        "apt": ["apt-get", "remove", "-y", "{name}"],
    },
    "update": {
        "winget": ["winget", "upgrade", "--name", "{name}", "--accept-package-agreements", "--accept-source-agreements"],
        "apt": ["apt-get", "install", "--only-upgrade", "-y", "{name}"],
    },
    "check": {
        "winget": ["winget", "upgrade"],
        "apt": ["apt", "list", "--upgradable"],
    },
    "list": {
        "winget": ["winget", "list"],
        "apt": ["dpkg-query", "-W", "-f=${Package}\n"],
    },
}


# region HELPERS

def _package_manager() -> str | None:
    if IS_WINDOWS and shutil.which("winget"):
        return "winget"
    if shutil.which("apt-get"):
        return "apt"
    return None


def _valid(name: str) -> bool:
    return bool(NAME_RE.match(name.strip()))


def _run_action(action: str, name: str | None, timeout: int = 120) -> CommandResult:
    """Build the right argument list for this action and run it."""
    manager = _package_manager()
    if manager is None:
        return CommandResult(success=False, error="No supported package manager (winget or apt) was found.")
    template = _ACTIONS[action][manager]
    if name is not None:
        if not _valid(name):
            return CommandResult(success=False, error=f"'{name}' is not a valid software name.")
        argv = [part.replace("{name}", name.strip()) for part in template]
    else:
        argv = list(template)
    return run_command(argv, timeout=timeout)

# endregion


# region INSTALL AND UNINSTALL

def install_software(software: str) -> CommandResult:
    """Install a package by name. The executor has already confirmed this command."""
    return _run_action("install", software, timeout=INSTALL_TIMEOUT)


def uninstall_software(software: str) -> CommandResult:
    """Uninstall a package by name. The executor has already confirmed this command."""
    return _run_action("uninstall", software, timeout=INSTALL_TIMEOUT)


def update_software(software: str) -> CommandResult:
    """Upgrade one package. The executor has already confirmed this command."""
    return _run_action("update", software, timeout=INSTALL_TIMEOUT)

# endregion


# region QUERIES

def check_updates() -> CommandResult:
    """List packages that have updates available."""
    return _run_action("check", None, timeout=120)


def list_installed_software() -> CommandResult:
    """List installed packages."""
    return _run_action("list", None, timeout=120)


def launch_software(software: str) -> CommandResult:
    """Launch an installed program. Same behaviour as OPEN_APP."""
    from commands.handlers.applications import open_app  # local import avoids a circular import

    return open_app(software)

# endregion
