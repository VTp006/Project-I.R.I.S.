from ollama import chat

MODEL = "qwen3:4b"

SYSTEM_PROMPT = """
You are I.R.I.S. (Intelligent Response & Interactive System),
a local AI assistant.

Be helpful, natural, and concise.
Answer directly without unnecessary explanations.
"""

def ask(prompt: str) -> str:
    response = chat(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            },
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response.message.content.strip()