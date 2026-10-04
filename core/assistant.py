from core.voice_input import listen
from core.voice_output import speak
from api.ollama import ask


def run_assistant():
    speak("Hello, I am iris. How can I help you?")

    while True:
        user_input = listen()

        if not user_input:
            continue

        print(f"You: {user_input}")

        if user_input.lower() in ["exit", "quit", "goodbye", "stop"]:
            speak("Goodbye.")
            break

        response = ask(user_input)

        print(f"iris: {response}")

        speak(response)