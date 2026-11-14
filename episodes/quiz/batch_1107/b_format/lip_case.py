"""en/ja: copy look/v2/lipdata/<qid>.json rms into case.json 'lip_rms' (keeps the shared Lip.ts import list untouched).
usage: python3 look/v2/lipdata.py <qid> && python3 lip_case.py <qid>"""
import sys, json
from pathlib import Path
D = Path(__file__).resolve().parent; q = sys.argv[1]; P = D.parents[3] / 'upload/pkg' / f'{q}_B' / 'case.json'
c = json.loads(P.read_text()); c['lip_rms'] = json.loads((D / 'look/v2/lipdata' / f'{q}.json').read_text())['rms']
P.write_text(json.dumps(c, ensure_ascii=False, indent=1)); print('lip_rms', len(c['lip_rms']))
