"""Window handlers: minimize, maximize, focus, move, resize, snap, close.

Windows are found through pygetwindow by case-insensitive title substring.
"""

from __future__ import annotations

from commands.executor import CommandResult
from commands.handlers.system import IS_WINDOWS, load_optional, lock_pc, missing_dependency


# region HELPERS

def get_window(query: str):
    """Return (window, None) for the first open window whose title contains query.

    Returns (None, CommandResult) when nothing matches or pygetwindow is missing.
    """
    needle = query.strip().lower()
    if not needle:
        return None, CommandResult(success=False, error="Window name cannot be empty.")
    gw = load_optional("pygetwindow")
    if gw is None:
        return None, missing_dependency("pygetwindow")
    for window in gw.getAllWindows():
        if window.title and needle in window.title.lower():
            return window, None
    return None, CommandResult(success=False, error=f"No open window matches '{query}'.")


def window_action(query: str, action: str, done: str) -> CommandResult:
    """Call one method on the matching window, such as minimize or activate."""
    window, error = get_window(query)
    if error is not None:
        return error
    try:
        getattr(window, action)()
    except Exception as exc:  # pygetwindow raises its own exception types
        return CommandResult(success=False, error=f"Could not {action} '{window.title}': {exc}")
    return CommandResult(success=True, message=f"{done} '{window.title}'.", data={"title": window.title})


def _screen_size() -> tuple[int, int] | None:
    pyautogui = load_optional("pyautogui")
    if pyautogui is None:
        return None
    size = pyautogui.size()
    return int(size[0]), int(size[1])

# endregion


# region BASIC WINDOW STATE

def minimize_window(window: str) -> CommandResult:
    """Minimize a window."""
    return window_action(window, "minimize", "Minimized")


def maximize_window(window: str) -> CommandResult:
    """Maximize a window."""
    return window_action(window, "maximize", "Maximized")


def restore_window(window: str) -> CommandResult:
    """Restore a window from minimized or maximized."""
    return window_action(window, "restore", "Restored")


def focus_window(window: str) -> CommandResult:
    """Bring a window to the front and give it focus."""
    return window_action(window, "activate", "Focused")


def switch_window(window: str) -> CommandResult:
    """Switch to a window. Same action as focus."""
    return window_action(window, "activate", "Switched to")


def close_window(window: str) -> CommandResult:
    """Close a window. The executor confirms first, since unsaved work may be lost."""
    return window_action(window, "close", "Closed")

# endregion


# region GEOMETRY

def move_window(window: str, x: str, y: str) -> CommandResult:
    """Move a window so its top-left corner is at (x, y)."""
    try:
        px, py = int(x), int(y)
    except ValueError:
        return CommandResult(success=False, error="x and y must be whole numbers.")
    found, error = get_window(window)
    if error is not None:
        return error
    try:
        found.moveTo(px, py)
    except Exception as exc:
        return CommandResult(success=False, error=f"Could not move '{found.title}': {exc}")
    return CommandResult(success=True, message=f"Moved '{found.title}' to {px}, {py}.")


def resize_window(window: str, width: str, height: str) -> CommandResult:
    """Resize a window to width by height pixels."""
    try:
        pw, ph = int(width), int(height)
    except ValueError:
        return CommandResult(success=False, error="width and height must be whole numbers.")
    found, error = get_window(window)
    if error is not None:
        return error
    try:
        found.resizeTo(pw, ph)
    except Exception as exc:
        return CommandResult(success=False, error=f"Could not resize '{found.title}': {exc}")
    return CommandResult(success=True, message=f"Resized '{found.title}' to {pw} x {ph}.")


def snap_window(window: str, position: str) -> CommandResult:
    """Snap a window to the left half, right half, or maximize it."""
    where = position.strip().lower()
    if where == "maximize":
        return maximize_window(window)
    if where not in ("left", "right"):
        return CommandResult(success=False, error="Position must be left, right or maximize.")
    size = _screen_size()
    if size is None:
        return missing_dependency("pyautogui")
    width, height = size
    half = width // 2
    x, w = (0, half) if where == "left" else (half, width - half)
    found, error = get_window(window)
    if error is not None:
        return error
    try:
        found.restore()
        found.moveTo(x, 0)
        found.resizeTo(w, height)
    except Exception as exc:
        return CommandResult(success=False, error=f"Could not snap '{found.title}': {exc}")
    return CommandResult(success=True, message=f"Snapped '{found.title}' to the {where} half.")

# endregion


# region DESKTOP

def show_desktop() -> CommandResult:
    """Show the desktop (Win+D on Windows)."""
    if not IS_WINDOWS:
        return CommandResult(success=False, error="Show desktop is only implemented for Windows.")
    pyautogui = load_optional("pyautogui")
    if pyautogui is None:
        return missing_dependency("pyautogui")
    pyautogui.hotkey("win", "d")
    return CommandResult(success=True, message="Showing the desktop.")


def lock_screen() -> CommandResult:
    """Lock the screen. Same action as lock_pc."""
    return lock_pc()

# endregion
