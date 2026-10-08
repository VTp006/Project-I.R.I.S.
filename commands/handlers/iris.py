"""IRIS control handlers.

These do not own IRIS's voice loop or settings. They delegate to a controller
object that the main IRIS app registers with set_iris_controller(). The
controller is expected to provide these methods (missing ones return a clear error):

    get_wake_word()                  -> str
    set_wake_word(word: str)
    set_wake_word_enabled(enabled: bool)
    set_mode(mode: str)              -> "voice" or "text"
    sleep()
    wake()
    stop()
    restart()
    status()                         -> dict or str

Until a controller is registered, every command fails honestly instead of
pretending to succeed.
"""

from __future__ import annotations

from typing import Any

from commands.executor import CommandResult

_controller: Any = None


# region CONTROLLER INTEGRATION

def set_iris_controller(controller: Any) -> None:
    """Register the object that owns IRIS's voice loop and settings."""
    global _controller
    _controller = controller


def _call(method: str, *args: Any) -> CommandResult:
    if _controller is None:
        return CommandResult(success=False, error="IRIS controller is not connected yet.")
    action = getattr(_controller, method, None)
    if action is None:
        return CommandResult(success=False, error=f"IRIS controller does not provide '{method}'.")
    result = action(*args)
    if isinstance(result, CommandResult):
        return result
    if result is None:
        return CommandResult(success=True, message="Done.")
    return CommandResult(success=True, message=str(result), data=result)

# endregion


# region WAKE WORD

def wake_word() -> CommandResult:
    """The current wake word. The spoken name is 'iris'."""
    return _call("get_wake_word")


def enable_wake_word() -> CommandResult:
    """Turn wake word detection on."""
    return _call("set_wake_word_enabled", True)


def disable_wake_word() -> CommandResult:
    """Turn wake word detection off."""
    return _call("set_wake_word_enabled", False)


def change_wake_word(wake_word: str) -> CommandResult:
    """Change the wake word to a single word."""
    word = wake_word.strip().lower()
    if not word or " " in word or len(word) > 32:
        return CommandResult(success=False, error="The wake word must be a single word up to 32 characters.")
    return _call("set_wake_word", word)

# endregion


# region MODES AND STATE

def voice_mode() -> CommandResult:
    """Switch IRIS to voice mode."""
    return _call("set_mode", "voice")


def text_mode() -> CommandResult:
    """Switch IRIS to text mode."""
    return _call("set_mode", "text")


def sleep_mode() -> CommandResult:
    """Put IRIS to sleep until the wake word is said."""
    return _call("sleep")


def wake_iris() -> CommandResult:
    """Wake IRIS up."""
    return _call("wake")


def stop_iris() -> CommandResult:
    """Stop IRIS."""
    return _call("stop")


def restart_iris() -> CommandResult:
    """Restart IRIS."""
    return _call("restart")


def iris_status() -> CommandResult:
    """Current IRIS status."""
    return _call("status")

# endregion
