"""AI command handlers using the shared Ollama integration."""

from __future__ import annotations

from api.ollama import ask
from commands.executor import CommandResult
from commands.handlers.files import read_file


MAX_INPUT_CHARS = 12_000


def _checked(text: str) -> tuple[str | None, CommandResult | None]:
    cleaned = text.strip()

    if not cleaned:
        return None, CommandResult(
            success=False,
            error="There is no text to work with.",
        )

    if len(cleaned) > MAX_INPUT_CHARS:
        cleaned = cleaned[:MAX_INPUT_CHARS]

    return cleaned, None


def _generate(
    prompt: str,
    system: str | None = None,
) -> CommandResult:
    try:
        response = ask(prompt, system)
    except Exception as exc:
        return CommandResult(
            success=False,
            error=f"Could not reach the local AI server: {exc}",
        )

    if not response:
        return CommandResult(
            success=False,
            error="The AI server returned an empty reply.",
        )

    return CommandResult(
        success=True,
        message=response,
        data=response,
    )


def ask_ai(prompt: str) -> CommandResult:
    text, error = _checked(prompt)

    if error:
        return error

    return _generate(text)


def ai_fallback(prompt: str) -> CommandResult:
    text, error = _checked(prompt)

    if error:
        return error

    return _generate(
        text,
        system="Answer helpfully and briefly. Say so if you are unsure.",
    )


def generate_text(prompt: str) -> CommandResult:
    text, error = _checked(prompt)

    if error:
        return error

    return _generate(
        text,
        system="Write the requested text. Output only the text.",
    )


def summarize(text: str) -> CommandResult:
    body, error = _checked(text)

    if error:
        return error

    return _generate(
        f"Summarize the following text in a few sentences:\n\n{body}"
    )


def explain(text: str) -> CommandResult:
    body, error = _checked(text)

    if error:
        return error

    return _generate(
        f"Explain the following in plain language:\n\n{body}"
    )


def translate(text: str, language: str) -> CommandResult:
    target = language.strip()

    if not target:
        return CommandResult(
            success=False,
            error="Say which language to translate into.",
        )

    body, error = _checked(text)

    if error:
        return error

    return _generate(
        f"Translate the following text into {target}. "
        f"Output only the translation:\n\n{body}"
    )


def rewrite(text: str, style: str) -> CommandResult:
    requested = style.strip()

    if not requested:
        return CommandResult(
            success=False,
            error="Say which style to rewrite in.",
        )

    body, error = _checked(text)

    if error:
        return error

    return _generate(
        f"Rewrite the following text in a {requested} style. "
        f"Output only the rewritten text:\n\n{body}"
    )


def analyze_text(text: str) -> CommandResult:
    body, error = _checked(text)

    if error:
        return error

    return _generate(
        "Analyze the following text. Cover the main points, "
        "the tone, and any errors or gaps:\n\n" + body
    )


def analyze_file(path: str) -> CommandResult:
    loaded = read_file(path)

    if not loaded.success:
        return loaded

    return analyze_text(loaded.data)