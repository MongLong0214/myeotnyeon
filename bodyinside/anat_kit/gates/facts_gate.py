"""Facts gate. usage: python facts_gate.py EPISODE_DIR -> JSON, exit 1 on fail.
Every label/beat carrying a numeric or factual claim must have a `claim` id, and every claim id must have a row `| <id> |` in SOURCES.md. Also fails on forbidden wording
(a fixed timeline like '10년', inevitability words) anywhere in title, captions and labels."""
import sys, json, re, subprocess
E = sys.argv[1]; ep = json.load(open(E + '/episode.json')); src = open(E + '/SOURCES.md').read()
ids = {l['claim'] for l in ep.get('labels', []) if l.get('claim')}; rows = set(re.findall(r'^\|\s*([A-Z]\w*)\s*\|', src, re.M))
texts = list(ep['title']) + [''.join(t for t, _ in b['cap']) for b in ep['beats']] + [l['text'] + ' ' + l.get('sub', '') for l in ep.get('labels', [])]
texts.extend(line['text'] for line in ep.get('narration', []))
bad = [t for t in texts if re.search(r'\d+\s*년|반드시|무조건|100\s*%|확실히|(?:모두에게|모든 사람에게)[^.?!]*(?:생기|나타나)[^.?!]*아니', t)]
numeric_unsourced = [l['id'] for l in ep.get('labels', []) if re.search(r'\d', l['text'] + l.get('sub', '')) and not l.get('claim')]
ids.update(b['claim'] for b in ep['beats'] if b.get('claim'))
ids.update(c['source'] for c in ep.get('claims',[]))
if 'shots' in ep:
    numeric_unsourced.extend(f'beat {i}' for i,b in enumerate(ep['beats']) if b.get('cap') and not b.get('claim'))
miss = sorted(ids - rows); ok = not miss and not bad and not numeric_unsourced
out = dict(claim_ids=sorted(ids), missing_rows=miss, forbidden_wording=bad, numeric_without_claim=numeric_unsourced)
if ep.get('template') in ('neck_v3','wisdom'):
    from clinical import assess, claims, spoken_conditions
    from pathlib import Path
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
    from episode_template import validate
    validate(Path(E),ep)
    import media_checks
    screen_ok, out['screen_wording'] = media_checks.on_screen_wording(ep)
    out["spoken_conditions"] = spoken_conditions(ep)
    ok = ok and screen_ok and not out["spoken_conditions"]
    if ok:
        try:
            out['clinical'] = assess(ep, claims(ep))
            ok = out['clinical']['ok']
        except (OSError, ValueError, RuntimeError, KeyError, subprocess.TimeoutExpired) as exc:
            out['clinical'] = {'error':str(exc)}
            ok = False
else:
    ok = False
    out['clinical'] = {'error':'episode lacks a trusted source and condition template'}
print(json.dumps(dict(out, ok=ok), ensure_ascii=False))
sys.exit(0 if ok else 1)
