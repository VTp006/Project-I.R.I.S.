"""Screen and input handlers.

Screenshots use pyautogui, or Pillow's ImageGrab when pyautogui is missing.
Screen recording runs ffmpeg in the background. Keyboard and mouse input use
pyautogui. Key names are checked against pyautogui's list before use.
pyautogui's failsafe is on: moving the mouse into a screen corner aborts input.
"""

from __future__ import annotations

import datetime
import os
import re
import shutil
import subprocess
from typing import Any

from commands.executor import CommandResult
from commands.handlers.system import IS_WINDOWS, load_optional, missing_dependency
from commands.handlers.windows import get_window

PICTURES_DIR = os.path.join(os.path.expanduser("~"), "Pictures", "IRIS")
VIDEO_DIR = os.path.join(os.path.expanduser("~"), "Videos", "IRIS")
MAX_TEXT_LENGTH = 2000
MAX_KEYS = 4

_recorder: subprocess.Popen | None = None
_recording_path: str | None = None


# region HELPERS

def _stamp() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def _grab(region: tuple[int, int, int, int] | None) -> Any:
    """Capture the screen, or a region given as (x, y, width, height)."""
    pyautogui = load_optional("pyautogui")
    if pyautogui is not None:
        return pyautogui.screenshot(region=region)
    try:
        from PIL import ImageGrab
    except ImportError:
        return None
    bbox = None
    if region is not None:
        x, y, w, h = region
        bbox = (x, y, x + w, y + h)
    return ImageGrab.grab(bbox=bbox)


def _save_screenshot(image: Any, label: str) -> CommandResult:
    if image is None:
        return CommandResult(success=False, error="Screenshots need the 'pyautogui' or 'Pillow' package.")
    os.makedirs(PICTURES_DIR, exist_ok=True)
    path = os.path.join(PICTURES_DIR, f"{label}_{_stamp()}.png")
    image.save(path)
    return CommandResult(success=True, message=f"Screenshot saved to {path}.", data={"path": path})


def _ints(text: str, count: int) -> list[int] | None:
    """Parse exactly count whole numbers from text such as '100,200' or '100 200'."""
    parts = [p for p in re.split(r"[,\s]+", text.strip()) if p]
    if len(parts) != count:
        return None
    try:
        return [int(p) for p in parts]
    except ValueError:
        return None


def _pyautogui_or_error():
    pyautogui = load_optional("pyautogui")
    return pyautogui, (missing_dependency("pyautogui") if pyautogui is None else None)


def _check_on_screen(pyautogui: Any, x: int, y: int) -> CommandResult | None:
    width, height = pyautogui.size()
    if not (0 <= x < width and 0 <= y < height):
        return CommandResult(success=False, error=f"({x}, {y}) is outside the screen ({width} x {height}).")
    return None

# endregion


# region SCREENSHOTS

def screenshot() -> CommandResult:
    """Take a screenshot of the full screen and save it to Pictures/IRIS."""
    return _save_screenshot(_grab(None), "screenshot")


def screenshot_full() -> CommandResult:
    """Take a full-screen screenshot. Same action as screenshot."""
    return _save_screenshot(_grab(None), "fullscreen")


def screenshot_window(window: str) -> CommandResult:
    """Screenshot the area of the window whose title contains the text."""
    found, error = get_window(window)
    if error is not None:
        return error
    region = (int(found.left), int(found.top), int(found.width), int(found.height))
    return _save_screenshot(_grab(region), "window")


def screenshot_region(region: str) -> CommandResult:
    """Screenshot a region given as 'x,y,width,height'."""
    values = _ints(region, 4)
    if values is None or values[2] <= 0 or values[3] <= 0:
        return CommandResult(success=False, error="Region must be 'x,y,width,height' with a positive size.")
    return _save_screenshot(_grab(tuple(values)), "region")

# endregion


# region SCREEN RECORDING

def screen_record() -> CommandResult:
    """Start recording the screen with ffmpeg. Saves an .mp4 to Videos/IRIS."""
    global _recorder, _recording_path
    if _recorder is not None and _recorder.poll() is None:
        return CommandResult(success=False, error="A screen recording is already running.")
    if shutil.which("ffmpeg") is None:
        return CommandResult(success=False, error="Screen recording needs ffmpeg installed and on PATH.")
    os.makedirs(VIDEO_DIR, exist_ok=True)
    path = os.path.join(VIDEO_DIR, f"recording_{_stamp()}.mp4")
    if IS_WINDOWS:
        source = ["-f", "gdigrab", "-framerate", "15", "-i", "desktop"]
    else:
        source = ["-f", "x11grab", "-framerate", "15", "-i", os.environ.get("DISPLAY", ":0")]
    _recorder = subprocess.Popen(
        ["ffmpeg", "-y", *source, path],
        stdin=subprocess.PIPE,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    _recording_path = path
    return CommandResult(success=True, message="Screen recording started.", data={"path": path})


def stop_screen_record() -> CommandResult:
    """Stop the recording. Sends 'q' to ffmpeg so the file is finalised properly."""
    global _recorder
    if _recorder is None or _recorder.poll() is not None:
        _recorder = None
        return CommandResult(success=False, error="No screen recording is running.")
    try:
        _recorder.communicate(input=b"q", timeout=20)
    except subprocess.TimeoutExpired:
        _recorder.kill()
        _recorder.communicate()
    path = _recording_path
    _recorder = None
    return CommandResult(success=True, message=f"Screen recording saved to {path}.", data={"path": path})

# endregion


# region KEYBOARD

def type_text(text: str) -> CommandResult:
    """Type text into the focused window. Non-ASCII characters may not type reliably."""
    if not text:
        return CommandResult(success=False, error="Nothing to type.")
    if len(text) > MAX_TEXT_LENGTH:
        return CommandResult(success=False, error=f"Text is longer than {MAX_TEXT_LENGTH} characters.")
    pyautogui, error = _pyautogui_or_error()
    if error is not None:
        return error
    pyautogui.write(text, interval=0.02)
    return CommandResult(success=True, message=f"Typed {len(text)} character(s).")


def press_key(key: str) -> CommandResult:
    """Press one key by its pyautogui name, such as 'enter' or 'f5'."""
    pyautogui, error = _pyautogui_or_error()
    if error is not None:
        return error
    name = key.strip().lower()
    if name not in pyautogui.KEYBOARD_KEYS:
        return CommandResult(success=False, error=f"'{key}' is not a recognised key name.")
    pyautogui.press(name)
    return CommandResult(success=True, message=f"Pressed {name}.")


def press_keys(keys: str) -> CommandResult:
    """Press a key combination such as 'ctrl+shift+t'. Separate keys with +, commas or spaces."""
    pyautogui, error = _pyautogui_or_error()
    if error is not None:
        return error
    names = [k for k in re.split(r"[+,\s]+", keys.strip().lower()) if k]
    if not names or len(names) > MAX_KEYS:
        return CommandResult(success=False, error=f"Give between 1 and {MAX_KEYS} keys.")
    unknown = [k for k in names if k not in pyautogui.KEYBOARD_KEYS]
    if unknown:
        return CommandResult(success=False, error=f"Unrecognised key name(s): {', '.join(unknown)}.")
    pyautogui.hotkey(*names)
    return CommandResult(success=True, message=f"Pressed {'+'.join(names)}.")

# endregion


# region MOUSE

def mouse_click(button: str) -> CommandResult:
    """Click the mouse button: left, right or middle."""
    name = button.strip().lower()
    if name not in ("left", "right", "middle"):
        return CommandResult(success=False, error="Button must be left, right or middle.")
    pyautogui, error = _pyautogui_or_error()
    if error is not None:
        return error
    pyautogui.click(button=name)
    return CommandResult(success=True, message=f"Clicked the {name} button.")


def mouse_move(x: str, y: str) -> CommandResult:
    """Move the mouse to screen coordinates (x, y)."""
    try:
        px, py = int(x), int(y)
    except ValueError:
        return CommandResult(success=False, error="x and y must be whole numbers.")
    pyautogui, error = _pyautogui_or_error()
    if error is not None:
        return error
    bounds_error = _check_on_screen(pyautogui, px, py)
    if bounds_error is not None:
        return bounds_error
    pyautogui.moveTo(px, py, duration=0.2)
    return CommandResult(success=True, message=f"Moved the mouse to {px}, {py}.")


def scroll(amount: str) -> CommandResult:
    """Scroll the mouse wheel. Positive scrolls up, negative scrolls down."""
    try:
        steps = int(amount)
    except ValueError:
        return CommandResult(success=False, error="Scroll amount must be a whole number.")
    pyautogui, error = _pyautogui_or_error()
    if error is not None:
        return error
    pyautogui.scroll(steps)
    return CommandResult(success=True, message=f"Scrolled {steps}.")


def drag(start: str, end: str) -> CommandResult:
    """Drag with the left button from start to end. Each point is 'x,y'."""
    origin = _ints(start, 2)
    target = _ints(end, 2)
    if origin is None or target is None:
        return CommandResult(success=False, error="start and end must each be 'x,y'.")
    pyautogui, error = _pyautogui_or_error()
    if error is not None:
        return error
    for x, y in (origin, target):
        bounds_error = _check_on_screen(pyautogui, x, y)
        if bounds_error is not None:
            return bounds_error
    pyautogui.moveTo(origin[0], origin[1], duration=0.2)
    pyautogui.dragTo(target[0], target[1], duration=0.3, button="left")
    return CommandResult(success=True, message="Dragged the mouse.")

# endregion
