"""Kokoro-82M (Apache-2.0) local synth for every spec line. Runs in research/tts_kokoro/.venv (reuses that install,
HF cache offline). usage: synth.py <id> [voice] [speed] -> cand/<id>/<Lxx>.wav (24 kHz)"""
import os, sys, json
K = '/Users/isaac/projects/verdict-kr/work/research/tts_kokoro'
os.environ['HF_HOME'] = K + '/hf'; os.environ['HF_HUB_OFFLINE'] = '1'
sys.path.insert(0, K)
from gen import synth
import soundfile as sf
D = os.path.dirname(os.path.abspath(__file__)); q = sys.argv[1]
sp = json.load(open(f'{D}/specs/{q}.json'))
voice = sys.argv[2] if len(sys.argv) > 2 else sp['voice']; speed = float(sys.argv[3]) if len(sys.argv) > 3 else sp['speed']
out = f'{D}/cand/{q}'; os.makedirs(out, exist_ok=True)
for l in sp['lines']:
    x, sr = synth('a', voice, l.get('speed', speed), l['tts'])
    sf.write(f"{out}/{l['id']}.wav", x, sr); print(l['id'], round(len(x) / sr, 2))
