import sounddevice as sd
import numpy as np
from faster_whisper import WhisperModel

SAMPLE_RATE = 16000
RECORD_SECONDS = 5

model = None


def _get_model():
    global model

    if model is None:
        model = WhisperModel(
            "base",
            device="cpu",
            compute_type="int8",
        )

    return model


def listen():
    print("Listening...")

    audio = sd.rec(
        int(RECORD_SECONDS * SAMPLE_RATE),
        samplerate=SAMPLE_RATE,
        channels=1,
        dtype="float32",
        blocking=True,
    )

    audio = np.squeeze(audio)

    print("Processing speech...")

    speech_model = _get_model()

    segments, _ = speech_model.transcribe(
        audio,
        language="en",
    )

    text = " ".join(
        segment.text for segment in segments
    ).strip()

    print(f"You said: {text}" if text else "No speech detected.")

    return text
