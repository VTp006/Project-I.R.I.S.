"""Productivity handlers: notes, documents, calendar, reminders and timers.

Notes are plain text files in ~/.iris/notes and need no cloud service.
Reminders and timers run in memory for the current IRIS session. The notifier
can be replaced with set_notifier() so the main app can speak or display them.
"""

from __future__ import annotations

import datetime
import os
import re
import threading
import webbrowser
from typing import Callable

from commands.executor import CommandResult
from commands.handlers.files import create_file, open_with_default_app
from commands.handlers.system import IS_WINDOWS, load_optional, missing_dependency

NOTES_DIR = os.path.join(os.path.expanduser("~"), ".iris", "notes")
NAME_RE = re.compile(r"^[A-Za-z0-9 _.\-]{1,64}$")
DURATION_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(hours?|hrs?|h|minutes?|mins?|m|seconds?|secs?|s)(?![a-z])",
    re.IGNORECASE,
)
UNIT_SECONDS = {"h": 3600, "m": 60, "s": 1}

_lock = threading.Lock()
_timers: list[threading.Timer] = []


def _default_notifier(message: str) -> None:
    print(f"[IRIS] {message}")


_notifier: Callable[[str], None] = _default_notifier


# region HELPERS

def set_notifier(notifier: Callable[[str], None]) -> None:
    """Replace how timer and reminder messages are delivered, for example to speak them."""
    global _notifier
    _notifier = notifier


def _notify(message: str) -> None:
    _notifier(message)


def parse_duration(text: str) -> float | None:
    """Parse durations such as '10 minutes', '1h30m', 'in 2 hours' or '90 seconds'. Returns seconds."""
    cleaned = re.sub(r"^(in|for)\s+", "", text.strip().lower())
    matches = DURATION_RE.findall(cleaned)
    if not matches:
        return None
    leftover = DURATION_RE.sub("", cleaned).replace("and", "").replace(",", "").strip()
    if leftover:
        return None
    return sum(float(value) * UNIT_SECONDS[unit[0]] for value, unit in matches)


def parse_when(text: str) -> datetime.datetime | None:
    """Parse 'YYYY-MM-DD HH:MM' or 'HH:MM'. A past 'HH:MM' means tomorrow."""
    value = text.strip()
    try:
        return datetime.datetime.strptime(value, "%Y-%m-%d %H:%M")
    except ValueError:
        pass
    try:
        clock = datetime.datetime.strptime(value, "%H:%M")
    except ValueError:
        return None
    now = datetime.datetime.now()
    when = now.replace(hour=clock.hour, minute=clock.minute, second=0, microsecond=0)
    if when <= now:
        when += datetime.timedelta(days=1)
    return when


def _schedule(seconds: float, notice: str, success_text: str) -> CommandResult:
    timer = threading.Timer(seconds, _notify, args=(notice,))
    timer.daemon = True
    timer.start()
    with _lock:
        _timers[:] = [t for t in _timers if t.is_alive()]
        _timers.append(timer)
    return CommandResult(success=True, message=success_text, data={"seconds": round(seconds)})


def _note_path(name: str) -> str | None:
    key = name.strip()
    if not NAME_RE.match(key):
        return None
    return os.path.join(NOTES_DIR, key + ".txt")


def _with_extension(path: str, extension: str) -> str:
    target = os.path.abspath(os.path.expanduser(path.strip()))
    if not os.path.splitext(target)[1]:
        target += "." + extension
    return target

# endregion


# region NOTES

def create_note(content: str) -> CommandResult:
    """Save a new note with a timestamp name and return that name."""
    os.makedirs(NOTES_DIR, exist_ok=True)
    name = f"note-{datetime.datetime.now():%Y%m%d-%H%M%S}"
    path = _note_path(name)
    if path is None or os.path.exists(path):
        return CommandResult(success=False, error="A note with that timestamp already exists. Try again.")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)
    return CommandResult(success=True, message=f"Saved note '{name}'.", data={"name": name})


def read_note(name: str) -> CommandResult:
    """Return the text of a note."""
    path = _note_path(name)
    if path is None or not os.path.isfile(path):
        return CommandResult(success=False, error=f"No note called '{name}'.")
    with open(path, "r", encoding="utf-8") as handle:
        text = handle.read()
    return CommandResult(success=True, message=f"Note '{name.strip()}' has {len(text)} characters.", data=text)


def edit_note(name: str, content: str) -> CommandResult:
    """Replace the text of an existing note."""
    path = _note_path(name)
    if path is None or not os.path.isfile(path):
        return CommandResult(success=False, error=f"No note called '{name}'.")
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)
    return CommandResult(success=True, message=f"Updated note '{name.strip()}'.")


def delete_note(name: str) -> CommandResult:
    """Delete a note. The executor has already confirmed this command."""
    path = _note_path(name)
    if path is None or not os.path.isfile(path):
        return CommandResult(success=False, error=f"No note called '{name}'.")
    os.remove(path)
    return CommandResult(success=True, message=f"Deleted note '{name.strip()}'.")

# endregion


# region DOCUMENTS AND CALENDAR

def open_document(path: str) -> CommandResult:
    """Open a document in its default application."""
    return open_with_default_app(path)


def create_document(path: str, type: str) -> CommandResult:
    """Create a document. Text formats are created directly. .docx needs python-docx."""
    extension = type.strip().lstrip(".").lower()
    if extension == "docx":
        docx = load_optional("docx")
        if docx is None:
            return missing_dependency("python-docx")
        target = _with_extension(path, "docx")
        if os.path.exists(target):
            return CommandResult(success=False, error=f"Already exists: {target}")
        document = docx.Document()
        document.save(target)
        return CommandResult(success=True, message=f"Created {target}.", data={"path": target})
    return create_file(path, extension)


def open_calendar() -> CommandResult:
    """Open Outlook's calendar on Windows if it is registered, otherwise Google Calendar in the browser."""
    if IS_WINDOWS:
        try:
            os.startfile("outlookcal:")
            return CommandResult(success=True, message="Opened the calendar.")
        except OSError:
            pass
    webbrowser.open_new_tab("https://calendar.google.com")
    return CommandResult(success=True, message="Opened Google Calendar in your browser.")

# endregion


# region REMINDERS AND TIMERS

def create_reminder(text: str, time: str) -> CommandResult:
    """Set a reminder for a time ('HH:MM', 'YYYY-MM-DD HH:MM') or a duration ('10 minutes')."""
    note = text.strip()
    if not note:
        return CommandResult(success=False, error="Reminder text cannot be empty.")
    when = parse_when(time)
    if when is not None:
        seconds = (when - datetime.datetime.now()).total_seconds()
        success_text = f"Reminder set for {when:%Y-%m-%d %H:%M}."
    else:
        seconds = parse_duration(time)
        success_text = f"Reminder set in {round(seconds)} seconds." if seconds else ""
    if seconds is None or seconds <= 0:
        return CommandResult(
            success=False,
            error="I could not understand that time. Use HH:MM, YYYY-MM-DD HH:MM, or a duration like '10 minutes'.",
        )
    return _schedule(seconds, f"Reminder: {note}", success_text)


def set_timer(duration: str) -> CommandResult:
    """Start a timer for a duration such as '5 minutes' or '1h30m'."""
    seconds = parse_duration(duration)
    if seconds is None or seconds <= 0:
        return CommandResult(
            success=False,
            error="I could not understand that duration. Try '10 minutes' or '1h30m'.",
        )
    return _schedule(seconds, f"Your timer for {duration.strip()} is done.", f"Timer set for {duration.strip()}.")


def cancel_timer() -> CommandResult:
    """Cancel all active timers and reminders."""
    with _lock:
        active = [t for t in _timers if t.is_alive()]
        for timer in active:
            timer.cancel()
        _timers.clear()
    return CommandResult(success=True, message=f"Cancelled {len(active)} timer(s) or reminder(s).", data={"cancelled": len(active)})

# endregion
