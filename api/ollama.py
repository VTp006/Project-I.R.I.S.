from ollama import chat

MODEL = "qwen3:1.7b"

SYSTEM_PROMPT = """
You are Iris, a local AI assistant.

Your name is spoken as "iris". Never spell it as I.R.I.S. or I R I S.

Be helpful, natural, and concise.
Use plain text and normal punctuation.
Do not use markdown formatting.
Do not use emojis or decorative symbols.
Keep responses suitable for text-to-speech.
"""


def ask(prompt: str, system_prompt: str = SYSTEM_PROMPT) -> str:
    response = chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": system_prompt,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )

    return response.message.content.strip()