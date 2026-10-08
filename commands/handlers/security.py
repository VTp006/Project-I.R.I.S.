"""Security handlers.

IRIS never receives, stores or displays passwords. Password changes open the
operating system's own settings page. Firewall commands run fixed programs, and
the executor confirms them before they run.
"""

from __future__ import annotations

import os

from commands.executor import CommandResult
from commands.handlers.processes import list_processes
from commands.handlers.system import IS_WINDOWS, run_command, with_message


# region PASSWORD

def change_password() -> CommandResult:
    """Open the system's sign-in settings so the user can change the password themselves."""
    if IS_WINDOWS:
        try:
            os.startfile("ms-settings:signinoptions")
        except OSError as exc:
            return CommandResult(success=False, error=f"Could not open sign-in settings: {exc}")
        return CommandResult(
            success=True,
            message="I opened Windows sign-in settings. Change your password there. I never see or store it.",
            data={"performed": False},
        )
    return CommandResult(
        success=True,
        message="Run 'passwd' in a terminal to change your password. I never see or store it.",
        data={"performed": False},
    )

# endregion


# region FIREWALL AND STATUS

def _firewall(state: str) -> CommandResult:
    if IS_WINDOWS:
        return run_command(["netsh", "advfirewall", "set", "allprofiles", "state", state])
    if state == "on":
        return run_command(["ufw", "enable"])
    return run_command(["ufw", "disable"])


def enable_firewall() -> CommandResult:
    """Turn the firewall on for all profiles. The executor has already confirmed this command."""
    return with_message(_firewall("on"), "Firewall turned on.")


def disable_firewall() -> CommandResult:
    """Turn the firewall off. The executor has already confirmed this dangerous command."""
    return with_message(_firewall("off"), "Firewall turned off.")


def check_security_status() -> CommandResult:
    """Firewall profile state and, on Windows, antivirus and real-time protection state."""
    if IS_WINDOWS:
        script = (
            "Get-NetFirewallProfile | Select-Object Name,Enabled | Format-Table -HideTableHeaders | Out-String; "
            "Get-MpComputerStatus | Select-Object AntivirusEnabled,RealTimeProtectionEnabled | Format-List | Out-String"
        )
        return run_command(["powershell", "-NoProfile", "-Command", script], timeout=60)
    return run_command(["ufw", "status"])


def check_running_processes() -> CommandResult:
    """List running processes, for a quick security review."""
    return list_processes()

# endregion
