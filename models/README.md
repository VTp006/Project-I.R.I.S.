# I.R.I.S. Models

This directory contains information and setup instructions for the AI models used by I.R.I.S.

I.R.I.S. follows a **local-first architecture**, using local models as the primary option.

---

## 1. Speech-to-Text — faster-whisper

**Purpose:** Converts microphone audio into text.

**Engine:** faster-whisper
**Model:** `small`
**Runtime:** Local
**Primary:** Yes

### Installation

Install faster-whisper through `requirements.txt`:

```powershell
pip install faster-whisper==1.2.1
```

### Model

I.R.I.S. currently uses:

```text
small
```

The model is automatically downloaded when faster-whisper loads it for the first time.

### Configuration

Current configuration:

```python
WhisperModel(
    "small",
    device="cpu",
    compute_type="int8"
)
```

The current setup uses CPU inference for compatibility.

> GPU/CUDA acceleration can be enabled later.

---

## 2. Local LLM — Ollama

**Purpose:** Main reasoning and conversational AI.

**Model:** `qwen3:4b`
**Runtime:** Local
**Primary:** Yes

I.R.I.S. uses **Ollama** to run its local language model.

### Install Ollama

Install Ollama on Windows and verify the installation:

```powershell
ollama --version
```

### Download the Model

I.R.I.S. currently uses:

```text
qwen3:4b
```

Download it with:

```powershell
ollama pull qwen3:4b
```

Verify:

```powershell
ollama list
```

You should see:

```text
qwen3:4b
```

### Test

Run:

```powershell
ollama run qwen3:4b
```

Then enter a prompt to verify that the model responds.

### Python Package

The Python interface is installed through:

```text
ollama==0.6.3
```

I.R.I.S. communicates with Ollama through:

```text
api/ollama.py
```

---

## 3. Text-to-Speech — Piper

**Purpose:** Converts I.R.I.S. responses into speech.

**Engine:** Piper
**Voice Model:** `en_US-lessac-medium`
**Runtime:** Local
**Primary:** Yes

Piper is I.R.I.S.'s primary offline TTS engine.

### Installation TTS

Install through:

```powershell
pip install piper-tts==1.8.0
```

Verify:

```powershell
python -m piper --help
```

### Voice Model

I.R.I.S. currently uses:

```text
en_US-lessac-medium
```

Download it with:

```powershell
python -m piper.download_voices en_US-lessac-medium --data-dir models/piper
```

The model files will be placed inside:

```text
models/piper/
```

Expected files:

```text
models/piper/
├── en_US-lessac-medium.onnx
└── en_US-lessac-medium.onnx.json
```

These files are intentionally excluded from Git because the model binary is large.

---

## Current Model Summary

| Component      | Model                       | Runtime        | Status    |
| -------------- | --------------------------- | -------------- | --------  |
| Speech-to-Text | faster-whisper `small`      | Local          | ✅ Active |
| LLM            | Qwen3 `4B`                  | Ollama / Local | ✅ Active |
| Text-to-Speech | Piper `en_US-lessac-medium` | Local          | ✅ Active |

---

## Local-First Principle

I.R.I.S. is designed to work primarily with local models.

```text
Local Model
     ↓
I.R.I.S. Core
     ↓
Offline Operation
```

This reduces internet dependency, API usage, cloud latency, privacy concerns, and recurring costs.

The goal is for the core I.R.I.S. functionality to remain usable **offline** whenever the required local models are available.
