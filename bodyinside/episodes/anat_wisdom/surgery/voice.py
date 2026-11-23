"""Render the Sohee track against the surgery shot clock."""
import json
from pathlib import Path
import re
import subprocess
import sys

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "main"))
import voice as main_voice

AUDIO = HERE / "audio"
main_voice.AUDIO = AUDIO

def main():
    AUDIO.mkdir(exist_ok=True)
    rate = 48000
    beats = json.loads((HERE / "timing.json").read_text())
    voice = np.zeros(round(beats[-1]["end"] * rate), dtype=np.float32)
    for index, beat in enumerate(beats):
        text = beat["voice"]
        syllables = len(re.findall("[가-힣]", text))
        duration = min(beat["end"] - beat["start"] - .28, syllables / 5.6 + .10)
        start = round((beat["start"] + (.035 if index == 0 else .14)) * rate)
        raw = main_voice.take_for(index, text, duration, str(index) in sys.argv[1:])
        take, tempo = main_voice.fit(raw, AUDIO / f"take_{index}.wav", duration, rate)
        voice[start:start+len(take)] = take
        print(f"{start/rate:.3f}–{(start+len(take))/rate:.3f} | {tempo:.2f}x | {text}", flush=True)
    sf.write(AUDIO / "voice.wav", voice, rate)
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", str(AUDIO / "voice.wav"),
                    "-af", "highpass=f=65,loudnorm=I=-15:TP=-1.5:LRA=7",
                    "-ar", str(rate), str(AUDIO / "narration.wav")], check=True)

if __name__ == "__main__":
    main()
