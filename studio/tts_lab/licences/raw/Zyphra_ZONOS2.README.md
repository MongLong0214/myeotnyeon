---
license: apache-2.0
pipeline_tag: text-to-speech
library_name: ZONOS2
---

# ZONOS2

<p align="center">
  <img src="./assets/ZONOS2BlogThumbnail.png" alt="ZONOS2 title card" width="750" />
</p>

<div align="center">
  <a href="https://discord.gg/gTW9JwST8q" target="_blank">
    <img src="https://img.shields.io/badge/Join%20Our%20Discord-7289DA?style=for-the-badge&logo=discord&logoColor=white" alt="Discord">
  </a>
</div>

---


ZONOS2 is our latest text-to-speech model trained on more than 6 million hours of varied multilingual speech, delivering expressiveness and quality on par with—or even surpassing—top TTS providers at low latency with MoE. ZONOS2 excels at high-fidelity and naturalistic voice cloning.


During inference we use nemo TN normalized UTF-8 bytes and an ECAPA-TDNN embedding to generate DAC tokens with our MoE backbone. An inference overview can be seen below.
<p align="center">
  <img src="./assets/zonos2_arlooop_animated.gif" alt="ZONOS2 title card" width="750" />
</p>

Language support is as follows.
| Tier   | Languages                                                                                                                                                                                      |
| ------ | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Tier 1 | English, Mandarin Chinese, Japanese                                                                                                                                                            |
| Tier 2 | Korean, Russian, Italian, Portuguese, French, Spanish, Vietnamese, German, Hebrew, Dutch                                                                                                       |
| Tier 3 | Swedish, Hindi, Tamil, Telugu, Thai, Norwegian, Bengali, Tagalog, Arabic, Danish, Indonesian, Polish, Ukrainian, Romanian, Finnish, Hungarian, Lithuanian, Estonian, Slovak, Croatian, Latvian |


For local inference we provide a high-performance TTS inference server built on [Mini-SGLang](https://github.com/sgl-project/mini-sglang).

**For more details and speech samples, check out our [blog](https://www.zyphra.com/our-work/zonos2).**

**We also have a hosted version available at [cloud.zyphra.com/audio-playground](https://cloud.zyphra.com/audio-playground).**

---

## Quick Start

> **Platform Support**: Linux only (x86_64). Requires NVIDIA GPU with CUDA toolkit matching your driver version (`nvidia-smi` to check).

### 1. Installation

Requires [uv](https://docs.astral.sh/uv/getting-started/installation/).

```bash
git clone https://github.com/Zyphra/ZONOS2.git
cd ZONOS2
uv sync
```

### 2. Launch the TTS Server

```bash
uv run python -m minisgl --model-path Zyphra/ZONOS2 --tts-default-voices-dir ./default_voices/
```

`uv run` always uses the project environment, so no venv activation is needed.

The server starts on `http://localhost:1919` by default. TTS mode is auto-detected for zonos2 models.
`--tts-default-voices-dir <folder>` pre-populates the web UI with voice-clone
speakers from disk; the folder is scanned recursively for speaker audio
(`.wav`, `.mp3`, `.flac`, `.m4a`, `.ogg`, `.opus`, `.aac`, `.webm`) and saved
embeddings (`.npy`, `.npz`). The newest voice is selected automatically on
startup.

### 3. Generate Speech

**curl:**

```bash
curl -X POST http://localhost:1919/tts/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "stream": true}' \
  --output output.pcm

# Convert to WAV
ffmpeg -f f32le -ar 44100 -ac 1 -i output.pcm output.wav
```

**Web UI:** Open `http://localhost:1919/` in your browser.

## Python API (offline inference)

You can also run the engine directly in a Python script, without starting a
server, via `TTSLLM`:

```python
from zonos2.message import TTSSamplingParams
from zonos2.tts import TTSLLM

tts = TTSLLM(model_path="Zyphra/ZONOS2")

results = tts.generate(
    ["Hello from the offline Python API.", "Batched prompts work too."],
    TTSSamplingParams(seed=42),
)

for i, result in enumerate(results):
    print(f"frames={len(result['audio_tokens'])}, eos_frame={result['eos_frame']}")
    tts.save_audio(result["audio"], f"output_{i}.wav")
```


## Citation
If you find this model useful in an academic context please cite as:
```
@misc{zyphra2025zonos,
  title     = {Zonos V2 Technical Report},
  author    = {Gabriel Clark, Sofian Mejjoute, Mohamed Osman, George Close, Beren Millidge},
  year      = {2026},
}
```
