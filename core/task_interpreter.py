import json
import re

from api.ollama import ask
from commands.registry import (
    COMMAND_REGISTRY,
    CommandDomain,
    get_commands_by_domain,
)


DOMAIN_KEYWORDS = {
    CommandDomain.SYSTEM: {
        "shutdown", "shut down", "restart", "reboot", "sleep",
        "hibernate", "log out", "logout", "lock pc", "lock computer",
        "cancel shutdown", "cpu usage", "gpu usage", "ram usage",
        "disk usage", "battery", "os information", "system information",
    },
    CommandDomain.APPLICATIONS: {
        "open app", "open application", "close app", "close application",
        "launch app", "restart app", "minimize app", "maximize app",
        "focus app", "switch app", "install app", "uninstall app",
    },
    CommandDomain.BROWSER: {
        "browser", "website", "web page", "chrome", "google",
        "search google", "new tab", "close tab", "switch tab",
        "refresh page", "url", "bookmark", "download",
    },
    CommandDomain.AUDIO_MEDIA: {
        "volume", "mute", "unmute", "music", "song", "track",
        "play music", "pause music", "resume music", "video",
        "media",
    },
    CommandDomain.FILES: {
        "file", "folder", "directory", "document", "delete file",
        "create file", "read file", "rename file", "copy file",
        "move file", "compress", "extract", "recycle bin",
    },
    CommandDomain.WINDOWS: {
        "window", "desktop", "minimize window", "maximize window",
        "restore window", "move window", "resize window",
        "snap window", "show desktop",
    },
    CommandDomain.SCREEN_INPUT: {
        "screenshot", "screen record", "record screen", "keyboard",
        "type", "press key", "mouse", "click", "scroll", "drag",
    },
    CommandDomain.PRODUCTIVITY: {
        "note", "calendar", "reminder", "timer", "document",
    },
    CommandDomain.CLIPBOARD: {
        "clipboard", "copy", "paste",
    },
    CommandDomain.SEARCH_INFORMATION: {
        "search the web", "search web", "calculate", "date", "time",
        "weather", "news", "search pc", "search files",
    },
    CommandDomain.NETWORK: {
        "wifi", "wi-fi", "bluetooth", "network", "ping",
    },
    CommandDomain.HARDWARE: {
        "hardware", "temperature", "display", "microphone",
        "audio device", "cpu status", "gpu status", "ram status",
        "disk status",
    },
    CommandDomain.SECURITY: {
        "password", "firewall", "security", "processes",
    },
    CommandDomain.PROCESSES: {
        "process", "task", "kill process", "start process",
        "stop process",
    },
    CommandDomain.SOFTWARE: {
        "software", "install software", "uninstall software",
        "update software", "updates", "installed software",
    },
    CommandDomain.IRIS: {
        "wake word", "voice mode", "text mode", "sleep mode",
        "wake iris", "stop iris", "restart iris", "iris status",
    },
    CommandDomain.AI: {
        "explain", "summarize", "translate", "rewrite", "analyze",
        "generate", "ask ai", "artificial intelligence",
    },
    CommandDomain.AUTOMATION: {
        "automation", "sequence", "multi-step", "multi step",
    },
}


def _detect_domains(task: str) -> list[CommandDomain]:
    text = task.lower()
    matches = []

    for domain, keywords in DOMAIN_KEYWORDS.items():
        if any(keyword in text for keyword in keywords):
            matches.append(domain)

    return matches


def _build_command_reference(domains: list[CommandDomain]) -> str:
    commands = []

    for domain in domains:
        for command in get_commands_by_domain(domain):
            parameters = ", ".join(command.parameters)

            if parameters:
                commands.append(
                    f"{command.name}({parameters}) - {command.description}"
                )
            else:
                commands.append(
                    f"{command.name}() - {command.description}"
                )

    return "\n".join(commands)


def _build_system_prompt(command_reference: str) -> str:
    return f"""
You are the task interpreter for iris, a local AI assistant.

Convert the user's natural-language request into one or more commands
from the available command registry.

You MUST only use commands listed below.

Return ONLY valid JSON.
Do not use markdown.
Do not explain your answer.

Understand intent, not just exact command names.

Examples:

User: "restart my computer"
Output:
{{"commands":[{{"name":"RESTART","parameters":{{}}}}]}}

User: "reboot my PC"
Output:
{{"commands":[{{"name":"RESTART","parameters":{{}}}}]}}

User: "turn off my computer"
Output:
{{"commands":[{{"name":"SHUTDOWN","parameters":{{}}}}]}}

User: "log me out"
Output:
{{"commands":[{{"name":"LOG_OUT","parameters":{{}}}}]}}

User: "set the volume to 50"
Output:
{{"commands":[{{"name":"SET_VOLUME","parameters":{{"level":50}}}}]}}

User: "open chrome and set the volume to 50"
Output:
{{"commands":[
    {{"name":"OPEN_APP","parameters":{{"app":"chrome"}}}},
    {{"name":"SET_VOLUME","parameters":{{"level":50}}}}
]}}

If the request cannot be mapped to an available command, return:

{{"commands":[]}}

Available commands:

{command_reference}
"""


def interpret(task: str) -> list[dict]:
    if not task or not task.strip():
        return []

    task = task.strip()

    domains = _detect_domains(task)

    if not domains:
        domains = list(CommandDomain)

    command_reference = _build_command_reference(domains)
    system_prompt = _build_system_prompt(command_reference)

    prompt = f"""
User request:

{task}

Convert this request into the appropriate command or commands.
Return JSON only.
"""

    response = ask(prompt, system_prompt)

    try:
        data = json.loads(response)
    except json.JSONDecodeError:
        return []

    commands = data.get("commands")

    if not isinstance(commands, list):
        return []

    validated = []

    for item in commands:
        if not isinstance(item, dict):
            continue

        name = item.get("name")
        parameters = item.get("parameters", {})

        if not isinstance(name, str):
            continue

        command = COMMAND_REGISTRY.get(name.upper())

        if command is None:
            continue

        if not isinstance(parameters, dict):
            continue

        validated.append(
            {
                "name": command.name,
                "parameters": parameters,
            }
        )

    return validated
