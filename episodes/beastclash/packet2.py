"""CEO evidence packet for a factory-built Beast Clash package (engine v2). Everything is derived from the episode spec
(episodes/specs/<id>.json: lines -> facts -> quotes -> source URLs) and the package files; nothing is typed in by hand
except the scope notes in the spec-side file episodes/specs/<id>.scope.md (optional, copied verbatim).
usage: packet2.py <id>   -> upload/pkg/<id>_B/ceo_packet/
  FINAL.txt, claims.md, rights.md, meta.txt, cover.jpg, sheet_1fps.png, audio/audio_numbers.{json,md}, audio/final_mix.wav,
  flash_screening.md"""
import sys, json, re, shutil, subprocess, hashlib
from pathlib import Path
import numpy as np, soundfile as sf
from PIL import Image, ImageDraw
D = Path(__file__).resolve().parent; W = D.parents[1]; q = sys.argv[1]; P = W / 'upload/pkg' / f'{q}_B'; O = P / 'ceo_packet'
O.mkdir(exist_ok=True); (O / 'audio').mkdir(exist_ok=True)
spec = json.loads((W / 'episodes/specs' / f'{q}.json').read_text()); c = json.loads((P / 'case.json').read_text()); V = P / 'video.mp4'
sha = hashlib.sha256(V.read_bytes()).hexdigest()

# ---- claims: line -> claim -> source URL -> verbatim quote
src = {s['id']: s for s in spec['sources']}; facts = {f['id']: f for f in spec['facts']}
md = [f'# {q} claims: line -> claim -> source -> verbatim quote', '',
      'Quotes are the snapshot text the factory checked at build time (episodes/specs/%s.sources; make_short.py step "facts").' % q, '']
scope = W / 'episodes/specs' / f'{q}.scope.md'
if scope.exists(): md += ['## Conditions and scope', '', scope.read_text().strip(), '']
for i, ln in enumerate(spec['lines']):
    f = facts[ln['fact']]; md += [f'## L{i + 1:02d} ({ln["beat"]}): "{ln["text"]}"', f'- claim {f["id"]}: {f["claim"]}']
    if ln['beat'] in ('clash', 'prompt', 'loop', 'face'): md.append('- kind: staging / dramatization line (hypothetical action); the fact is the reference it leans on')
    for qt in f['quotes']: md += [f'- {src[qt["source"]]["outlet"]}: {src[qt["source"]]["url"]}', f'  > "{qt["text"]}"']
    md.append('')
md += ['## On-screen numbers (stat captions)', '']
for st in c['stats']:
    md.append(f'- {st["label"]}: ' + ' | '.join(f'{c["title"][0 if s == "a" else 1]} {st[s]["big"]}' + (f' ({st[s]["small"]}, converted)' if st[s]['small'] else '') for s in ('a', 'b') if st.get(s)))
md += ['', '## Verdict screen', '', f'- heading: "{c["verdict"]["head"]}" / "{c["verdict"]["name"]}"; chip: "{c["verdict"]["note"]}"', '']
(O / 'claims.md').write_text('\n'.join(md))

# ---- meta, cover, 1 fps sheet, rights
shutil.copy(P / 'meta.txt', O / 'meta.txt'); shutil.copy(P / 'cover.jpg', O / 'cover.jpg')
if (P / 'rights.md').exists(): shutil.copy(P / 'rights.md', O / 'rights.md')
n = c['n']; secs = list(range(0, int(n / 30) + 1)); cols = 7; tw, th = 216, 384
sheet = Image.new('RGB', (cols * tw, -(-len(secs) // cols) * (th + 16)), '#111'); dr = ImageDraw.Draw(sheet)
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(V), '-vf', f'fps=1,scale={tw}:{th}', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, th, tw, 3)
for i in range(min(len(secs), len(fr))):
    sheet.paste(Image.fromarray(fr[i]), (i % cols * tw, i // cols * (th + 16) + 16)); dr.text((i % cols * tw + 4, i // cols * (th + 16) + 2), f'{i} s', fill='white')
sheet.save(O / 'sheet_1fps.png')

# ---- audio numbers (machine proxies)
ld = json.loads((P / 'loudness.json').read_text()); wh = json.loads((P / 'whisper.json').read_text())
x, sr = sf.read(P / 'mix_master.wav'); mono = x if x.ndim == 1 else x.mean(1); clip = int((np.abs(x) >= .999).sum())
e = np.sqrt(np.convolve(mono ** 2, np.ones(int(.05 * sr)) / int(.05 * sr), 'same')); quiet = e < 10 ** (-40 / 20); sil = []; k = 0
while k < len(quiet):
    if quiet[k]:
        j = k
        while j < len(quiet) and quiet[j]: j += 1
        if (j - k) / sr >= .5: sil.append([round(k / sr, 2), round(j / sr, 2)])
        k = j
    else: k += 1
words = sum(len(r['heard'].split()) for r in wh)
an = dict(integrated_lufs=ld['integrated_lufs'], true_peak_dbtp=ld['true_peak_dbtp'], clipped_samples=clip, silences_ge_0_5s=sil, sfx_events=len(ld['events']),
          whisper_min_match=min(r['match'] for r in wh), whisper_lines=wh, words_heard=words, words_per_s=round(words / (n / 30), 2), duration_s=round(n / 30, 2))
(O / 'audio/audio_numbers.json').write_text(json.dumps(an, indent=1)); shutil.copy(P / 'mix_master.wav', O / 'audio/final_mix.wav')
(O / 'audio/audio_numbers.md').write_text('\n'.join([f'# {q} audio numbers (final mix of video.mp4)', '',
    '**Machine proxies. They do not replace listening by ear on a phone speaker and on headphones; nobody has listened to this mix yet.**', '',
    f'- Loudness: {an["integrated_lufs"]} LUFS integrated, true peak {an["true_peak_dbtp"]} dBTP (ffmpeg ebur128 on video.mp4)',
    f'- Clipping: {clip} samples at |x| >= 0.999 in mix_master.wav', f'- Silences >= 0.5 s below -40 dB: {sil or "none"}',
    f'- SFX: {an["sfx_events"]} synthesized events (mix.py, numpy; no samples)',
    f'- Whisper (local mlx whisper-large-v3-turbo, offline) per narration line vs script: min match {an["whisper_min_match"]}',
    f'- Narration: {words} words heard by whisper in {an["duration_s"]} s = {an["words_per_s"]} words/s (digits count as one word)', '',
    '## Lines (expected -> heard)'] + [f'- {r["id"]} ({r["match"]}): "{r["expected"]}" -> "{r["heard"]}"' for r in wh]) + '\n')

# ---- objective flash screening
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(V), '-vf', 'scale=270:480', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], capture_output=True, check=True).stdout
F = np.frombuffer(raw, np.uint8).reshape(-1, 480, 270, 3).astype(np.float32) / 255
lin = np.where(F <= .04045, F / 12.92, ((F + .055) / 1.055) ** 2.4); Y = lin @ np.array([.2126, .7152, .0722], np.float32)
dm = Y[1:].mean((1, 2)) - Y[:-1].mean((1, 2)); frac = (np.abs(Y[1:] - Y[:-1]) >= .10).mean((1, 2))
tr = [(i + 1, 1 if dm[i] > 0 else -1) for i in range(len(dm)) if frac[i] >= .25 or abs(dm[i]) >= .20]
pairs = []; prev = None
for f_, s_ in tr:
    if prev and prev[1] != s_: pairs.append((prev[0], f_)); prev = None
    else: prev = (f_, s_)
mx = max((sum(1 for a, b in pairs if t0 <= b < t0 + 30) for t0 in range(max(1, len(Y) - 29))), default=0)
g = json.loads((P / 'gate/gate.json').read_text()); gi = {i['check']: i for i in g['items']}
(O / 'flash_screening.md').write_text('\n'.join([f'# {q} objective flash screening (screening, not a conformance claim)', '',
    f'Method: all {len(Y)} frames of video.mp4 at 270x480, sRGB -> linear relative luminance. Transition = at least 25% of pixels change by >= 0.10, '
    'or the frame mean changes by >= 0.20, in one direction. Flash = a pair of opposite-direction transitions. Screening threshold: 3 flashes in any 1 s.',
    '', f'- transitions: {len(tr)} (frames {[a for a, _ in tr][:40]})', f'- flash pairs: {len(pairs)} {pairs[:20]}', f'- max flashes in any 1 s window: {mx} (threshold 3)',
    f'- max frame-mean luminance step: {float(np.abs(dm).max()):.3f}', f'- gate.py flash_black_frames: {gi["flash_black_frames"]["status"]} — {gi["flash_black_frames"]["summary"]}', '',
    'This is an automated screening of luminance changes only. Red-flash and area-of-view criteria were not evaluated, the pixel threshold above is this script\'s own choice, '
    'and no photosensitivity conformance (e.g. WCAG 2.3.1, Harding) is claimed. Scene cuts count as transitions.']) + '\n')
np_ = [(i['check'], i['status']) for i in g['items'] if not i['status'].startswith('PASS')]
(O / 'FINAL.txt').write_text('\n'.join([f'final video: {V}', f'sha256: {sha}', f'cover: {P / "cover.jpg"}', 'meta: meta.txt (copied verbatim from the package)',
    f'spec: episodes/specs/{q}.json (factory/make_short.py build; engine v2: episodes/beastclash/Rig.tsx, Film.tsx, mix.py, build.py)',
    f'duration: {n} frames = {n / 30:.2f} s', f'gate.py: {sum(1 for i in g["items"] if i["status"].startswith("PASS"))}/{len(g["items"])} PASS; not PASS: {np_}',
    f'flash screening: max {mx} flashes in any 1 s (flash_screening.md; screening, not a conformance claim)',
    f'audio: {an["integrated_lufs"]} LUFS, {an["true_peak_dbtp"]} dBTP (audio/audio_numbers.md)', '1 fps sheet: sheet_1fps.png; claims: claims.md; rights: rights.md',
    'review status: frame sheets only. Nobody has watched the video at speed or listened to the mix. Not uploaded.']) + '\n')
print('PACKET', O, 'sha256', sha, 'flash max/1s', mx)
