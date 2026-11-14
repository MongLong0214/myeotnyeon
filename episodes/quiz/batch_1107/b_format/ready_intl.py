"""READY.txt for en/ja B3 packages: measured numbers from the package files + the maker's own notes (notes file).
usage: ready_intl.py <qid> <notes.txt>"""
import sys, json, hashlib, re
from pathlib import Path
D = Path(__file__).resolve().parent; q, notes = sys.argv[1], Path(sys.argv[2]).read_text()
P = D.parents[3] / 'upload/pkg' / f'{q}_B'
c = json.loads((P / 'case.json').read_text()); a = json.loads((P / 'audio.json').read_text())
l = json.loads((P / 'loudness.json').read_text()); m = json.loads((P / 'measure.json').read_text())
U = {u['id']: u for u in c['utterances']}; sha = hashlib.sha256((P / 'video.mp4').read_bytes()).hexdigest()
g = json.loads((P / 'gate/gate.json').read_text()); items = g['items']
npass = sum(i['status'].startswith('PASS') for i in items)
rest = '\n'.join(f" - {i['check']} {i['status']}: {i['summary'][:150]}" for i in items if not i['status'].startswith('PASS'))
unit = 'mora/s' if c.get('locale') == 'ja' else 'syll/s'
txt = f"""{q.upper()}_B · {notes.splitlines()[0]}
File: upload/pkg/{q}_B/video.mp4  SHA256 {sha}
Spec: 1080x1920 · 30fps · {c['n']} frames ({c['duration']:.2f} s) · {l['integrated_lufs']} LUFS · peak {l['true_peak_dbtp']} dBTP
Build: episodes/quiz/batch_1107/b_format/build_intl.sh {q} (spec specs/{q}.json, locale {c.get('locale')}). B3 code shared with the Korean channel via i18n.ts.
Voice: {a['engine']}, voice {a['voice']}, local/offline. Overall {a['overall_sps']:.2f} {unit}; per-line atempo {min(u['atempo'] for u in c['utterances']):.2f}-{max(u['atempo'] for u in c['utterances']):.2f} (cap 1.4).
 Whisper check (local mlx whisper-large-v3-turbo) on every isolated clip: max CER {max(u['cer'] for u in c['utterances']):.3f}; residual retakes {a['residual'] or 'none'}.
Timing: first sentence ends {U['L01']['offset']:.2f} s; twist line starts {U['L04']['onset']:.2f} s; choices {c['choice_frame']/30:.2f} s; answer {c['answer_frame']/30:.2f} s; loop line -> frame 0.
B3 measure (measure_b3.py): motion {m['motion_pct']}%, {m['bg_changes_per_min']} background changes/min, longest same background {m['longest_same_bg_s']} s, loop diff {m['loop_diff']}/255.
Number pops with arithmetic: cues.md (bottom table).
gate.py --format shorts --lang {c.get('locale')}: overall {g['overall']}, {npass} PASS. Others:
{rest}
""" + '\n'.join(notes.splitlines()[1:]) + '\n'
(P / 'READY.txt').write_text(txt); print(txt[:400])
