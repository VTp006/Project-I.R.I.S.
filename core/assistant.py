from core.voice_input import listen
from core.voice_output import speak
from core.task_interpreter import interpret
from commands.executor import CommandExecutor
from commands.handlers import HANDLERS


executor = CommandExecutor()
executor.register_handlers(HANDLERS)


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

        commands = interpret(user_input)

        if not commands:
            speak("I couldn't understand that command.")
            continue

        for command in commands:
            result = executor.execute(
                command["name"],
                command["parameters"]
            )

            if result.success:
                response = result.message
            elif result.error == "CONFIRMATION_REQUIRED":
                response = result.message
            else:
                response = result.error or result.message

            print(f"iris: {response}")
            speak(response)