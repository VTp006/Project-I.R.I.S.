# IRIS command handlers

This package contains the real handler functions for every command in
`commands/registry.py` (194 commands, 18 domains). It does not replace the
Task Interpreter, the executor, or the registry.

```
User request -> Task Interpreter -> command(s) -> CommandExecutor -> handler -> OS/app -> CommandResult -> IRIS reply
```

## Layout

One module per domain. Each handler name is the command name in lower case,
and its parameters match the registry exactly.

| Module | Domain |
|---|---|
| files.py | FILES |
| applications.py | APPLICATIONS |
| browser.py | BROWSER |
| windows.py | WINDOWS |
| system.py | SYSTEM (also holds shared helpers) |
| audio.py | AUDIO_MEDIA |
| screen.py | SCREEN_INPUT |
| productivity.py | PRODUCTIVITY |
| clipboard.py | CLIPBOARD |
| search.py | SEARCH_INFORMATION |
| network.py | NETWORK |
| hardware.py | HARDWARE |
| security.py | SECURITY |
| processes.py | PROCESSES |
| software.py | SOFTWARE |
| iris.py | IRIS |
| ai.py | AI |
| automation.py | AUTOMATION |

`__init__.py` defines `HANDLERS`, a dictionary from every command name to its handler.

## Registering

```python
from commands.executor import executor
from commands.handlers import HANDLERS

executor.register_handlers(HANDLERS)
assert executor.get_missing_handlers() == []
```

## Integration points

These are the places where the main app connects to the handlers.

- `iris.set_iris_controller(controller)`: the object that owns the voice loop
  and settings. Its methods are listed in the module docstring. Without it,
  IRIS commands return "IRIS controller is not connected yet."
- `automation.set_task_interpreter(fn)`: `fn(task_text)` returns a list of
  `{"command": ..., "parameters": {...}}` steps. Without it, EXECUTE_TASK fails.
- `productivity.set_notifier(fn)`: `fn(message)` delivers timer and reminder
  messages. The default prints to the console.
- `ai.py` talks to a local Ollama server over HTTP. If the project already has
  an Ollama client, replace `_generate()` so there is only one integration.

## Safety rules

- Handlers never bypass the executor's confirmation. Commands marked
  `requires_confirmation` or `dangerous` are refused unless `confirmed=True`,
  and handlers do not ask a second time.
- No handler passes user text to a shell. Every system call uses a fixed program
  with an argument list. Host names, Wi-Fi names and package names are validated.
- CALCULATE parses an AST and evaluates a whitelist. It never calls `eval`.
- Automations run every step through the executor with `confirmed=False`, so
  confirmation-required steps are refused. Automation commands cannot nest.
- Protected processes (PIDs 0-4, IRIS itself, core OS processes) are never stopped.
- Passwords are never received, stored or displayed. CHANGE_PASSWORD opens the OS settings.
- Archive extraction refuses entries that would leave the destination folder.
- No API keys are stored. Weather, news and web search use keyless public endpoints.

## Optional dependencies

The package imports without any of these. A feature that needs a missing package
returns a clear error that names the package to install.

| Package | Used for |
|---|---|
| psutil | CPU, RAM, battery, processes, network interfaces, temperatures |
| pyautogui | Screenshots, keyboard, mouse, clipboard copy/paste, browser shortcuts |
| pygetwindow | Window control (minimize, focus, move, close) |
| pyperclip | Reading and writing clipboard text |
| send2trash | Recycle-bin deletion (otherwise deletion is permanent) |
| pycaw | Exact volume and mute on Windows |
| screeninfo | Display information |
| pyaudio | Microphone check |
| python-docx | CREATE_DOCUMENT with .docx |
| Pillow | Screenshot fallback on Windows |

External programs: winget or apt, nvidia-smi, ffmpeg (screen recording),
playerctl and pactl (Linux media), nmcli and rfkill (Linux network), ufw (Linux firewall).

## Known limitations

- CONFIRM_DELETION and CANCEL_DELETION report that nothing is pending. Deletions are
  confirmed through the executor before the handler runs, so no pending state exists.
- Pause and resume are toggles on Windows (one media key). On Linux they use playerctl.
- CLOSE_WEBSITE is best effort: the browser closes its active tab, which may not be the site.
- CHANGE_TAB and SWITCH_TAB accept positions 1-9, next and previous. Tab names are not readable.
- CLIPBOARD_HISTORY is unavailable. Windows keeps it, and IRIS cannot read it.
- Reminders and timers live in memory and do not survive a restart.
- Web search returns instant answers only, not full result pages.
- Windows-only paths (netsh, PowerShell, pycaw, keybd_event, os.startfile, Bluetooth
  PnP cmdlets) were written for Windows but could not be executed in the Linux
  build environment. Test them on Windows before relying on them.
- Bluetooth and firewall changes on Windows usually need an elevated (administrator) IRIS.
- Screen recording requires ffmpeg. Its arguments were not tested on either platform.
