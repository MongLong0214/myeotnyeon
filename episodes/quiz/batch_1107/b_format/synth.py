"""B-format narration takes: Qwen3-TTS 12Hz-1.7B CustomVoice 6-bit (MLX, local, offline), speaker Sohee,
same instruction strings as the owner-selected bake-off / N18 (production/lf_toon/n18_film/qwen_synth.py).
usage (bake-off venv): synth.py <qid> <normal|fast> <take> [line ids...] -> raw/<qid>/<id>_<style>_t<take>.wav"""
import os, sys, json
B = '/Users/isaac/projects/verdict-kr/work/research/tts_bakeoff'
os.environ.update(HF_HOME=f'{B}/hf', HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
sys.path.insert(0, B)
from pathlib import Path
import numpy as np, soundfile as sf
from common import trim
D = Path(__file__).resolve().parent
STYLE = "Tense, suspenseful documentary narration. Low, firm voice, brisk pace, crisp diction."
FAST = "Tense, suspenseful documentary narration. Low, firm voice, fast and urgent pace with short pauses, crisp diction."
if __name__ == '__main__':
    from mlx_audio.tts.utils import load_model
    q, style, take = sys.argv[1:4]; ids = set(sys.argv[4:])
    spec = json.loads((D / 'specs' / f'{q}.json').read_text())
    m = load_model('mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-6bit')
    def one(t):
        rs = list(m.generate_custom_voice(text=t, speaker='sohee', language='Korean', instruct=FAST if style == 'fast' else STYLE))
        return np.concatenate([np.asarray(np.array(r.audio), np.float32).reshape(-1) for r in rs]), rs[0].sample_rate
    one('워밍업입니다.')
    R = D / 'raw' / q; R.mkdir(parents=True, exist_ok=True)
    for s in spec['lines']:
        if ids and s['id'] not in ids: continue
        x, sr = one(s['tts']); sf.write(R / f"{s['id']}_{style}_t{take}.wav", trim(x, sr), sr)
        print('SYN', s['id'], style, take, round(len(x) / sr, 2), sr, flush=True)
