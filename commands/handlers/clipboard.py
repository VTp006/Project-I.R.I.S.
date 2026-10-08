"""Clipboard handlers.

Copy and paste send Ctrl+C and Ctrl+V to the focused window. Reading and
writing text use pyperclip, which needs xclip or xsel on Linux.
"""

from __future__ import annotations

from commands.executor import CommandResult
from commands.handlers.system import load_optional, missing_dependency


# region HELPERS

def _hotkey(*keys: str) -> CommandResult:
    pyautogui = load_optional("pyautogui")
    if pyautogui is None:
        return missing_dependency("pyautogui")
    pyautogui.hotkey(*keys)
    return CommandResult(success=True, message="Done.")


def _pyperclip():
    pyperclip = load_optional("pyperclip")
    return pyperclip, (missing_dependency("pyperclip") if pyperclip is None else None)

# endregion


# region COPY AND PASTE

def copy() -> CommandResult:
    """Copy the current selection (Ctrl+C)."""
    result = _hotkey("ctrl", "c")
    if result.success:
        result.message = "Copied the selection."
    return result


def paste() -> CommandResult:
    """Paste the clipboard into the focused window (Ctrl+V)."""
    result = _hotkey("ctrl", "v")
    if result.success:
        result.message = "Pasted the clipboard."
    return result

# endregion


# region CLIPBOARD TEXT

def read_clipboard() -> CommandResult:
    """Return the current clipboard text."""
    pyperclip, error = _pyperclip()
    if error is not None:
        return error
    try:
        text = pyperclip.paste()
    except pyperclip.PyperclipException as exc:
        return CommandResult(success=False, error=f"Could not read the clipboard: {exc}")
    return CommandResult(success=True, message=f"Clipboard has {len(text)} character(s).", data=text)


def write_clipboard(text: str) -> CommandResult:
    """Put text on the clipboard."""
    pyperclip, error = _pyperclip()
    if error is not None:
        return error
    try:
        pyperclip.copy(text)
    except pyperclip.PyperclipException as exc:
        return CommandResult(success=False, error=f"Could not write the clipboard: {exc}")
    return CommandResult(success=True, message=f"Copied {len(text)} character(s) to the clipboard.")


def clear_clipboard() -> CommandResult:
    """Empty the clipboard by writing an empty string."""
    result = write_clipboard("")
    if result.success:
        result.message = "Clipboard cleared."
    return result


def clipboard_history() -> CommandResult:
    """Clipboard history is kept by Windows (Win+V) and is not readable by IRIS yet."""
    return CommandResult(
        success=False,
        error="Clipboard history is not available to IRIS yet. Use Win+V on Windows to see it.",
    )

# endregion
