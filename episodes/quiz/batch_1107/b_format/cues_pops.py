"""append the number-pop table (shown text + arithmetic/source from the spec 'calc') to upload/pkg/<qid>_B/cues.md"""
import sys, json
from pathlib import Path
D = Path(__file__).resolve().parent; q = sys.argv[1]; P = D.parents[3] / 'upload/pkg' / f'{q}_B'
spec = json.loads((D / 'specs' / f'{q}.json').read_text()); c = json.loads((P / 'case.json').read_text())
U = {u['id']: u for u in c['utterances']}
o = ['', '## Number pops (on-screen) and arithmetic', '', '| line | frame | big | small | calculation / source |', '|---|---|---|---|---|']
for p in spec.get('pops', []):
    u = U[p['line']]; f = u['from_frame'] + round(p['at'] * u['dur'])
    o.append(f"| {p['line']} | {f} ({f/30:.2f}s) | {p['big']} | {p['small']} | {p['calc']} |")
o += [''] + [f'Note: {n}' for n in spec.get('cues_notes', [])]
o += ['', f"Locale {spec.get('locale','ko')} · voice {spec.get('engine','')} / {spec.get('voice','')}"]
with open(P / 'cues.md', 'a') as fh: fh.write('\n'.join(o) + '\n')
print('pops', len(spec.get('pops', [])))
