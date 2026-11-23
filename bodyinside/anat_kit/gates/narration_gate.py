#!/usr/bin/env python3
"""usage: python narration_gate.py EPISODE_DIR -> JSON, exit 1 on fail. Whisper (mlx large-v3-turbo, local) transcript vs the script (CER <= 8 %), caption/narration sync, pauses <= 0.2 s inside a line."""
import sys, os, json; os.environ.update(HF_HUB_OFFLINE='1')
from pathlib import Path
import numpy as np, soundfile as sf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import checks
import mlx_whisper
E = sys.argv[1]; ep = json.load(open(E + '/episode.json')); lines = json.load(open(E + '/audio/narration.json'))
M = str(next(Path.home().joinpath('.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots').glob('*/weights.safetensors')).parent)
hyp = [mlx_whisper.transcribe(E + '/audio/' + l['file'], path_or_hf_repo=M, language='ko', temperature=0, condition_on_previous_text=False, verbose=None)['text'].strip() for l in lines]
ok1, r1 = checks.narration_wer([(l['text'], h) for l, h in zip(lines, hyp)]); ok2, r2 = checks.narration_sync(lines, ep['beats'])
gaps = []
for l in lines:
    x, sr = sf.read(E + '/audio/' + l['file'], dtype='float32'); x = x.reshape(-1) if x.ndim == 1 else x.mean(1); w = int(sr * 0.01); n = len(x) // w; q = 20 * np.log10(np.sqrt(np.mean(x[:n * w].reshape(-1, w) ** 2, 1)) + 1e-9) < -42
    run = best = 0
    for v in q[int(0.05 * 100):-int(0.05 * 100)]: run = run + 1 if v else 0; best = max(best, run)
    if best * 0.01 > 0.2: gaps.append((l['line'], round(best * 0.01, 2)))
def listen_flags(movie):
    import re
    import subprocess
    import tempfile
    def normalize(s):
        return re.sub(r'[\s,.?!-]', '', s).casefold().replace('c자', '씨짜').replace('c짜', '씨짜')
    rows, flags = [], []
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / 'mix.wav'
        subprocess.run(['ffmpeg', '-v','error','-i',movie,'-ac','1','-ar','16000',str(wav)],check=True)
        audio, rate = sf.read(wav, dtype='float32')
        for line in lines:
            sample = Path(tmp) / 'line.wav'
            sf.write(sample, audio[max(0,int((line['start']-.1)*rate)):int((line['end']+.1)*rate)], rate)
            heard = [mlx_whisper.transcribe(str(sample),path_or_hf_repo=M, language='ko', temperature=temp,
                     condition_on_previous_text=False,verbose=None)['text'].strip() for temp in (0,.4)]
            rows.append({'line':line['line'],'heard':heard})
            for target in ep.get('lexicon_heard', []):
                aliases = [normalize(a) for a in target.split('|')]
                if any(a in normalize(line['text']) for a in aliases) and not all(
                        any(a in normalize(s) for a in aliases) for s in heard):
                    flags.append(dict(line=line['line'], target=target, heard=heard))
    return dict(source=movie, lines=rows, listen_flags=flags)

out = {'wer': {'ok': ok1, **r1, 'heard': hyp}, 'sync': {'ok': ok2, **r2}, 'pauses': {'ok': not gaps, 'over_0.2s': gaps}}; out['pass'] = ok1 and ok2 and not gaps
if len(sys.argv) > 2:
    out['final_mix'] = listen_flags(sys.argv[2])
print(json.dumps(out, ensure_ascii=False, indent=1)); sys.exit(0 if out['pass'] else 1)
