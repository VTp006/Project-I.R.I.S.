"""Audio and media handlers.

Windows sends media keys through keybd_event, and uses pycaw (optional) for
exact volume and mute. Linux uses playerctl and pactl. Pause and resume are
toggles on Windows, because the media key only toggles playback.
"""

from __future__ import annotations

import os
import webbrowser

from commands.executor import CommandResult
from commands.handlers.files import open_with_default_app
from commands.handlers.system import IS_WINDOWS, load_optional, missing_dependency, run_command, with_message

KEYEVENTF_KEYUP = 0x0002
VK_PLAY_PAUSE = 0xB3
VK_STOP = 0xB2
VK_NEXT = 0xB0
VK_PREVIOUS = 0xB1
VK_VOLUME_UP = 0xAF
VK_VOLUME_DOWN = 0xAE


# region HELPERS

def _media_key(windows_key: int, linux_argv: list[str]) -> CommandResult:
    """Press a media key on Windows, or run the matching playerctl or pactl command on Linux."""
    if IS_WINDOWS:
        import ctypes

        user32 = ctypes.windll.user32
        user32.keybd_event(windows_key, 0, 0, 0)
        user32.keybd_event(windows_key, 0, KEYEVENTF_KEYUP, 0)
        return CommandResult(success=True, message="Done.")
    return run_command(linux_argv)


def _endpoint_volume():
    """Return the default speakers' volume control from pycaw, or None if pycaw is missing."""
    pycaw = load_optional("pycaw.pycaw")
    if pycaw is None:
        return None
    return pycaw.AudioUtilities.GetSpeakers().EndpointVolume


def _set_mute(muted: bool) -> CommandResult:
    label = "Muted." if muted else "Unmuted."
    if IS_WINDOWS:
        endpoint = _endpoint_volume()
        if endpoint is None:
            return missing_dependency("pycaw")
        endpoint.SetMute(1 if muted else 0, None)
        return CommandResult(success=True, message=label)
    return with_message(
        run_command(["pactl", "set-sink-mute", "@DEFAULT_SINK@", "1" if muted else "0"]),
        label,
    )


def _open_media(source: str, kind: str) -> CommandResult:
    """Open a local media file or a web link with the default app or browser."""
    target = source.strip()
    if target.startswith(("http://", "https://")):
        webbrowser.open_new_tab(target)
        return CommandResult(success=True, message=f"Opened the {kind} link.", data={"url": target})
    if not os.path.isfile(os.path.expanduser(target)):
        return CommandResult(success=False, error=f"'{source}' is not a media file or web link I can open.")
    return open_with_default_app(target)

# endregion


# region PLAYBACK

def play_music(source: str) -> CommandResult:
    """Open a music file or link in its default player. Searching by song name is not supported."""
    return _open_media(source, "music")


def pause_media() -> CommandResult:
    """Pause playback."""
    return with_message(_media_key(VK_PLAY_PAUSE, ["playerctl", "pause"]), "Paused.")


def resume_media() -> CommandResult:
    """Resume playback."""
    return with_message(_media_key(VK_PLAY_PAUSE, ["playerctl", "play"]), "Resumed.")


def stop_media() -> CommandResult:
    """Stop playback."""
    return with_message(_media_key(VK_STOP, ["playerctl", "stop"]), "Stopped playback.")


def next_track() -> CommandResult:
    """Skip to the next track."""
    return with_message(_media_key(VK_NEXT, ["playerctl", "next"]), "Next track.")


def previous_track() -> CommandResult:
    """Go to the previous track."""
    return with_message(_media_key(VK_PREVIOUS, ["playerctl", "previous"]), "Previous track.")


def play_video(source: str) -> CommandResult:
    """Open a video file or link in its default player."""
    return _open_media(source, "video")


def stop_video() -> CommandResult:
    """Stop video playback. Uses the same stop control as media."""
    return with_message(_media_key(VK_STOP, ["playerctl", "stop"]), "Stopped the video.")

# endregion


# region VOLUME

def volume_up() -> CommandResult:
    """Raise the volume by one step."""
    return with_message(
        _media_key(VK_VOLUME_UP, ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "+5%"]),
        "Volume up.",
    )


def volume_down() -> CommandResult:
    """Lower the volume by one step."""
    return with_message(
        _media_key(VK_VOLUME_DOWN, ["pactl", "set-sink-volume", "@DEFAULT_SINK@", "-5%"]),
        "Volume down.",
    )


def set_volume(level: str) -> CommandResult:
    """Set the system volume to a value from 0 to 100."""
    try:
        value = int(level)
    except ValueError:
        return CommandResult(success=False, error="Volume must be a whole number from 0 to 100.")
    if not 0 <= value <= 100:
        return CommandResult(success=False, error="Volume must be between 0 and 100.")
    if IS_WINDOWS:
        endpoint = _endpoint_volume()
        if endpoint is None:
            return missing_dependency("pycaw")
        endpoint.SetMasterVolumeLevelScalar(value / 100, None)
        return CommandResult(success=True, message=f"Volume set to {value}%.", data={"level": value})
    return with_message(
        run_command(["pactl", "set-sink-volume", "@DEFAULT_SINK@", f"{value}%"]),
        f"Volume set to {value}%.",
    )


def mute() -> CommandResult:
    """Mute the system audio."""
    return _set_mute(True)


def unmute() -> CommandResult:
    """Unmute the system audio."""
    return _set_mute(False)

# endregion
