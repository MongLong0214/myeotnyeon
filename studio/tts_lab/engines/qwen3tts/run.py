import sys, pathlib, os
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / 'common'))
from labio import Raw, LINES, timer
import numpy as np, mlx.core as mx
from mlx_audio.tts.utils import load_model

which = sys.argv[1]
COMIC_EN = ("Fast-paced, high-energy comedic narrator for an adult animated cartoon. Playful and sarcastic, "
            "big exaggerated pitch swings, punchy emphasis on key words, a little over-the-top.")

def run(raw, voice, style, fn, params):
    for ln in LINES:
        if raw.have(voice, style, ln['id']):
            continue
        mx.random.seed(1000 + ln['id'])
        t = timer()
        res = list(fn(ln['tts']))
        wav = np.concatenate([np.array(r.audio, dtype=np.float32).reshape(-1) for r in res])
        raw.save(voice, style, ln['id'], wav, model.sample_rate, params=params, gen_s=t(), text=ln['tts'])

if which == 'custom':
    model = load_model('mlx-community/Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16')
    print('speakers', model.get_supported_speakers() if hasattr(model, 'get_supported_speakers') else '?', flush=True)
    raw = Raw('qwen3tts-cv')
    for spk in os.environ.get('SPK', 'Sohee,Ryan,Aiden,Dylan,Eric,Uncle_Fu,Vivian,Serena,Ono_Anna').split(','):
        for style, ins in (('neutral', None), ('comic', COMIC_EN)):
            run(raw, spk, style, lambda t: model.generate_custom_voice(text=t, speaker=spk, language='korean', instruct=ins),
                dict(model='Qwen3-TTS-12Hz-1.7B-CustomVoice-bf16', speaker=spk, language='korean', instruct=ins, seed='1000+line'))
else:
    model = load_model('mlx-community/Qwen3-TTS-12Hz-1.7B-VoiceDesign-bf16')
    raw = Raw('qwen3tts-vd')
    PERSONAS = {
        'M30': ("A Korean man in his early 30s with a bright, slightly husky voice, speaking natural Seoul Korean.",
                "Calm, clear documentary narrator, even pace.",
                "A fast-talking comedic narrator for an adult animated cartoon: energetic and sarcastic, big exaggerated pitch swings, punchy emphasis, comic timing."),
        'F20': ("A Korean woman in her late 20s with a clear, lively voice, speaking natural Seoul Korean.",
                "Calm, friendly news-style narrator, even pace.",
                "A witty variety-show narrator: fast, bouncy and playful, dramatic rises and falls in pitch, teasing tone, comic timing."),
        'Deep': ("A middle-aged Korean man with a deep, gravelly voice, speaking natural Seoul Korean.",
                 "Serious, measured narrator.",
                 "Over-the-top dramatic movie-trailer narration played for laughs: huge emphasis, theatrical pauses, booming climaxes."),
    }
    for v, (timbre, neu, com) in PERSONAS.items():
        for style, d in (('neutral', neu), ('comic', com)):
            ins = f'{timbre} {d}'
            run(raw, v, style, lambda t: model.generate_voice_design(text=t, instruct=ins, language='korean'),
                dict(model='Qwen3-TTS-12Hz-1.7B-VoiceDesign-bf16', instruct=ins, language='korean', seed='1000+line'))
