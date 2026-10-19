
# region Imports and Configuration

import os
import json

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

MODEL = "gemini-3.8-flash"
client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

SYSTEM_PROMPT = """
You are Iris, an AI assistant.

Your name is spoken as "iris". Never spell it as I.R.I.S. or I R I S.

Be helpful, natural, and concise.
Use plain text and normal punctuation.
Do not use markdown formatting.
Do not use emojis or decorative symbols.
Keep responses suitable for text-to-speech.
"""

# endregion


# region Plain Text Response

def ask(prompt: str, system_prompt: str = SYSTEM_PROMPT) -> str:
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.7,
        ),
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")

    return response.text.strip()

# endregion


# region Language-Segmented Response

def ask_segments(prompt: str) -> list[tuple[str, str]]:
    response = client.models.generate_content(
        model=MODEL,
        contents=prompt,
        config=types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT + """
Return a JSON array of speech segments.
Each segment must contain "language" and "text".
Use "hi" for Hindi, including Romanized Hindi.
Use "en" for English.
Preserve the original wording.
Keep segments as large and natural as possible.
Return JSON only.
""",
            response_mime_type="application/json",
            temperature=0.3,
        ),
    )

    if not response.text:
        raise RuntimeError("Gemini returned an empty response.")

    data = json.loads(response.text)

    segments = [
        (item["language"], item["text"])
        for item in data
        if item.get("language") in ("hi", "en")
        and isinstance(item.get("text"), str)
        and item["text"].strip()
    ]

    if not segments:
        raise RuntimeError("Gemini returned no valid language segments.")

    return segments

# endregion
