---
license: apache-2.0
base_model: openbmb/VoxCPM2
tags:
  - mlx
  - tts
  - text-to-speech
  - voice-cloning
  - voice-design
  - multilingual
library_name: mlx-audio
pipeline_tag: text-to-speech
language:
  - en
  - zh
  - id
  - ja
  - ko
  - multilingual
---

# VoxCPM2 - 8-bit quantized

MLX port of [openbmb/VoxCPM2](https://huggingface.co/openbmb/VoxCPM2) — a 2B-parameter multilingual TTS model with 48kHz studio-quality output, voice cloning, and voice design.

8-bit quantized (LM layers only, VAE/DiT at full precision). Best quality/speed tradeoff — nearly 2x faster, 35% smaller.

## Features
- **30 languages** — including English, Chinese, Indonesian, Japanese, Korean, and more
- **48kHz output** — studio-quality audio
- **Voice Design** — create voices from text descriptions (no reference audio needed)
- **Voice Cloning** — clone any voice from a short audio reference
- **4 generation modes** — zero-shot, continuation, reference cloning, combined

## Usage

```bash
pip install mlx-audio

# Zero-shot
python -m mlx_audio.tts.generate --model mlx-community/VoxCPM2-8bit --text "Hello world" --verbose

# Voice design
python -m mlx_audio.tts.generate --model mlx-community/VoxCPM2-8bit \
  --text "Hello world" \
  --instruct "A young woman, gentle and sweet voice"

# Voice cloning
python -m mlx_audio.tts.generate --model mlx-community/VoxCPM2-8bit \
  --text "Hello world" \
  --ref_audio speaker.wav --ref_text "reference text"
```

### Python API

```python
from mlx_audio.tts import load_model

model = load_model("mlx-community/VoxCPM2-8bit")

# Generate
for result in model.generate(
    text="Hello, this is VoxCPM2 on Apple Silicon.",
    inference_timesteps=7,
    cfg_value=2.0,
):
    print(f"Duration: {result.audio_duration}")
```

## Performance (Apple Silicon)

| Variant | Size | RTF (7 timesteps) |
|---------|------|--------------------|
| bf16 | 4.96 GB | 0.48x |
| **8-bit** | **3.23 GB** | **0.85x** |
| **4-bit** | **2.30 GB** | **0.90x** |

*RTF = Real-Time Factor (>1.0 = faster than realtime)*

## Original Model
- [openbmb/VoxCPM2](https://huggingface.co/openbmb/VoxCPM2)
- Apache 2.0 License

Converted with [mlx-audio](https://github.com/Blaizzy/mlx-audio).
