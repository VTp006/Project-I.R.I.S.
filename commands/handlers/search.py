"""Search and information handlers.

Network features use lightweight HTTP through urllib and need no API keys:
DuckDuckGo instant answers, wttr.in for weather, and Google News RSS for news.
Web search returns instant answers only, not full result pages. CALCULATE
parses the expression into an AST and evaluates a whitelist. It never calls eval.
"""

from __future__ import annotations

import ast
import datetime
import json
import math
import operator
import os
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any

from commands.executor import CommandResult
from commands.handlers.files import search_path

USER_AGENT = "IRIS/1.0 (local assistant)"
MAX_EXPRESSION_LENGTH = 200
MAX_EXPONENT = 1000

_BINARY_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
}
_UNARY_OPS = {ast.UAdd: operator.pos, ast.USub: operator.neg}
_FUNCTIONS = {
    "sqrt": math.sqrt, "sin": math.sin, "cos": math.cos, "tan": math.tan,
    "log": math.log, "log10": math.log10, "abs": abs, "round": round,
}
_CONSTANTS = {"pi": math.pi, "e": math.e}


# region HELPERS

def _http_get(url: str, timeout: int = 10) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read()


def _evaluate(node: ast.AST) -> Any:
    """Evaluate a whitelisted arithmetic AST. Anything else raises ValueError."""
    if isinstance(node, ast.Expression):
        return _evaluate(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return node.value
    if isinstance(node, ast.BinOp) and type(node.op) in _BINARY_OPS:
        left = _evaluate(node.left)
        right = _evaluate(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > MAX_EXPONENT:
            raise ValueError("Exponent is too large.")
        return _BINARY_OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _UNARY_OPS:
        return _UNARY_OPS[type(node.op)](_evaluate(node.operand))
    if isinstance(node, ast.Name) and node.id in _CONSTANTS:
        return _CONSTANTS[node.id]
    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in _FUNCTIONS
        and not node.keywords
    ):
        return _FUNCTIONS[node.func.id](*[_evaluate(arg) for arg in node.args])
    raise ValueError("Unsupported part of the expression.")

# endregion


# region CALCULATION AND DATE

def calculate(expression: str) -> CommandResult:
    """Evaluate arithmetic such as '2 + 3 * 4', '2^10' or 'sqrt(144)'."""
    text = expression.strip().replace("^", "**")
    if not text or len(text) > MAX_EXPRESSION_LENGTH:
        return CommandResult(success=False, error="Expression is empty or too long.")
    try:
        value = _evaluate(ast.parse(text, mode="eval"))
    except ZeroDivisionError:
        return CommandResult(success=False, error="Division by zero.")
    except (ValueError, TypeError, SyntaxError, OverflowError) as exc:
        return CommandResult(success=False, error=f"Could not calculate that: {exc}")
    return CommandResult(success=True, message=f"{expression.strip()} = {value}", data=value)


def get_date() -> CommandResult:
    """Today's date."""
    today = datetime.date.today()
    return CommandResult(success=True, message=f"Today is {today:%A, %B %d, %Y}.", data=today.isoformat())


def get_time() -> CommandResult:
    """The current local time."""
    now = datetime.datetime.now()
    return CommandResult(success=True, message=f"The time is {now:%H:%M}.", data=now.strftime("%H:%M"))

# endregion


# region WEB INFORMATION

def web_search(query: str) -> CommandResult:
    """Look up an instant answer from DuckDuckGo, with a link to the full results page."""
    text = query.strip()
    if not text:
        return CommandResult(success=False, error="Search text cannot be empty.")
    search_url = "https://duckduckgo.com/?" + urllib.parse.urlencode({"q": text})
    params = urllib.parse.urlencode({"q": text, "format": "json", "no_html": 1, "skip_disambig": 1})
    try:
        body = json.loads(_http_get(f"https://api.duckduckgo.com/?{params}"))
    except (OSError, ValueError) as exc:
        return CommandResult(success=False, error=f"Web search failed: {exc}")
    answer = str(body.get("AbstractText") or body.get("Answer") or "")
    if not answer:
        return CommandResult(
            success=True,
            message=f"No instant answer for '{text}'. Full results: {search_url}",
            data={"search_url": search_url},
        )
    return CommandResult(
        success=True,
        message=answer,
        data={"source": body.get("AbstractURL", ""), "search_url": search_url},
    )


def weather(location: str) -> CommandResult:
    """Current weather for a place name, from wttr.in (no API key)."""
    place = location.strip()
    if not place:
        return CommandResult(success=False, error="Location cannot be empty.")
    try:
        body = json.loads(_http_get(f"https://wttr.in/{urllib.parse.quote(place)}?format=j1"))
        current = body["current_condition"][0]
    except (OSError, ValueError, KeyError, IndexError) as exc:
        return CommandResult(success=False, error=f"Could not get weather for '{place}': {exc}")
    description = current["weatherDesc"][0]["value"]
    data = {
        "location": place,
        "temp_c": current["temp_C"],
        "feels_like_c": current["FeelsLikeC"],
        "humidity": current["humidity"],
        "description": description,
    }
    message = (
        f"{place}: {description}, {current['temp_C']}°C "
        f"(feels like {current['FeelsLikeC']}°C), humidity {current['humidity']}%."
    )
    return CommandResult(success=True, message=message, data=data)


def news(topic: str) -> CommandResult:
    """Recent headlines for a topic, from Google News RSS (no API key)."""
    subject = topic.strip()
    if not subject:
        return CommandResult(success=False, error="Topic cannot be empty.")
    url = (
        "https://news.google.com/rss/search?q="
        + urllib.parse.quote(subject)
        + "&hl=en-US&gl=US&ceid=US:en"
    )
    try:
        root = ET.fromstring(_http_get(url))
    except (OSError, ET.ParseError) as exc:
        return CommandResult(success=False, error=f"Could not get news: {exc}")
    items = [
        {
            "title": (item.findtext("title") or "").strip(),
            "link": (item.findtext("link") or "").strip(),
            "published": (item.findtext("pubDate") or "").strip(),
        }
        for item in root.iter("item")
    ][:5]
    if not items:
        return CommandResult(success=True, message=f"No news found for '{subject}'.", data=[])
    return CommandResult(
        success=True,
        message=f"Found {len(items)} headline(s) for '{subject}'. Top story: {items[0]['title']}",
        data=items,
    )

# endregion


# region LOCAL SEARCH

def _home_search(query: str, want_dirs: bool) -> list[str]:
    return search_path(os.path.expanduser("~"), query, want_dirs)


def search_pc(query: str) -> CommandResult:
    """Search the home folder for files and folders whose names contain the text."""
    if not query.strip():
        return CommandResult(success=False, error="Search text cannot be empty.")
    files = _home_search(query, want_dirs=False)
    folders = _home_search(query, want_dirs=True)
    total = len(files) + len(folders)
    return CommandResult(
        success=True,
        message=f"Found {total} file(s) and folder(s) matching '{query.strip()}'.",
        data={"files": files, "folders": folders},
    )


def search_files(query: str) -> CommandResult:
    """Search the home folder for files whose names contain the text."""
    if not query.strip():
        return CommandResult(success=False, error="Search text cannot be empty.")
    files = _home_search(query, want_dirs=False)
    return CommandResult(success=True, message=f"Found {len(files)} file(s) matching '{query.strip()}'.", data=files)

# endregion
