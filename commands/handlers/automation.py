"""Automation handlers: sequences, multi-step tasks and saved automations.

Every step goes through the global executor with confirmed=False. So steps that
need confirmation are refused, and nothing can bypass the confirmation system.
Sequences are fully validated before the first step runs. Automation commands
cannot run inside another automation, which prevents uncontrolled recursion.
Saved automations are JSON files in ~/.iris/automations.
"""

from __future__ import annotations

import json
import os
import re
import threading
from typing import Any, Callable

from commands.executor import CommandResult, executor
from commands.registry import get_command

AUTOMATION_DIR = os.path.join(os.path.expanduser("~"), ".iris", "automations")
MAX_STEPS = 20
NAME_RE = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
NESTED_COMMANDS = {"EXECUTE_TASK", "RUN_SEQUENCE", "CREATE_AUTOMATION", "RUN_AUTOMATION", "STOP_AUTOMATION"}

_task_interpreter: Callable[[str], list[dict[str, Any]]] | None = None
_lock = threading.Lock()
_running: dict[str, threading.Event] = {}
_last_results: dict[str, CommandResult] = {}


# region INTEGRATION

def set_task_interpreter(interpreter: Callable[[str], list[dict[str, Any]]]) -> None:
    """Register the Task Interpreter. It turns a task description into {'command', 'parameters'} steps."""
    global _task_interpreter
    _task_interpreter = interpreter

# endregion


# region VALIDATION AND RUNNING

def _fail(message: str) -> CommandResult:
    return CommandResult(success=False, error=message)


def _validate_steps(raw: Any) -> tuple[list[dict[str, Any]] | None, CommandResult | None]:
    """Check every step before any runs. Returns (steps, None) or (None, error)."""
    if not isinstance(raw, list) or not raw:
        return None, _fail("A sequence must be a non-empty list of steps.")
    if len(raw) > MAX_STEPS:
        return None, _fail(f"A sequence can contain at most {MAX_STEPS} steps.")
    steps: list[dict[str, Any]] = []
    for index, step in enumerate(raw, 1):
        if not isinstance(step, dict) or "command" not in step:
            return None, _fail(f"Step {index} needs a 'command' field.")
        name = str(step["command"]).upper()
        parameters = step.get("parameters") or {}
        if not isinstance(parameters, dict):
            return None, _fail(f"Step {index} parameters must be an object.")
        if get_command(name) is None:
            return None, _fail(f"Step {index}: unknown command {name}.")
        if name in NESTED_COMMANDS:
            return None, _fail(f"Step {index}: {name} cannot run inside a sequence.")
        if executor.requires_confirmation(name):
            return None, _fail(f"Step {index} ({name}) needs confirmation, so it must be run on its own.")
        check = executor.validate_command(name, parameters)
        if not check.success:
            return None, _fail(f"Step {index}: {check.error}")
        steps.append({"command": name, "parameters": parameters})
    return steps, None


def _parse_and_validate(commands: str) -> tuple[list[dict[str, Any]] | None, CommandResult | None]:
    try:
        raw = json.loads(commands)
    except (TypeError, ValueError):
        return None, _fail('Commands must be a JSON list such as [{"command": "GET_DATE", "parameters": {}}].')
    return _validate_steps(raw)


def _run_steps(steps: list[dict[str, Any]], stop_event: threading.Event | None = None) -> CommandResult:
    """Run validated steps in order, stopping at the first failure or a stop request."""
    outcomes: list[dict[str, Any]] = []
    for index, step in enumerate(steps, 1):
        if stop_event is not None and stop_event.is_set():
            return CommandResult(success=False, error="Stopped by request.", data=outcomes)
        result = executor.execute(step["command"], step["parameters"], confirmed=False)
        outcomes.append({
            "step": index,
            "command": step["command"],
            "success": result.success,
            "detail": result.message or result.error,
        })
        if not result.success:
            return CommandResult(
                success=False,
                error=f"Step {index} ({step['command']}) failed: {result.error}",
                data=outcomes,
            )
    return CommandResult(success=True, message=f"Completed {len(outcomes)} step(s).", data=outcomes)


def _path(name: str) -> str:
    return os.path.join(AUTOMATION_DIR, name + ".json")

# endregion


# region TASKS AND SEQUENCES

def execute_task(task: str) -> CommandResult:
    """Plan a multi-step task with the registered interpreter, then run its steps."""
    if _task_interpreter is None:
        return _fail("The task interpreter is not connected, so multi-step tasks are unavailable.")
    try:
        raw = _task_interpreter(task)
    except Exception as exc:
        return _fail(f"Could not plan the task: {exc}")
    steps, error = _validate_steps(raw)
    if error is not None:
        return error
    return _run_steps(steps)


def run_sequence(commands: str) -> CommandResult:
    """Run a JSON list of commands in order. Every step is validated before any runs."""
    steps, error = _parse_and_validate(commands)
    if error is not None:
        return error
    return _run_steps(steps)

# endregion


# region SAVED AUTOMATIONS

def create_automation(name: str, commands: str) -> CommandResult:
    """Save a named automation after validating its steps."""
    key = name.strip()
    if not NAME_RE.match(key):
        return _fail("Names may use letters, numbers, dashes and underscores (up to 64 characters).")
    steps, error = _parse_and_validate(commands)
    if error is not None:
        return error
    os.makedirs(AUTOMATION_DIR, exist_ok=True)
    path = _path(key)
    if os.path.exists(path):
        return _fail(f"An automation called '{key}' already exists.")
    with open(path, "w", encoding="utf-8") as handle:
        json.dump({"name": key, "steps": steps}, handle, indent=2)
    return CommandResult(success=True, message=f"Saved automation '{key}' with {len(steps)} step(s).", data={"name": key})


def run_automation(name: str) -> CommandResult:
    """Start a saved automation on a background thread. Use STOP_AUTOMATION to cancel it."""
    key = name.strip()
    if not NAME_RE.match(key):
        return _fail("That is not a valid automation name.")
    path = _path(key)
    if not os.path.isfile(path):
        return _fail(f"No automation called '{key}'.")
    with open(path, "r", encoding="utf-8") as handle:
        saved = json.load(handle)
    steps, error = _validate_steps(saved.get("steps"))
    if error is not None:
        return error
    with _lock:
        if key in _running:
            return _fail(f"'{key}' is already running.")
        stop_event = threading.Event()
        _running[key] = stop_event

    def worker() -> None:
        try:
            outcome = _run_steps(steps, stop_event)
        except Exception as exc:
            outcome = _fail(str(exc))
        finally:
            with _lock:
                _running.pop(key, None)
        _last_results[key] = outcome

    threading.Thread(target=worker, name=f"automation-{key}", daemon=True).start()
    return CommandResult(success=True, message=f"Started automation '{key}' in the background.", data={"name": key})


def stop_automation(name: str) -> CommandResult:
    """Ask a running automation to stop before its next step."""
    key = name.strip()
    with _lock:
        stop_event = _running.get(key)
    if stop_event is None:
        return _fail(f"'{key}' is not running.")
    stop_event.set()
    return CommandResult(success=True, message=f"Stopping '{key}' after the current step.")


def list_automations() -> CommandResult:
    """Names of all saved automations."""
    if not os.path.isdir(AUTOMATION_DIR):
        return CommandResult(success=True, message="No automations saved yet.", data=[])
    names = sorted(f[:-5] for f in os.listdir(AUTOMATION_DIR) if f.endswith(".json"))
    return CommandResult(success=True, message=f"{len(names)} automation(s) saved.", data=names)

# endregion
