import json
import wave
from pathlib import Path

import numpy as np
import onnxruntime as ort
import sounddevice as sd
from piper import PiperVoice
from piper.config import PiperConfig


PIPER_MODEL = Path("models/piper/en_US-lessac-medium.onnx")
PIPER_CONFIG = Path("models/piper/en_US-lessac-medium.onnx.json")
OUTPUT_FILE = Path("data/temp/iris_voice.wav")

piper_voice = None


def _get_piper_voice():
    global piper_voice

    if piper_voice is None:
        with PIPER_CONFIG.open("r", encoding="utf-8") as file:
            config = PiperConfig.from_dict(json.load(file))

        options = ort.SessionOptions()
        options.intra_op_num_threads = 2
        options.inter_op_num_threads = 1

        session = ort.InferenceSession(
            str(PIPER_MODEL),
            sess_options=options,
            providers=["CPUExecutionProvider"],
        )

        piper_voice = PiperVoice(
            config=config,
            session=session,
        )

    return piper_voice


def speak(text: str):
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    voice = _get_piper_voice()

    with wave.open(str(OUTPUT_FILE), "wb") as wav_file:
        voice.synthesize_wav(text, wav_file)

    with wave.open(str(OUTPUT_FILE), "rb") as wf:
        sample_rate = wf.getframerate()
        channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        frames = wf.readframes(wf.getnframes())

    if sample_width != 2:
        raise ValueError(
            f"Unsupported WAV sample width: {sample_width} bytes"
        )

    audio = np.frombuffer(frames, dtype=np.int16)

    if channels > 1:
        audio = audio.reshape(-1, channels)

    sd.play(audio, sample_rate)
    sd.wait()

