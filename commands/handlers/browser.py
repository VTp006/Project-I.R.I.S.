"""Browser handlers.

Opening sites and searches use the default browser through the webbrowser
module. Tabs, navigation and page actions send keyboard shortcuts to the focused
window through pyautogui, so the browser must be in front. Downloads run on a
background thread that can be cancelled. Bookmark lookup reads the Chrome or
Edge bookmark file.
"""

from __future__ import annotations

import datetime
import json
import os
import re
import threading
import urllib.parse
import urllib.request
import webbrowser
from typing import Iterator

from commands.executor import CommandResult
from commands.handlers.system import IS_WINDOWS, load_optional, missing_dependency, with_message
from commands.handlers.windows import get_window

DOWNLOAD_DIR = os.path.join(os.path.expanduser("~"), "Downloads")
CHUNK_SIZE = 64 * 1024

_download_lock = threading.Lock()
_download_cancel = threading.Event()
_download_active = False
_download_state: dict[str, str] = {}


# region HELPERS

def _normalize_url(url: str) -> str | None:
    """Return an http or https URL, adding https:// when the scheme is missing."""
    candidate = url.strip()
    if not re.match(r"^https?://", candidate, re.IGNORECASE):
        candidate = "https://" + candidate
    parsed = urllib.parse.urlparse(candidate)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return None
    return candidate


def _invalid_url(url: str) -> CommandResult:
    return CommandResult(success=False, error=f"'{url}' is not a valid web address.")


def _hotkey(*keys: str) -> CommandResult:
    """Send a keyboard shortcut to the focused window."""
    pyautogui = load_optional("pyautogui")
    if pyautogui is None:
        return missing_dependency("pyautogui")
    pyautogui.hotkey(*keys)
    return CommandResult(success=True, message="Done.")


def _switch_tab(tab: str) -> CommandResult:
    choice = tab.strip().lower()
    if choice.isdigit() and 1 <= int(choice) <= 9:
        return with_message(_hotkey("ctrl", choice), f"Switched to tab {choice}.")
    if choice == "next":
        return with_message(_hotkey("ctrl", "tab"), "Switched to the next tab.")
    if choice in ("previous", "prev"):
        return with_message(_hotkey("ctrl", "shift", "tab"), "Switched to the previous tab.")
    return CommandResult(
        success=False,
        error="Tabs can be chosen by position (1-9), 'next' or 'previous'. IRIS cannot read tab names.",
    )


def _iter_bookmarks(node: dict) -> Iterator[dict]:
    if node.get("type") == "url":
        yield node
    for child in node.get("children", []):
        yield from _iter_bookmarks(child)


def _bookmark_files() -> list[str]:
    home = os.path.expanduser("~")
    if IS_WINDOWS:
        local = os.environ.get("LOCALAPPDATA", os.path.join(home, "AppData", "Local"))
        return [
            os.path.join(local, "Google", "Chrome", "User Data", "Default", "Bookmarks"),
            os.path.join(local, "Microsoft", "Edge", "User Data", "Default", "Bookmarks"),
        ]
    return [
        os.path.join(home, ".config", "google-chrome", "Default", "Bookmarks"),
        os.path.join(home, ".config", "chromium", "Default", "Bookmarks"),
    ]

# endregion


# region WEBSITES AND SEARCH

def open_website(url: str) -> CommandResult:
    """Open a website in a new browser tab."""
    target = _normalize_url(url)
    if target is None:
        return _invalid_url(url)
    webbrowser.open_new_tab(target)
    return CommandResult(success=True, message=f"Opened {target}.", data={"url": target})


def close_website(url: str) -> CommandResult:
    """Close the current tab in the browser window whose title contains the site's host.

    This is best effort. Page titles do not always contain the host, and the
    shortcut closes whichever tab is active in that window.
    """
    target = _normalize_url(url)
    if target is None:
        return _invalid_url(url)
    host = urllib.parse.urlparse(target).hostname or ""
    window, error = get_window(host)
    if error is not None:
        return error
    try:
        window.activate()
    except Exception:
        pass
    closed = _hotkey("ctrl", "w")
    return with_message(closed, f"Sent close-tab to the browser window for {host}. Check the result.")


def google_search(query: str) -> CommandResult:
    """Search Google in a new browser tab."""
    text = query.strip()
    if not text:
        return CommandResult(success=False, error="Search text cannot be empty.")
    url = "https://www.google.com/search?q=" + urllib.parse.quote_plus(text)
    webbrowser.open_new_tab(url)
    return CommandResult(success=True, message=f"Searched Google for '{text}'.", data={"url": url})


def go_to_url(url: str) -> CommandResult:
    """Type a web address into the current tab's address bar and press Enter."""
    target = _normalize_url(url)
    if target is None:
        return _invalid_url(url)
    pyautogui = load_optional("pyautogui")
    if pyautogui is None:
        return missing_dependency("pyautogui")
    pyautogui.hotkey("ctrl", "l")
    pyautogui.write(target, interval=0.01)
    pyautogui.press("enter")
    return CommandResult(success=True, message=f"Navigating to {target}.", data={"url": target})


def search_website(query: str) -> CommandResult:
    """Use the page's find bar (Ctrl+F) to search the current page."""
    text = query.strip()
    if not text:
        return CommandResult(success=False, error="Search text cannot be empty.")
    pyautogui = load_optional("pyautogui")
    if pyautogui is None:
        return missing_dependency("pyautogui")
    pyautogui.hotkey("ctrl", "f")
    pyautogui.write(text, interval=0.01)
    pyautogui.press("enter")
    return CommandResult(success=True, message=f"Searching this page for '{text}'.")

# endregion


# region TABS AND NAVIGATION

def change_tab(tab: str) -> CommandResult:
    """Switch tab by position (1-9), or to 'next' or 'previous'."""
    return _switch_tab(tab)


def switch_tab(tab: str) -> CommandResult:
    """Switch tab by position (1-9), or to 'next' or 'previous'. Same as change_tab."""
    return _switch_tab(tab)


def new_tab() -> CommandResult:
    """Open a new blank tab."""
    return with_message(_hotkey("ctrl", "t"), "Opened a new tab.")


def close_tab() -> CommandResult:
    """Close the current tab."""
    return with_message(_hotkey("ctrl", "w"), "Closed the current tab.")


def reopen_tab() -> CommandResult:
    """Reopen the most recently closed tab."""
    return with_message(_hotkey("ctrl", "shift", "t"), "Reopened the last closed tab.")


def back() -> CommandResult:
    """Go back one page."""
    return with_message(_hotkey("alt", "left"), "Went back.")


def forward() -> CommandResult:
    """Go forward one page."""
    return with_message(_hotkey("alt", "right"), "Went forward.")


def refresh_page() -> CommandResult:
    """Reload the current page."""
    return with_message(_hotkey("f5"), "Refreshed the page.")

# endregion


# region DOWNLOADS

def _download_worker(url: str, path: str) -> None:
    global _download_active
    try:
        with urllib.request.urlopen(url, timeout=30) as response, open(path, "wb") as handle:
            while True:
                if _download_cancel.is_set():
                    handle.close()
                    os.remove(path)
                    _download_state["state"] = "stopped"
                    return
                chunk = response.read(CHUNK_SIZE)
                if not chunk:
                    break
                handle.write(chunk)
        _download_state["state"] = f"finished: {path}"
    except (OSError, ValueError) as exc:
        _download_state["state"] = f"failed: {exc}"
    finally:
        with _download_lock:
            _download_active = False


def download_file(url: str) -> CommandResult:
    """Download a file to the Downloads folder in the background. One download at a time."""
    global _download_active
    target = _normalize_url(url)
    if target is None:
        return _invalid_url(url)
    with _download_lock:
        if _download_active:
            return CommandResult(success=False, error="A download is already in progress. Stop it first.")
        _download_active = True
    try:
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        name = os.path.basename(urllib.parse.urlparse(target).path) or "download"
        path = os.path.join(DOWNLOAD_DIR, name)
        if os.path.exists(path):
            base, ext = os.path.splitext(name)
            path = os.path.join(DOWNLOAD_DIR, f"{base}_{datetime.datetime.now():%H%M%S}{ext}")
        _download_cancel.clear()
        _download_state["state"] = "running"
        threading.Thread(target=_download_worker, args=(target, path), daemon=True).start()
    except OSError as exc:
        with _download_lock:
            _download_active = False
        return CommandResult(success=False, error=f"Could not start the download: {exc}")
    return CommandResult(success=True, message=f"Downloading to {path} in the background.", data={"path": path})


def stop_download() -> CommandResult:
    """Cancel the download in progress and delete the partial file."""
    with _download_lock:
        active = _download_active
    if not active:
        return CommandResult(success=False, error="No download is in progress.")
    _download_cancel.set()
    return CommandResult(success=True, message="Stopping the download.")

# endregion


# region BOOKMARKS AND DATA

def bookmark_page() -> CommandResult:
    """Open the browser's bookmark dialog (Ctrl+D) for the current page. The user confirms it there."""
    return with_message(_hotkey("ctrl", "d"), "Opened the bookmark dialog. Confirm it in the browser.")


def open_bookmark(bookmark: str) -> CommandResult:
    """Open the first Chrome or Edge bookmark whose name contains the text."""
    needle = bookmark.strip().lower()
    if not needle:
        return CommandResult(success=False, error="Bookmark name cannot be empty.")
    for path in _bookmark_files():
        if not os.path.isfile(path):
            continue
        try:
            with open(path, "r", encoding="utf-8") as handle:
                tree = json.load(handle)
        except (OSError, ValueError):
            continue
        for root in tree.get("roots", {}).values():
            if not isinstance(root, dict):
                continue
            for item in _iter_bookmarks(root):
                name = str(item.get("name", ""))
                url = str(item.get("url", ""))
                if needle in name.lower() and url.startswith(("http://", "https://")):
                    webbrowser.open_new_tab(url)
                    return CommandResult(success=True, message=f"Opened bookmark '{name}'.", data={"url": url})
    return CommandResult(success=False, error=f"No Chrome or Edge bookmark matches '{bookmark}'.")


def clear_browser_data() -> CommandResult:
    """Open the browser's clear-browsing-data dialog. The executor confirms first, and the user picks what to clear."""
    return with_message(_hotkey("ctrl", "shift", "delete"), "Opened the clear browsing data dialog.")

# endregion
