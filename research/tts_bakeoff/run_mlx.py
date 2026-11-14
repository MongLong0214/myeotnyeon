"""Bake-off runner for MLX engines. usage: run_mlx.py <engine>  (weights from ./hf, offline)."""
import os, sys, time, json
HERE = os.path.dirname(os.path.abspath(__file__)); os.environ.update(HF_HOME=f'{HERE}/hf', HF_XET_HIGH_PERFORMANCE='1'); os.environ.setdefault('HF_HUB_OFFLINE', '1')
import numpy as np, soundfile as sf, mlx.core as mx
sys.path.insert(0, HERE); from common import SPOKEN, trim
from mlx_audio.tts.utils import load_model
MALE = ("Korean male documentary narrator in his late 30s. Low, firm, slightly husky baritone. "
        "Tense, suspenseful true-crime delivery, brisk pace, crisp diction, no smile in the voice.")
FEMALE = ("Korean female documentary narrator in her early 30s. Low-mid pitch, cool and composed. "
          "Tense, suspenseful true-crime delivery, brisk pace, crisp diction.")
STYLE = "Tense, suspenseful documentary narration. Low, firm voice, brisk pace, crisp diction."
REF_TEXT = "그날 밤, 서버실의 불은 꺼지지 않았습니다. 누군가 이미 안에 들어와 있었던 겁니다."
REF = {'male': f'{HERE}/raw/ref_design_male.wav', 'female': f'{HERE}/raw/ref_design_female.wav'}
def arr(r): return np.asarray(np.array(r.audio), np.float32).reshape(-1)
def one(gen):  # concatenate all chunks a generator yields
    rs = list(gen); return np.concatenate([arr(r) for r in rs]), rs[0].sample_rate
def run(tag, fn, texts=SPOKEN):
    fn('워밍업입니다.')
    meta = []
    for i, t in enumerate(texts):
        t0 = time.time(); x, sr = fn(t); dt = time.time() - t0
        sf.write(f'{HERE}/raw/{tag}_{i}.wav', trim(x, sr), sr); meta.append(dict(line=i, synth_s=dt, sr=sr)); print(tag, i, round(dt, 2), len(x) / sr, flush=True)
    json.dump(meta, open(f'{HERE}/raw/{tag}.json', 'w'))
e = sys.argv[1]
if e == 'qwen3_custom':
    m = load_model('mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-6bit')
    for spk in ['sohee', 'ryan']:
        run(f'qwen3tts-cv_{spk}', lambda t, s=spk: one(m.generate_custom_voice(text=t, speaker=s, language='Korean', instruct=STYLE)))
elif e == 'qwen3_design':
    m = load_model('mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-6bit')
    for g, ins in [('male', MALE), ('female', FEMALE)]:
        x, sr = one(m.generate_voice_design(text=REF_TEXT, language='Korean', instruct=ins)); sf.write(REF[g], trim(x, sr), sr)
        run(f'qwen3tts-design_{g}', lambda t, i=ins: one(m.generate_voice_design(text=t, language='Korean', instruct=i)))
elif e == 'voxcpm2':
    m = load_model('mlx-community/VoxCPM2-4bit')
    for g, ins in [('male', MALE), ('female', FEMALE)]:
        run(f'voxcpm2-design_{g}', lambda t, i=ins: one(m.generate(text=t, instruct=i, inference_timesteps=10)))
elif e == 'chatterbox':
    m = load_model('mlx-community/chatterbox-multilingual-v3')
    for g in ['male', 'female']:  # reference = our own synthetic Qwen3 VoiceDesign clip, not a real person
        run(f'chatterbox-ml_{g}', lambda t, g=g: one(m.generate(text=t, ref_audio=REF[g], lang_code='ko', exaggeration=0.6, cfg_weight=0.4, verbose=False)))
elif e == 'moss_nano':
    m = load_model('mlx-community/MOSS-TTS-Nano-100M')
    for g in ['male', 'female']:
        run(f'moss-nano_{g}', lambda t, g=g: one(m.generate(text=t, ref_audio=REF[g], ref_text=REF_TEXT)))
