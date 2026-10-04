# I.R.I.S. Models

This folder contains the local AI models required by I.R.I.S.

## Piper TTS

I.R.I.S. uses Piper as its primary offline text-to-speech engine.

### Voice Model

```text
en_US-lessac-medium
```

The model files are intentionally excluded from Git because they are large binary files.

### Download

From the project root, run:

```powershell
python -m piper.download_voices en_US-lessac-medium --data-dir models/piper
```

The downloaded files will be stored in:

```text
models/piper/
```

### Current Models

| Model                     | Purpose        | Type   |
| ------------------------- | -------------- | ------ |
| Qwen3 4B                  | Local LLM      | Ollama |
| faster-whisper Small      | Speech-to-text | Local  |
| Piper en_US-lessac-medium | Text-to-speech | Local  |
