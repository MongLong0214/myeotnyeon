#!/usr/bin/env python3
"""Pick, for chosen narration lines, the lexicon respelling whose synthesized take is HEARD as the target word by Whisper at temperature 0 and 0.4 (a plain 'C자' in the transcript is not evidence: Whisper normalizes it).
usage (.venv): python narr_pick.py EPISODE_DIR LINE TARGETREGEX CAND1 CAND2 ...   e.g.  narr_pick.py . 0 '씨짜|C짜' '목뼈는 ... 씨-짜예요.' ...
Writes audio/narr_<line>.wav (replacing the take), updates audio/narration.json and episode.json 'spoken' (episode.json + episode_variantB.json), prints the transcripts."""
import sys, os, json, re, subprocess, shutil
os.environ.update(HF_HUB_OFFLINE='1')
from pathlib import Path
import mlx_whisper
E, LINE, TARGET, CANDS = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4:]
M = str(next(Path.home().joinpath('.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots').glob('*/weights.safetensors')).parent)
MLX = (__import__('os').path.dirname(__import__('os').path.abspath(__file__)) + '/../../research/tts_bakeoff/venvs/mlx/bin/python'); KIT = os.path.dirname(os.path.abspath(__file__))
cj = E + '/audio/cand_in.json'; json.dump(CANDS, open(cj, 'w'), ensure_ascii=False); subprocess.run([MLX, KIT + '/narr_synth.py', E, str(LINE), cj, '3'], check=True, stdout=subprocess.DEVNULL)
info = json.load(open(f'{E}/audio/cand/L{LINE}.json')); good = []
def asr(p, t): return mlx_whisper.transcribe(p, path_or_hf_repo=M, language='ko', temperature=t, condition_on_previous_text=False, verbose=None)['text'].strip()
for it in info:
    h0 = asr(it['file'], 0); h4 = asr(it['file'], 0.4); it['h0'] = h0; it['h4'] = h4
    ok = bool(re.search(TARGET, h0.replace(' ', ''))) and bool(re.search(TARGET, h4.replace(' ', ''))) and 6.2 <= it['rate'] <= 6.6
    print(it['cand'], it['take'], it['rate'], it['atempo'], 'OK' if ok else '--', '|', h0, '|', h4, flush=True)
    if ok: good.append(it)
if not good: print('NO CANDIDATE PASSED'); sys.exit(1)
best = sorted(good, key=lambda it: (it['cand'], it['take']))[0]; print('PICK', best['cand'], best['take'], best['text'])
shutil.copyfile(best['file'], f'{E}/audio/narr_{LINE}.wav')
nj = json.load(open(E + '/audio/narration.json')); l = nj[LINE]; import soundfile as sf
x, sr = sf.read(f'{E}/audio/narr_{LINE}.wav'); l.update(text=best['text'], end=l['start'] + len(x) / sr, rate=best['rate'], atempo=best['atempo'], syll=best['syll']); json.dump(nj, open(E + '/audio/narration.json', 'w'), ensure_ascii=False, indent=1)
for p in ('episode.json', 'episode_variantB.json'):
    e = json.load(open(E + '/' + p)); e['narration'][LINE]['spoken'] = best['text']; json.dump(e, open(E + '/' + p, 'w'), ensure_ascii=False, indent=1)
