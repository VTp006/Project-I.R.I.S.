"""Network handlers: Wi-Fi, Bluetooth, network information and ping.

Windows uses netsh and PowerShell. Linux uses nmcli and rfkill. Host and
network names are validated before use and passed as separate arguments.
Bluetooth on Windows enables or disables the adapter, which usually needs an
elevated (administrator) IRIS.
"""

from __future__ import annotations

import re
import socket

from commands.executor import CommandResult
from commands.handlers.system import IS_WINDOWS, load_optional, run_command, with_message

WIFI_ADAPTER = "Wi-Fi"
HOST_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9.\-:]{0,252}$")
MAX_SSID_LENGTH = 32


# region HELPERS

def _powershell(script: str, timeout: int = 60):
    return run_command(["powershell", "-NoProfile", "-Command", script], timeout=timeout)


def _wifi_device_linux() -> str | None:
    """Return the name of the first Wi-Fi device (for example wlan0), or None."""
    result = run_command(["nmcli", "-t", "-f", "DEVICE,TYPE", "device"])
    for line in (result.data or "").splitlines():
        device, _, kind = line.partition(":")
        if kind == "wifi":
            return device
    return None

# endregion


# region WI-FI

def wifi_on() -> CommandResult:
    """Turn Wi-Fi on."""
    if IS_WINDOWS:
        result = run_command(["netsh", "interface", "set", "interface", f"name={WIFI_ADAPTER}", "admin=enabled"])
    else:
        result = run_command(["nmcli", "radio", "wifi", "on"])
    return with_message(result, "Wi-Fi turned on.")


def wifi_off() -> CommandResult:
    """Turn Wi-Fi off."""
    if IS_WINDOWS:
        result = run_command(["netsh", "interface", "set", "interface", f"name={WIFI_ADAPTER}", "admin=disabled"])
    else:
        result = run_command(["nmcli", "radio", "wifi", "off"])
    return with_message(result, "Wi-Fi turned off.")


def wifi_status() -> CommandResult:
    """Current Wi-Fi state and connection details."""
    if IS_WINDOWS:
        return run_command(["netsh", "wlan", "show", "interfaces"])
    return run_command(["nmcli", "-t", "-f", "WIFI", "general"])


def connect_wifi(network: str) -> CommandResult:
    """Connect to a saved or visible Wi-Fi network by its name (SSID)."""
    ssid = network.strip()
    if not ssid or ssid.startswith("-") or len(ssid) > MAX_SSID_LENGTH or '"' in ssid:
        return CommandResult(success=False, error="That is not a valid Wi-Fi network name.")
    if IS_WINDOWS:
        argv = ["netsh", "wlan", "connect", f'name="{ssid}"']
    else:
        argv = ["nmcli", "device", "wifi", "connect", ssid]
    return with_message(run_command(argv, timeout=30), f"Connecting to {ssid}.")


def disconnect_wifi() -> CommandResult:
    """Disconnect from the current Wi-Fi network."""
    if IS_WINDOWS:
        return with_message(run_command(["netsh", "wlan", "disconnect"]), "Disconnected from Wi-Fi.")
    device = _wifi_device_linux()
    if device is None:
        return CommandResult(success=False, error="No Wi-Fi device was found.")
    return with_message(run_command(["nmcli", "device", "disconnect", device]), "Disconnected from Wi-Fi.")

# endregion


# region BLUETOOTH

def bluetooth_on() -> CommandResult:
    """Enable the Bluetooth adapter."""
    if IS_WINDOWS:
        result = _powershell("Get-PnpDevice -Class Bluetooth | Enable-PnpDevice -Confirm:$false")
    else:
        result = run_command(["rfkill", "unblock", "bluetooth"])
    return with_message(result, "Bluetooth turned on.")


def bluetooth_off() -> CommandResult:
    """Disable the Bluetooth adapter."""
    if IS_WINDOWS:
        result = _powershell("Get-PnpDevice -Class Bluetooth | Disable-PnpDevice -Confirm:$false")
    else:
        result = run_command(["rfkill", "block", "bluetooth"])
    return with_message(result, "Bluetooth turned off.")


def bluetooth_status() -> CommandResult:
    """Bluetooth adapter status."""
    if IS_WINDOWS:
        return _powershell("Get-PnpDevice -Class Bluetooth | Select-Object -ExpandProperty Status")
    return run_command(["rfkill", "list", "bluetooth"])

# endregion


# region INFORMATION AND PING

def network_info() -> CommandResult:
    """Host name, local IP address, and IPv4 addresses for each interface."""
    local_ip = None
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(("8.8.8.8", 80))  # UDP connect sends no packets; it only picks a route
            local_ip = probe.getsockname()[0]
    except OSError:
        pass
    interfaces: dict[str, list[str]] = {}
    psutil = load_optional("psutil")
    if psutil is not None:
        for name, addresses in psutil.net_if_addrs().items():
            interfaces[name] = [a.address for a in addresses if a.family == socket.AF_INET]
    data = {"hostname": socket.gethostname(), "local_ip": local_ip, "interfaces": interfaces}
    return CommandResult(success=True, message=f"This computer is {data['hostname']} at {local_ip or 'an unknown address'}.", data=data)


def ping_host(host: str) -> CommandResult:
    """Ping a host name or IP address four times."""
    target = host.strip()
    if not HOST_RE.match(target):
        return CommandResult(success=False, error="That is not a valid host name or IP address.")
    argv = ["ping", "-n", "4", target] if IS_WINDOWS else ["ping", "-c", "4", target]
    result = run_command(argv, timeout=30)
    if result.success:
        result.message = f"Ping to {target} succeeded."
    return result

# endregion
