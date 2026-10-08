"""AI handlers, backed by a local Ollama server.

This module talks to Ollama's HTTP API with the standard library only. If the
project already has an Ollama client module, replace _generate() with a call to
it so there is one Ollama integration. Configure the server with:

    IRIS_OLLAMA_URL    default http://localhost:11434
    IRIS_OLLAMA_MODEL  default llama3.2
"""

from __future__ import annotations

import json
import os
import urllib.request

from commands.executor import CommandResult
from commands.handlers.files import read_file

OLLAMA_URL = os.environ.get("IRIS_OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("IRIS_OLLAMA_MODEL", "llama3.2")
MAX_INPUT_CHARS = 12_000
REQUEST_TIMEOUT = 120


# region CORE

def _generate(prompt: str, system: str | None = None) -> CommandResult:
    """Send one prompt to Ollama and return the reply. This is the only place that talks to Ollama."""
    payload: dict = {"model": OLLAMA_MODEL, "prompt": prompt, "stream": False}
    if system:
        payload["system"] = system
    request = urllib.request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=REQUEST_TIMEOUT) as response:
            body = json.loads(response.read().decode("utf-8"))
    except (OSError, ValueError) as exc:
        return CommandResult(success=False, error=f"Could not reach the local AI server at {OLLAMA_URL}: {exc}")
    reply = str(body.get("response", "")).strip()
    if not reply:
        return CommandResult(success=False, error="The AI server returned an empty reply.")
    return CommandResult(success=True, message=reply, data=reply)


def _checked(text: str) -> tuple[str | None, CommandResult | None]:
    """Return the text trimmed to the input limit, or an error when it is empty."""
    cleaned = text.strip()
    if not cleaned:
        return None, CommandResult(success=False, error="There is no text to work with.")
    if len(cleaned) > MAX_INPUT_CHARS:
        cleaned = cleaned[:MAX_INPUT_CHARS]
    return cleaned, None

# endregion


# region QUESTIONS AND GENERATION

def ask_ai(prompt: str) -> CommandResult:
    """Ask the AI a question."""
    text, error = _checked(prompt)
    if error:
        return error
    return _generate(text)


def ai_fallback(prompt: str) -> CommandResult:
    """General-purpose reply for requests no other command handles."""
    text, error = _checked(prompt)
    if error:
        return error
    return _generate(text, system="Answer helpfully and briefly. Say so if you are unsure.")


def generate_text(prompt: str) -> CommandResult:
    """Generate new text from a prompt."""
    text, error = _checked(prompt)
    if error:
        return error
    return _generate(text, system="Write the requested text. Output only the text.")

# endregion


# region TEXT TRANSFORMS

def summarize(text: str) -> CommandResult:
    """Summarise a passage in a few sentences."""
    body, error = _checked(text)
    if error:
        return error
    return _generate(f"Summarize the following text in a few sentences:\n\n{body}")


def explain(text: str) -> CommandResult:
    """Explain a passage or concept in plain language."""
    body, error = _checked(text)
    if error:
        return error
    return _generate(f"Explain the following in plain language:\n\n{body}")


def translate(text: str, language: str) -> CommandResult:
    """Translate a passage into the target language."""
    target = language.strip()
    if not target:
        return CommandResult(success=False, error="Say which language to translate into.")
    body, error = _checked(text)
    if error:
        return error
    return _generate(f"Translate the following text into {target}. Output only the translation:\n\n{body}")


def rewrite(text: str, style: str) -> CommandResult:
    """Rewrite a passage in the requested style, such as 'formal' or 'shorter'."""
    requested = style.strip()
    if not requested:
        return CommandResult(success=False, error="Say which style to rewrite in.")
    body, error = _checked(text)
    if error:
        return error
    return _generate(f"Rewrite the following text in a {requested} style. Output only the rewritten text:\n\n{body}")


def analyze_text(text: str) -> CommandResult:
    """Analyse a passage: main points, tone, and anything that looks wrong."""
    body, error = _checked(text)
    if error:
        return error
    return _generate(
        "Analyze the following text. Cover the main points, the tone, and any errors or gaps:\n\n" + body
    )


def analyze_file(path: str) -> CommandResult:
    """Read a text file with files.read_file and analyse its contents."""
    loaded = read_file(path)
    if not loaded.success:
        return loaded
    return analyze_text(loaded.data)

# endregion
