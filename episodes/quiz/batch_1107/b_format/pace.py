"""Pace, pick and assemble B-format narration (work/.venv). Same processing as research/tts_bakeoff/make_tempo.py and
production/lf_toon/n18_film/qwen_pace.py: internal pauses >0.18 s cut to 0.17 s, per-line atempo to the target
(default 6.4 syll/s, cap 1.4x). Every take is checked on its isolated paced clip with local whisper-large-v3-turbo;
lowest CER wins. Then lines are joined with 0.18 s gaps, voice onsets/offsets are measured on the joined
track with ffmpeg silencedetect, and case.json (timeline + subtitle cues) is written to upload/pkg/<qid>_B/.
usage: pace.py <qid>"""
import os, sys, json, re, subprocess, glob, math
os.environ.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1')
from pathlib import Path
import numpy as np, soundfile as sf
sys.path.insert(0, str(Path(__file__).resolve().parent))
import intl
L = 'ko'  # set from the spec's "locale" in main()
D = Path(__file__).resolve().parent; W = D.parents[3]
SR = 48000; LIMIT = 1.4; GAP = .18; FPS = 30
def syl(t): return intl.units(t, L)
def squeeze(x, sr, keep=.17, db=-40):
    w = int(sr * .01); n = len(x) // w; r = 20 * np.log10(np.sqrt(np.mean(x[:n*w].reshape(-1, w)**2, 1)) + 1e-9)
    q = r < r.max() + db; out = []; i = 0; longest = 0
    while i < n:
        j = i
        while j < n and q[j] == q[i]: j += 1
        seg = x[i*w:j*w]
        if q[i] and 0 < i and j < n:
            if (j - i) * w > keep * sr: h = int(keep * sr / 2); seg = np.r_[seg[:h], seg[-h:]]
            longest = max(longest, len(seg) / sr)
        out.append(seg); i = j
    return np.concatenate(out + [x[n*w:]]), longest
def cer(a, b):
    d = list(range(len(b) + 1))
    for i, c in enumerate(a, 1):
        prev = d[:]; d[0] = i
        for j, v in enumerate(b, 1): d[j] = min(prev[j] + 1, d[j-1] + 1, prev[j-1] + (c != v))
    return d[-1] / max(1, len(a))
NUM = {'1': '일', '2': '이', '3': '삼', '5': '오', '8': '팔'}
def heard(t):
    t = re.sub(r'(\d+)\s*명', lambda m: {'3': '세', '2': '두'}.get(m[1], m[1]) + '명', t)
    t = re.sub(r'\d+', lambda m: sino(int(m[0])), t)
    for a, b in {'B': '비', 'b': '비', '노리': '놀이'}.items(): t = t.replace(a, b)
    return re.sub('[^가-힣]', '', t)
def sino(n):
    if not n: return '영'
    out = ''
    for v, u in [(1000, '천'), (100, '백'), (10, '십'), (1, '')]:
        q, n = divmod(n, v)
        if q: out += ('' if q == 1 and v > 1 else '일이삼사오육칠팔구'[q - 1]) + u
    return out
M = None
def asr(path):
    global M
    import mlx_whisper
    if M is None: M = next(Path('/Users/isaac/.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots').glob('*/weights.safetensors')).parent
    return mlx_whisper.transcribe(str(path), path_or_hf_repo=str(M), language=intl.WL[L], temperature=0, condition_on_previous_text=False, verbose=None)
def candidate(q, s, raw):
    C = D / 'cand' / q; C.mkdir(parents=True, exist_ok=True)
    tag = Path(raw).stem; out = C / f'{tag}.wav'; meta = C / f'{tag}.json'
    if meta.exists() and meta.stat().st_mtime >= Path(raw).stat().st_mtime: return json.loads(meta.read_text())  # a re-synthesised take (--force-tts) must not reuse the old take's ASR
    target = s.get('target', intl.TARGET[L]); n = syl(s['tts'])
    x0, sr = sf.read(raw, dtype='float32'); x, lp = squeeze(x0, sr)
    native = n / (len(x) / sr); f = min(LIMIT, target / native)
    if f < 1:
        x, lp = squeeze(x0, sr, keep=.17 * f); native = n / (len(x) / sr); f = min(LIMIT, target / native)
    tmp = C / '_sq.wav'; sf.write(tmp, x, sr)
    subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', str(tmp), '-af', f'atempo={f:.4f}', '-ar', str(SR), '-ac', '1', '-c:a', 'pcm_s24le', str(out)], check=True)
    y, _ = sf.read(out, dtype='float32')
    a = asr(out); e = cer(intl.norm(s['tts'], L) if L != 'ko' else re.sub('[^가-힣]', '', s['tts']), intl.norm(a['text'], L, heard))
    rec = dict(tag=tag, native_sps=native, atempo=f, duration=len(y) / SR, sps=n / (len(y) / SR), longest_internal_pause=lp / f, cer=e, asr_text=a['text'])
    meta.write_text(json.dumps(rec, ensure_ascii=False)); return rec
def silences(path):
    r = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(path), '-af', 'silencedetect=noise=-38dB:d=0.08', '-f', 'null', '-'], capture_output=True, text=True).stderr
    st = [float(v) for v in re.findall(r'silence_start: ([\d.]+)', r)]; en = [float(v) for v in re.findall(r'silence_end: ([\d.]+)', r)]
    return list(zip(st, en + [None] * (len(st) - len(en))))
def main(q):
    global L
    spec = json.loads((D / 'specs' / f'{q}.json').read_text()); L = spec.get('locale', 'ko'); P = W / 'upload/pkg' / f'{q}_B'; (P / 'audio').mkdir(parents=True, exist_ok=True)
    chosen = []; bad = []
    for s in spec['lines']:
        cands = [candidate(q, s, r) for r in sorted(glob.glob(str(D / 'raw' / q / f"{s['id']}_*.wav")))]
        best = min(cands, key=lambda c: (round(c['cer'], 3), c['atempo'] >= LIMIT - 1e-6, abs(c['atempo'] - 1)))
        if best['cer'] > .03 or best['atempo'] >= LIMIT - 1e-6: bad.append((s['id'], round(best['cer'], 3), round(best['atempo'], 2), best['asr_text']))
        chosen.append(best); print(s['id'], best['tag'], 'x%.3f' % best['atempo'], '%.2f syl/s' % best['sps'], '%.2fs' % best['duration'], 'cer', round(best['cer'], 3), len(cands), best['asr_text'].strip(), flush=True)
    # join: line, gap (0.18 s, or hold_after) ...; short 0.03 s lead-in so frame 0 already speaks
    parts = [np.zeros(int(.03 * SR), np.float32)]; placed = []
    for s, c in zip(spec['lines'], chosen):
        y, _ = sf.read(D / 'cand' / q / f"{c['tag']}.wav", dtype='float32')
        at = sum(len(p) for p in parts) / SR; parts.append(y); placed.append(at)
        parts.append(np.zeros(int(s.get('hold_after', GAP) * SR), np.float32))
    parts[-1] = np.zeros(int(.25 * SR), np.float32)  # loop tail
    x = np.concatenate(parts); total = len(x) / SR
    n = math.ceil(total * FPS); x = np.pad(x, (0, n * SR // FPS - len(x)))
    sf.write(P / 'narration.wav', x, SR, subtype='PCM_24')
    sil = silences(P / 'narration.wav')
    # voice onset of a line = end of the silence that ends nearest before/at its placement (+ clip lead)
    def onset(at):
        ends = [e for st, e in sil if e is not None and st <= at + .06 and e <= at + .25]
        return max(ends) if ends else at
    def offset(at, nxt):
        sts = [st for st, e in sil if at < st < nxt]
        return max(sts) if sts else nxt
    lines = []
    for i, (s, c) in enumerate(zip(spec['lines'], chosen)):
        on = 0.0 if i == 0 else onset(placed[i]); nxt = placed[i + 1] if i + 1 < len(placed) else total
        off = offset(placed[i] + c['duration'] - .3, nxt + .01)
        lines.append(dict(s, **({'lip': intl.kana(s['tts'])} if L == 'ja' else {}), onset=round(on, 3), offset=round(min(off, placed[i] + c['duration']), 3), placed=round(placed[i], 3), take=c['tag'], sps=c['sps'], atempo=c['atempo'], cer=c['cer'], asr=c['asr_text'], syllables=syl(s['tts'])))
    for i, l in enumerate(lines):
        l['from_frame'] = 0 if i == 0 else max(0, math.floor(l['onset'] * FPS) - 1)
    for i, l in enumerate(lines):
        l['dur'] = (lines[i + 1]['from_frame'] if i + 1 < len(lines) else n) - l['from_frame']
    subs = []
    for i, l in enumerate(lines):
        if not l.get('shown'): continue
        end = min(l['offset'] + .12, lines[i + 1]['onset'] if i + 1 < len(lines) else n / FPS)
        subs.append(dict(start_s=l['onset'], end_s=round(end, 3), text=l['shown'], parent=l['id'], **({'emphasis': l['emphasis']} if l.get('emphasis') else {})))
    case = dict({k: v for k, v in spec.items() if k != 'lines'}, n=n, duration=n / FPS, utterances=lines, subtitles=subs,
                choice_frame=next((l['from_frame'] for l in lines if l['mode'] == 'choices'), None),  # None: result_first format (no quiz)
                answer_frame=next((l['from_frame'] for l in lines if l['mode'] == 'answer'), None),
                opinion_frame=next((l['from_frame'] for l in lines if l['mode'] == 'opinion'), None),
                options_frame=next((l['from_frame'] for l in lines if l['mode'] == 'options'), None))
    # option onsets inside L10 (for card beats): silences inside the options clip
    opt = next((l for l in lines if l['mode'] == 'options'), None)
    # measured inside the chosen options clip (silencedetect -30dB / whisper word starts), stored in the spec
    case['option_onsets'] = [round(opt['placed'] + o, 3) for o in spec['option_offsets']] if opt else []
    (P / 'case.json').write_text(json.dumps(case, ensure_ascii=False, indent=1))
    (P / 'audio.json').write_text(json.dumps(dict(engine=spec.get('engine', 'Qwen3-TTS 12Hz-1.7B CustomVoice 6-bit MLX (local, offline)'), voice=spec.get('voice', 'Sohee'),
        processing='pauses>0.18s->0.17s, per-line atempo to target syll/s (default 6.4, cap 1.4x); best take by local whisper-large-v3-turbo CER; silencedetect onsets',
        overall_sps=sum(l['syllables'] for l in lines) / sum(c['duration'] for c in chosen), lines=lines, silences=sil, residual=bad), ensure_ascii=False, indent=1))
    for b in bad: print('RETAKE', *b)
    print('DONE', q, n, 'frames', round(n / FPS, 2), 's; first line', lines[0]['offset'], 's; cuts', [round(l['from_frame'] / FPS, 2) for l in lines])
if __name__ == '__main__': main(sys.argv[1])
