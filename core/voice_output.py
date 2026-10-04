import subprocess
from pathlib import Path


PIPER_MODEL = Path("models/piper/en_US-lessac-medium.onnx")
OUTPUT_FILE = Path("data/temp/iris_voice.wav")


def speak(text: str):
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            "python",
            "-m",
            "piper",
            "-m",
            str(PIPER_MODEL),
            "-f",
            str(OUTPUT_FILE),
        ],
        input=text,
        text=True,
        check=True,
    )

    subprocess.run(
        ["powershell", "-c", f'(New-Object Media.SoundPlayer "{OUTPUT_FILE}").PlaySync()'],
        check=True,
    )