"""File and folder handlers.

Deletion handlers do not ask for confirmation themselves. The executor refuses
DELETE_FILE, DELETE_FOLDER and EMPTY_RECYCLE_BIN unless confirmed=True.
"""

from __future__ import annotations

import datetime
import os
import shutil
import subprocess
import sys
import tarfile
import zipfile

from commands.executor import CommandResult
from commands.handlers.system import IS_WINDOWS, load_optional, run_command
from commands.handlers.windows import get_window

MAX_READ_BYTES = 1_000_000
MAX_RESULTS = 50
MAX_SCAN_ENTRIES = 200_000
OFFICE_TYPES = {"docx", "xlsx", "pptx", "pdf"}


# region HELPERS

def _resolve(path: str) -> str:
    """Turn user text into an absolute path, expanding ~ and removing stray quotes."""
    return os.path.abspath(os.path.expanduser(path.strip().strip('"').strip("'")))


def _check_name(name: str) -> str | None:
    """Return an error message if a bare file or folder name is unsafe, otherwise None."""
    cleaned = name.strip()
    if not cleaned or cleaned in (".", "..") or "/" in cleaned or "\\" in cleaned:
        return f"'{name}' is not a valid name."
    return None


def _format_size(num: float) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if num < 1024:
            return f"{num:.1f} {unit}"
        num /= 1024
    return f"{num:.1f} TB"


def _iso(timestamp: float) -> str:
    return datetime.datetime.fromtimestamp(timestamp).isoformat(timespec="seconds")


def _close_matching_window(name: str) -> CommandResult:
    window, error = get_window(name)
    if error is not None:
        return error
    try:
        window.close()
    except Exception as exc:
        return CommandResult(success=False, error=f"Could not close '{window.title}': {exc}")
    return CommandResult(success=True, message=f"Closed '{window.title}'.")


def open_with_default_app(path: str) -> CommandResult:
    """Open a file or folder with the operating system's default handler."""
    target = _resolve(path)
    if not os.path.exists(target):
        return CommandResult(success=False, error=f"Path does not exist: {target}")
    try:
        if IS_WINDOWS:
            os.startfile(target)
        else:
            opener = "open" if sys.platform == "darwin" else "xdg-open"
            if shutil.which(opener) is None:
                return CommandResult(success=False, error=f"'{opener}' is not available on this system.")
            subprocess.Popen([opener, target], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except OSError as exc:
        return CommandResult(success=False, error=f"Could not open {target}: {exc}")
    return CommandResult(success=True, message=f"Opened {target}.", data={"path": target})


def _delete_path(target: str) -> CommandResult:
    """Delete a file or folder. Uses the recycle bin when send2trash is installed."""
    name = os.path.basename(target)
    send2trash = load_optional("send2trash")
    if send2trash is not None:
        send2trash.send2trash(target)
        return CommandResult(success=True, message=f"Moved '{name}' to the recycle bin.", data={"path": target})
    if os.path.isdir(target) and not os.path.islink(target):
        shutil.rmtree(target)
    else:
        os.remove(target)
    return CommandResult(
        success=True,
        message=f"Permanently deleted '{name}'. Install send2trash to use the recycle bin instead.",
        data={"path": target},
    )


def search_path(root: str, query: str, want_dirs: bool) -> list[str]:
    """Find files or folders under root whose names contain query (case-insensitive).

    Hidden entries are skipped. The search stops after MAX_RESULTS matches or
    MAX_SCAN_ENTRIES entries, whichever comes first.
    """
    needle = query.strip().lower()
    results: list[str] = []
    scanned = 0
    for dirpath, dirnames, filenames in os.walk(root, onerror=lambda _error: None):
        dirnames[:] = [d for d in dirnames if not d.startswith(".")]
        for name in dirnames if want_dirs else filenames:
            scanned += 1
            if not name.startswith(".") and needle in name.lower():
                results.append(os.path.join(dirpath, name))
                if len(results) >= MAX_RESULTS:
                    return results
        if scanned >= MAX_SCAN_ENTRIES:
            break
    return results


def _search(query: str, want_dirs: bool, label: str) -> CommandResult:
    if not query.strip():
        return CommandResult(success=False, error="Search text cannot be empty.")
    matches = search_path(os.path.expanduser("~"), query, want_dirs)
    if matches:
        message = f"Found {len(matches)} {label}(s) matching '{query.strip()}'."
    else:
        message = f"No {label}s matching '{query.strip()}' were found."
    return CommandResult(success=True, message=message, data=matches)


def _safe_member_path(destination: str, member: str) -> str:
    """Return the full path for an archive entry, or raise if it escapes destination."""
    target = os.path.abspath(os.path.join(destination, member))
    if os.path.commonpath([destination, target]) != destination:
        raise ValueError(f"Archive entry escapes the destination folder: {member}")
    return target


def _transfer(source: str, destination: str, want_dir: bool, move: bool) -> CommandResult:
    """Copy or move a file or folder into destination (a folder or a full new path)."""
    src = _resolve(source)
    kind = "folder" if want_dir else "file"
    if not (os.path.isdir(src) if want_dir else os.path.isfile(src)):
        return CommandResult(success=False, error=f"Not a {kind}: {src}")
    dst = _resolve(destination)
    if os.path.isdir(dst):
        dst = os.path.join(dst, os.path.basename(src))
    if os.path.exists(dst):
        return CommandResult(success=False, error=f"Destination already exists: {dst}")
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    if move:
        shutil.move(src, dst)
    elif want_dir:
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)
    verb = "Moved" if move else "Copied"
    return CommandResult(success=True, message=f"{verb} to {dst}.", data={"destination": dst})


def _rename(path: str, new_name: str, want_dir: bool) -> CommandResult:
    target = _resolve(path)
    kind = "folder" if want_dir else "file"
    if not (os.path.isdir(target) if want_dir else os.path.isfile(target)):
        return CommandResult(success=False, error=f"Not a {kind}: {target}")
    error = _check_name(new_name)
    if error:
        return CommandResult(success=False, error=error)
    destination = os.path.join(os.path.dirname(target), new_name.strip())
    if os.path.exists(destination):
        return CommandResult(success=False, error=f"Already exists: {destination}")
    os.rename(target, destination)
    return CommandResult(success=True, message=f"Renamed to {new_name.strip()}.", data={"path": destination})


def _delete_checked(path: str, want_dir: bool) -> CommandResult:
    target = _resolve(path)
    kind = "folder" if want_dir else "file"
    if not (os.path.isdir(target) if want_dir else os.path.isfile(target)):
        return CommandResult(success=False, error=f"Not a {kind}: {target}")
    return _delete_path(target)

# endregion


# region OPEN AND CLOSE

def open_file(path: str) -> CommandResult:
    """Open a file in its default application."""
    target = _resolve(path)
    if not os.path.isfile(target):
        return CommandResult(success=False, error=f"Not a file: {target}")
    return open_with_default_app(target)


def close_file(path: str) -> CommandResult:
    """Close the window showing a file, matched by file name."""
    return _close_matching_window(os.path.basename(_resolve(path)))


def open_folder(path: str) -> CommandResult:
    """Open a folder in the file manager."""
    target = _resolve(path)
    if not os.path.isdir(target):
        return CommandResult(success=False, error=f"Not a folder: {target}")
    return open_with_default_app(target)


def close_folder(path: str) -> CommandResult:
    """Close the file manager window for a folder, matched by folder name."""
    return _close_matching_window(os.path.basename(_resolve(path)))

# endregion


# region CREATE, READ, EDIT

def create_file(path: str, type: str) -> CommandResult:
    """Create an empty text file. Use CREATE_DOCUMENT for Office and PDF files."""
    target = _resolve(path)
    extension = type.strip().lstrip(".").lower()
    if extension in OFFICE_TYPES:
        return CommandResult(success=False, error=f"Use CREATE_DOCUMENT to make a .{extension} file.")
    if extension and not os.path.splitext(target)[1]:
        target += "." + extension
    if os.path.exists(target):
        return CommandResult(success=False, error=f"Already exists: {target}")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    with open(target, "x", encoding="utf-8"):
        pass
    return CommandResult(success=True, message=f"Created {target}.", data={"path": target})


def read_file(path: str) -> CommandResult:
    """Read a text file. Files over 1 MB are refused. The text is returned as data."""
    target = _resolve(path)
    if not os.path.isfile(target):
        return CommandResult(success=False, error=f"Not a file: {target}")
    if os.path.getsize(target) > MAX_READ_BYTES:
        return CommandResult(success=False, error="File is larger than 1 MB and was not read.")
    with open(target, "r", encoding="utf-8", errors="replace") as handle:
        text = handle.read()
    return CommandResult(success=True, message=f"Read {len(text)} characters from {os.path.basename(target)}.", data=text)


def edit_file(path: str, content: str) -> CommandResult:
    """Replace a text file's contents. Writes to a temp file first, then swaps it in."""
    target = _resolve(path)
    if not os.path.isfile(target):
        return CommandResult(success=False, error=f"Not a file: {target}")
    temp = target + ".iris-tmp"
    with open(temp, "w", encoding="utf-8") as handle:
        handle.write(content)
    os.replace(temp, target)
    return CommandResult(success=True, message=f"Saved changes to {os.path.basename(target)}.", data={"path": target})


def create_folder(path: str) -> CommandResult:
    """Create a new folder, including missing parents. Refuses to overwrite."""
    target = _resolve(path)
    if os.path.exists(target):
        return CommandResult(success=False, error=f"Already exists: {target}")
    os.makedirs(target)
    return CommandResult(success=True, message=f"Created folder {target}.", data={"path": target})

# endregion


# region DELETE

def delete_file(path: str) -> CommandResult:
    """Delete a file. The executor has already confirmed this command."""
    return _delete_checked(path, want_dir=False)


def delete_folder(path: str) -> CommandResult:
    """Delete a folder and its contents. The executor has already confirmed this command."""
    return _delete_checked(path, want_dir=True)


def confirm_deletion() -> CommandResult:
    """Confirm a pending deletion.

    Deletions are confirmed through the executor, so no deletion is ever left
    pending. This reports that there is nothing to confirm.
    """
    return CommandResult(success=False, error="There is no pending deletion to confirm.")


def cancel_deletion() -> CommandResult:
    """Cancel a pending deletion. Nothing is ever left pending, so this reports that."""
    return CommandResult(success=False, error="There is no pending deletion to cancel.")

# endregion


# region RENAME, COPY, MOVE

def rename_file(path: str, new_name: str) -> CommandResult:
    """Rename a file in place."""
    return _rename(path, new_name, want_dir=False)


def rename_folder(path: str, new_name: str) -> CommandResult:
    """Rename a folder in place."""
    return _rename(path, new_name, want_dir=True)


def copy_file(source: str, destination: str) -> CommandResult:
    """Copy a file. If destination is a folder, the file is copied into it."""
    return _transfer(source, destination, want_dir=False, move=False)


def copy_folder(source: str, destination: str) -> CommandResult:
    """Copy a folder and its contents."""
    return _transfer(source, destination, want_dir=True, move=False)


def move_file(source: str, destination: str) -> CommandResult:
    """Move a file. If destination is a folder, the file is moved into it."""
    return _transfer(source, destination, want_dir=False, move=True)


def move_folder(source: str, destination: str) -> CommandResult:
    """Move a folder. If destination is a folder, the folder is moved into it."""
    return _transfer(source, destination, want_dir=True, move=True)

# endregion


# region SEARCH AND INFO

def search_file(query: str) -> CommandResult:
    """Search the home folder for files whose names contain query."""
    return _search(query, want_dirs=False, label="file")


def search_folder(query: str) -> CommandResult:
    """Search the home folder for folders whose names contain query."""
    return _search(query, want_dirs=True, label="folder")


def list_folder(path: str) -> CommandResult:
    """List up to 500 entries in a folder, folders first."""
    target = _resolve(path)
    if not os.path.isdir(target):
        return CommandResult(success=False, error=f"Not a folder: {target}")
    with os.scandir(target) as entries:
        ordered = sorted(entries, key=lambda e: (not e.is_dir(), e.name.lower()))[:500]
        listing = [{"name": e.name, "type": "folder" if e.is_dir() else "file"} for e in ordered]
    return CommandResult(success=True, message=f"{len(listing)} item(s) in {target}.", data=listing)


def get_file_info(path: str) -> CommandResult:
    """Size, dates and extension of a file."""
    target = _resolve(path)
    if not os.path.isfile(target):
        return CommandResult(success=False, error=f"Not a file: {target}")
    stat = os.stat(target)
    data = {
        "name": os.path.basename(target),
        "path": target,
        "size": stat.st_size,
        "size_readable": _format_size(stat.st_size),
        "modified": _iso(stat.st_mtime),
        "created": _iso(stat.st_ctime),
        "extension": os.path.splitext(target)[1],
    }
    return CommandResult(success=True, message=f"{data['name']} is {data['size_readable']}.", data=data)


def get_folder_info(path: str) -> CommandResult:
    """Item counts and total size of a folder, scanning at most MAX_SCAN_ENTRIES entries."""
    target = _resolve(path)
    if not os.path.isdir(target):
        return CommandResult(success=False, error=f"Not a folder: {target}")
    files = folders = total = 0
    capped = False
    for dirpath, dirnames, filenames in os.walk(target, onerror=lambda _error: None):
        folders += len(dirnames)
        files += len(filenames)
        for name in filenames:
            try:
                total += os.path.getsize(os.path.join(dirpath, name))
            except OSError:
                continue
        if files + folders >= MAX_SCAN_ENTRIES:
            capped = True
            break
    data = {
        "path": target,
        "files": files,
        "folders": folders,
        "size": total,
        "size_readable": _format_size(total),
        "capped": capped,
    }
    note = " (scan stopped early, so counts are partial)" if capped else ""
    message = f"{os.path.basename(target)} has {files} file(s), {folders} folder(s), {data['size_readable']}{note}."
    return CommandResult(success=True, message=message, data=data)

# endregion


# region COMPRESSION

def compress_file(path: str) -> CommandResult:
    """Zip a file or folder into a .zip next to it."""
    source = _resolve(path)
    if not os.path.exists(source):
        return CommandResult(success=False, error=f"Does not exist: {source}")
    archive = source.rstrip(os.sep) + ".zip"
    if os.path.exists(archive):
        return CommandResult(success=False, error=f"Archive already exists: {archive}")
    parent = os.path.dirname(source)
    with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as bundle:
        if os.path.isdir(source):
            for dirpath, _dirnames, filenames in os.walk(source):
                for name in filenames:
                    full = os.path.join(dirpath, name)
                    bundle.write(full, os.path.relpath(full, parent))
        else:
            bundle.write(source, os.path.basename(source))
    return CommandResult(success=True, message=f"Created {archive}.", data={"path": archive})


def extract_file(path: str, destination: str) -> CommandResult:
    """Extract a .zip, .tar, .tar.gz or .tgz archive. Entries that escape the destination are refused."""
    archive = _resolve(path)
    if not os.path.isfile(archive):
        return CommandResult(success=False, error=f"Not an archive file: {archive}")
    target_dir = _resolve(destination)
    os.makedirs(target_dir, exist_ok=True)
    try:
        if zipfile.is_zipfile(archive):
            with zipfile.ZipFile(archive) as bundle:
                for member in bundle.namelist():
                    _safe_member_path(target_dir, member)
                bundle.extractall(target_dir)
        elif tarfile.is_tarfile(archive):
            with tarfile.open(archive) as bundle:
                for member in bundle.getmembers():
                    _safe_member_path(target_dir, member.name)
                if hasattr(tarfile, "data_filter"):
                    bundle.extractall(target_dir, filter="data")
                else:
                    bundle.extractall(target_dir)
        else:
            return CommandResult(success=False, error="Unsupported archive. Use .zip, .tar, .tar.gz or .tgz.")
    except (ValueError, OSError, tarfile.TarError, zipfile.BadZipFile) as exc:
        return CommandResult(success=False, error=str(exc))
    return CommandResult(success=True, message=f"Extracted to {target_dir}.", data={"destination": target_dir})

# endregion


# region RECYCLE BIN

def empty_recycle_bin() -> CommandResult:
    """Empty the recycle bin. The executor has already confirmed this command."""
    if IS_WINDOWS:
        result = run_command(
            ["powershell", "-NoProfile", "-Command", "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"],
            timeout=120,
        )
        if result.success:
            result.message = "Recycle bin emptied."
        return result
    trash = os.path.join(os.path.expanduser("~"), ".local", "share", "Trash")
    removed = 0
    for sub in ("files", "info"):
        folder = os.path.join(trash, sub)
        if not os.path.isdir(folder):
            continue
        with os.scandir(folder) as entries:
            for entry in entries:
                if entry.is_dir(follow_symlinks=False):
                    shutil.rmtree(entry.path)
                else:
                    os.remove(entry.path)
                removed += 1
    return CommandResult(success=True, message=f"Recycle bin emptied ({removed} item(s) removed).", data={"removed": removed})

# endregion
