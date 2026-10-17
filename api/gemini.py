import os
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

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))


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