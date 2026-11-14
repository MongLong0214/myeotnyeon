"""CEO evidence packet for an en/ja B3 package -> upload/pkg/<qid>_B/ceo_packet/
claims.md (claims/<qid>.json: script line -> claim -> source -> verbatim quote, court/date/finality), voice.md (engine
licence vs voice terms), audio.md + loop_seam.png (objective audio proxies), meta.txt (verbatim copy), cover.jpg,
sheet_1fps.png, README.md (paths). Run with the Kokoro venv (mlx_whisper, pyopenjtalk, num2words, Pillow).
usage: ceo_packet.py <qid>"""
import sys, json, re, shutil, subprocess, difflib, os
from pathlib import Path
import numpy as np
D = Path(__file__).resolve().parent; W = D.parents[3]; sys.path.insert(0, str(D)); sys.path.insert(0, str(W / 'research/tts_kokoro'))
import intl
q = sys.argv[1]; P = W / 'upload/pkg' / f'{q}_B'; O = P / 'ceo_packet'; O.mkdir(exist_ok=True)
c = json.loads((P / 'case.json').read_text()); L = c['locale']; cl = json.loads((D / 'claims' / f'{q}.json').read_text())
V = P / 'video.mp4'
# 1 claims
h = cl['header']
md = [f'# {q} claims — script line → claim → source → original-language quote', '',
      *(f'- **{k}**: {v}' for k, v in h.items()), '',
      '| line | script / on-screen | claim | source | verbatim quote (original language) |', '|---|---|---|---|---|']
md += [f'| {a} | {b} | {cc} | {s} | {qq} |' for a, b, cc, s, qq in cl['items']]
md += ['', 'Quotes were copied from the article text fetched on 2026-11-13 (saved under ceo_packet/src/ where available).']
(O / 'claims.md').write_text('\n'.join(md) + '\n')
# 2 voice
a = json.loads((P / 'audio.json').read_text())
if L == 'ja':
    R = W / 'research/tts_voicevox'
    vm = ['# Voice licence record', '', f"Engine used: {a['engine']} · voice {a['voice']} · run locally (127.0.0.1), no audio sent anywhere.", '',
          '## 1. Engine (software) licence and terms — VOICEVOX ENGINE 0.26.1',
          '- Software licence: LGPL (VOICEVOX ENGINE), core MIT — from the engine bundle `licenses.json`; source https://github.com/VOICEVOX/voicevox_engine',
          '- Engine terms of use (bundled `engine_manifest_assets/terms_of_service.md`, copy: research/tts_voicevox/engine_terms_of_service.md):', '',
          *('> ' + l for l in (R / 'engine_terms_of_service.md').read_text().strip().splitlines()), '',
          '## 2. Voice / character terms — 冥鳴ひまり',
          '- In-engine policy (speaker_info, copy: research/tts_voicevox/policy_8eaad775-3119-417e-8cf4-2a10bfd592c8.md):', '',
          *('> ' + l for l in (R / 'policy_8eaad775-3119-417e-8cf4-2a10bfd592c8.md').read_text().strip().splitlines()), '',
          '- Character terms page https://meimeihimari.wixsite.com/himari/terms-of-use (fetched 2026-11-13, copy: research/tts_voicevox/himari_terms_of_use_web.txt):', '',
          '> １．VOICEVOX冥鳴ひまりは商用、非商用ともにご利用いただけます', '> ２．個人、法人問わずご利用いただけますので、申請や報告は必要ありません',
          '> ３．利用の際はクレジット表記をしてください', '> 禁止事項 １．公序良俗に反する行為 ２．第三者に不利益・損害を与える行為 ３．特定の思想・団体に当たる行為 ４．冥鳴ひまりが不適切と判断する行為',
          '> Q：収益化する際報告やリンクは必要ですか？ A：特に必要ありません。', '',
          'Credit used in the description: 「ナレーション: VOICEVOX:冥鳴ひまり（ローカルAI音声合成）」 — satisfies both the engine credit (VOICEVOX) and the voice credit.',
          'Judgement item (not a licence condition we can verify): 禁止事項4「冥鳴ひまりが不適切と判断する行為」 is discretionary; crime/court news narration is not listed as prohibited.']
else:
    vm = ['# Voice licence record', '', f"Engine used: {a['engine']} · voice {a['voice']} · run locally, offline (HF_HUB_OFFLINE=1), no audio sent anywhere.", '',
          '## Engine and voice: Kokoro-82M (hexgrad/Kokoro-82M) — one licence covers code, weights and voicepacks',
          '- Licence: Apache-2.0 — model card https://huggingface.co/hexgrad/Kokoro-82M (license: apache-2.0); code https://github.com/hexgrad/kokoro (Apache-2.0).',
          '- Model card text: "Kokoro is an open-weight TTS model with 82 million parameters. ... with Apache-licensed weights, Kokoro can be deployed anywhere from production environments to personal projects."',
          '- The af_heart voicepack ships in the same Apache-2.0 repository (voices/af_heart.pt); there are no separate character terms.',
          '- Apache-2.0 requires no on-screen credit; the description names the engine and voice anyway (AI-voice disclosure).']
(O / 'voice.md').write_text('\n'.join(vm) + '\n')
# 3 audio proxies
wav = O / '_audio.wav'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(V), '-ac', '1', '-ar', '16000', str(wav)], check=True)
import mlx_whisper
M = next(Path('/Users/isaac/.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots').glob('*/weights.safetensors')).parent
r = mlx_whisper.transcribe(str(wav), path_or_hf_repo=str(M), language=L, temperature=0, condition_on_previous_text=False, verbose=None)
heard = r['text'].strip(); script = ' '.join(u['tts'] for u in c['utterances'])
nh, ns = intl.norm(heard, L), intl.norm(script, L)
sm = difflib.SequenceMatcher(None, ns, nh); ops = [(t, ns[i1:i2], nh[j1:j2]) for t, i1, i2, j1, j2 in sm.get_opcodes() if t != 'equal']
cer = 1 - sm.ratio()
eb = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(V), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
sm_ = eb[eb.rindex('Summary:'):]; I = re.search(r'I:\s+(-?[\d.]+) LUFS', sm_)[1]; TP = re.search(r'Peak:\s+(-?[\d.]+) dBFS', sm_)[1]; LRA = re.search(r'LRA:\s+(-?[\d.]+) LU', sm_)[1]
raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(V), '-ac', '2', '-ar', '48000', '-f', 'f32le', '-'], capture_output=True, check=True).stdout
x = np.frombuffer(raw, np.float32).reshape(-1, 2); clip = int((np.abs(x) >= 0.999).sum())
sd = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(V), '-af', 'silencedetect=noise=-40dB:d=0.5', '-f', 'null', '-'], capture_output=True, text=True).stderr
sil = list(zip(re.findall(r'silence_start: ([\d.]+)', sd), re.findall(r'silence_duration: ([\d.]+)', sd)))
# loop seam: last 1 s + first 1 s, mono envelope
from PIL import Image, ImageDraw
mono = x.mean(1); sr = 48000; a_ = mono[-sr:]; b_ = mono[:sr]; seg = np.concatenate([a_, b_])
im = Image.new('RGB', (1200, 300), '#111'); d = ImageDraw.Draw(im); step = len(seg) / 1200
for i in range(1200):
    s = seg[int(i * step):int((i + 1) * step)]; mx = float(np.abs(s).max()) if len(s) else 0
    d.line([(i, 150 - mx * 140), (i, 150 + mx * 140)], fill='#6cf' if i < 600 else '#fc6')
d.line([(600, 0), (600, 300)], fill='white'); d.text((8, 6), 'last 1.0 s of video', fill='white'); d.text((608, 6), 'first 1.0 s (loop restart)', fill='white')
im.save(O / 'loop_seam.png')
rms = lambda s: 20 * np.log10(np.sqrt(np.mean(s ** 2)) + 1e-9)
am = ['# Objective audio proxies — these do NOT replace listening on headphones/phone; no one has judged naturalness by ear', '',
      f'File: {V}', '',
      '## Whisper (local mlx whisper-large-v3-turbo, full final mix) vs script',
      f'- normalised comparison ({"katakana reading" if L == "ja" else "letters, numbers spelled out"}): similarity {sm.ratio():.3f} (≈ CER {cer:.3f})',
      f'- heard: {heard}', '- note: the comparison is phonetic (ja: katakana reading; en: letters with numbers spelled out), so homophones/kanji choices (e.g. 拘禁刑 vs 公金刑 in the transcript) count as equal — the transcript text shows what whisper wrote.', f'- script (TTS text): {script}', '- differences (script → heard):',
      *(f'  - {t}: `{s or "∅"}` → `{h_ or "∅"}`' for t, s, h_ in ops[:40]),
      '- per-line isolated-clip check (pace.py): ' + ', '.join(f"{u['id']} {u['cer']:.3f}" for u in c['utterances']), '',
      '## Loudness', f'- integrated {I} LUFS, true peak {TP} dBTP, LRA {LRA} LU (ffmpeg ebur128 on the final MP4)', '',
      '## Clipping', f'- samples with |x| ≥ 0.999 (48 kHz stereo float decode): {clip}', '',
      '## Silence scan (-40 dB, ≥ 0.5 s)', *([f'- at {s} s for {du} s' for s, du in sil] or ['- none']), '',
      '## Loop seam', f'- loop_seam.png: last 1 s | first 1 s. RMS last 0.25 s {rms(mono[-sr//4:]):.1f} dBFS, first 0.25 s {rms(mono[:sr//4]):.1f} dBFS.',
      '- The narration ends with the loop line, then a 0.25 s digital-silence tail (by design in pace.py), and the video restarts on the first line after a 0.03 s lead-in; see the image for the jump.']
(O / 'audio.md').write_text('\n'.join(am) + '\n'); wav.unlink()
# 4 meta, cover, 1 fps sheet
shutil.copy(P / 'meta.txt', O / 'meta.txt'); shutil.copy(P / 'cover.jpg', O / 'cover.jpg')
n = c['n'] // 30 + 1; rows = (n + 5) // 6
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(V), '-vf', f"fps=1,scale=216:384,drawtext=text='%{{pts\\:hms}}':x=4:y=4:fontsize=18:fontcolor=white:box=1:boxcolor=black@0.6,tile=6x{rows}", '-frames:v', '1', str(O / 'sheet_1fps.png')], check=True)
g = json.loads((P / 'gate/gate.json').read_text())
gr = [f"# Gate residuals — {q} (gate.py --format shorts --lang {L}), overall {g['overall']}", '',
      f"{sum(i['status'].startswith('PASS') for i in g['items'])} PASS; non-PASS items below with the maker's reading.", '',
      '| id | check | status | summary |', '|---|---|---|---|']
gr += [f"| {i['id']} | {i['check']} | {i['status']} | {i['summary'][:160]} |" for i in g['items'] if not i['status'].startswith('PASS')]
gr += ['', 'Standing readings: repeated_compositions = the loop ending replays frame 0 by design (plus reused card desks); manual_signoff = needs the reviewer log; hook_text_over_face = head boxes near the hook band (checked on the evidence images in gate/evidence/).']
(O / 'gate_residuals.md').write_text('\n'.join(gr) + '\n')
import hashlib
sha = hashlib.sha256(V.read_bytes()).hexdigest()
(O / 'README.md').write_text('\n'.join([f'# CEO packet {q}', '', f'- final MP4: {V} (sha256 {sha})', f'- cover: {O / "cover.jpg"}', f'- meta (verbatim): {O / "meta.txt"}',
    f'- claims: {O / "claims.md"}', f'- voice licence: {O / "voice.md"}', f'- audio proxies: {O / "audio.md"} + {O / "loop_seam.png"}', f'- 1 fps sheet: {O / "sheet_1fps.png"}',
    f'- full every-frame contact sheets: {P / "sheets"}', f'- gate: {P / "gate/gate.md"} (residuals: {O / "gate_residuals.md"})', f'- READY: {P / "READY.txt"}', '',
    'Objective proxies only; nobody has listened for naturalness. Not uploaded.']) + '\n')
print('packet', O, 'whisper sim', round(sm.ratio(), 3), 'LUFS', I, 'TP', TP, 'clip', clip, 'silences', len(sil))
