"""Kokoro-82M (Apache-2.0) local synth. usage: gen.py <lang a|j> <voice> <speed> <out.wav> <text>
HF cache is local to this dir; after the first download set HF_HUB_OFFLINE=1."""
import os, sys
os.environ.setdefault('HF_HOME', os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hf'))
import numpy as np, soundfile as sf
from kokoro import KPipeline
_P = {}
def pipe(lang):
    if lang not in _P: _P[lang] = KPipeline(lang_code=lang, repo_id='hexgrad/Kokoro-82M')
    return _P[lang]
def synth(lang, voice, speed, text):
    out = [np.asarray(r.audio, np.float32) for r in pipe(lang)(text, voice=voice, speed=speed, split_pattern=None) if r.audio is not None]
    return np.concatenate(out), 24000
if __name__ == '__main__':
    lang, voice, speed, out, text = sys.argv[1:6]
    x, sr = synth(lang, voice, float(speed), text); sf.write(out, x, sr); print(out, round(len(x)/sr, 2))
