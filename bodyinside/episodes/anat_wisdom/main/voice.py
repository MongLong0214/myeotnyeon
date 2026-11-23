"""Sohee narration, using the neck episode's Qwen checkpoint and a continuous dialogue clock."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys

import numpy as np
import soundfile as sf

MAIN = Path(__file__).resolve().parent
WORK = MAIN.parents[2]
AUDIO = MAIN / "audio"
MODEL = "mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-6bit"
STYLE = "Warm, clear Korean documentary narration. Brisk conversational pace. Small pauses. Clear articulation."
os.environ.update(HF_HOME=str(WORK / "research/tts_bakeoff/hf"), HF_HUB_OFFLINE="1")

def trim(wave, sample_rate):
    size = sample_rate // 100
    count = len(wave) // size
    rms = np.sqrt(np.mean(wave[:count*size].reshape(-1,size)**2,axis=1))
    loud = rms > max(.005, rms.max() * .024)
    active = np.flatnonzero(loud)
    start, end = max(0, active[0]-1), min(count, active[-1]+2)
    cuts = []
    i = start
    while i < end:
        if loud[i]:
            i += 1
            continue
        j = i
        while j < end and not loud[j]:
            j += 1
        if j-i > 13:
            cuts.append((i+5, j-5))
        i = j
    return np.concatenate([wave[a*size:b*size] for a,b in
        zip([start]+[b for a,b in cuts], [a for a,b in cuts]+[end])])

def take_for(index, text, duration, replace):
    raw = AUDIO / f"sohee_raw_{index}.wav"
    if raw.exists() and not replace:
        return raw
    from mlx_audio.tts.utils import load_model
    if not hasattr(take_for,"model"):
        take_for.model = load_model(MODEL)
    best = None
    for instruction in (STYLE, STYLE + " Aim for about six Korean syllables per second.",
                        STYLE + " Speak rapidly but articulate each word distinctly."):
        generated = list(take_for.model.generate_custom_voice(
            text=text, speaker="sohee", language="Korean", instruct=instruction,
            temperature=.65, top_p=.9))
        sr = generated[0].sample_rate
        wave = trim(np.concatenate([np.asarray(g.audio).reshape(-1) for g in generated]),sr)
        ratio = len(wave)/(sr*duration)
        candidate = (abs(np.log(ratio)),wave,sr)
        if best is None or candidate[0] < best[0]:
            best = candidate
        if .84 <= ratio <= 1.38:
            break
    sf.write(raw,best[1],best[2])
    return raw

def fit(raw, out, duration, sr):
    x, source_sr = sf.read(raw)
    factor = len(x)/(source_sr*duration)
    for _ in range(3):
        subprocess.run(["ffmpeg","-v","error","-y","-i",str(raw),"-af",
                        f"atempo={factor:.5f},aresample={sr}",str(out)],check=True)
        result, _ = sf.read(out,dtype="float32")
        actual = len(result)/sr
        if abs(actual-duration) < .008:
            return result,factor
        factor *= actual/duration
    return result,factor

def main():
    episode = json.loads((MAIN/"episode.json").read_text())
    original = AUDIO/"sfx_only.wav"
    if not original.exists():
        original.write_bytes((AUDIO/"sfx.wav").read_bytes())
    sfx, sr = sf.read(original,dtype="float32",always_2d=True)
    voice = np.zeros(len(sfx),np.float32)
    lines = []
    replace = {int(x) for x in sys.argv[1:]}
    for index,line in enumerate(episode["narration"]):
        b = episode["beats"][line["beat"]]
        start = b["t0"] + (.025 if index==0 else .04)
        duration = b["t1"] - b["t0"] - .15
        take = line.get("take",index)
        raw = take_for(take,line.get("spoken",line["text"]),duration,index in replace)
        name = f"narr_{take}.wav"
        y,tempo = fit(raw,AUDIO/name,duration,sr)
        n = len(re.findall("[가-힣]",line["text"]))
        sample = round(start*sr)
        voice[sample:sample+len(y)] = y
        record = dict(line=index,beat=line["beat"],text=line["text"],start=sample/sr,end=(sample+len(y))/sr,
                      syll=n,rate=round(n*sr/len(y),2),atempo=round(tempo,3),file=name)
        lines.append(record)
        print(record,flush=True)
    window = sr//50
    env = np.sqrt(np.maximum(0,np.convolve(voice**2,np.ones(window)/window,"same")))
    turn = (env>.01).astype(np.float32)
    duck = np.convolve(turn,np.ones(sr//8)/(sr//8),"same")
    mix = sfx * (1-.90*duck[:,None]) + voice[:,None] * 1.2
    sf.write(AUDIO/"sfx.wav",np.tanh(1.5*mix).astype(np.float32),sr)
    (AUDIO/"narration.json").write_text(json.dumps(lines,ensure_ascii=False,indent=2)+"\n")

if __name__ == "__main__":
    main()
