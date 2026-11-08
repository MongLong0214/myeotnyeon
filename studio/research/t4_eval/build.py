"""Build the frozen T4 evaluation set described in prereg.md. Inputs are read, never modified."""
import hashlib, json, math, re
from pathlib import Path

HERE = Path(__file__).resolve().parent
RESEARCH = HERE.parent
WORK = RESEARCH.parent
INPUTS = {
    'viral_candidates': RESEARCH / 'viral_candidates.json',
    'agent3_comparables': RESEARCH / 'agent3_comparables.jsonl',
    'episodes': WORK / 'episodes/quiz/episodes.py',
    'prereg': HERE / 'prereg.md',
}
CAR = {'k003': ['A3-013'], 'k004': ['A3-020', 'A3-052'], 'k005': ['A3-003']}
USED = {'V2-05', 'V2-11', 'V2-01', 'V2-02', 'V2-10'}


def sha(path):
    return 'sha256:' + hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    v2 = json.loads(INPUTS['viral_candidates'].read_text())
    a3 = {}
    for line in INPUTS['agent3_comparables'].read_text().splitlines():
        if line.strip():
            record = json.loads(line)
            a3[record['id']] = record
    shelved = INPUTS['episodes'].read_text()
    for key, sources in CAR.items():  # the SHELVED entry must still name exactly these sources
        found = re.search(rf"'{key}':.*?sources=\[([^\]]*)\]", shelved, re.S)
        assert found and re.findall(r"'([^']+)'", found.group(1)) == sources, key

    assert len(v2) == 14 and USED <= {c['id'] for c in v2}
    max_comments = max(c['max_naver_comments'] for c in v2)
    max_publishers = max(c['independent_publishers'] for c in v2)
    rows = []
    for c in v2:
        rows.append((c['id'], [{'title': s['title']} for s in c['sources']], {
            'engagement': math.log1p(c['max_naver_comments']) / math.log1p(max_comments),
            'crossPlatformSpread': c['independent_publishers'] / max_publishers,
        }))
    for key, sources in CAR.items():
        rows.append((key, [{'title': a3[s]['title']} for s in sources], {'engagement': None, 'crossPlatformSpread': None}))
    rows.sort(key=lambda row: row[0])

    nulls = dict.fromkeys(['velocity', 'trendSlope', 'expectationGap', 'reversal', 'recency', 'drawability',
                           'youtubeCompetition', 'outrageMarkers'])
    clusters, labels, key_map = [], [], {}
    for n, (case, articles, measured) in enumerate(rows, 1):
        cid = f'c{n:02d}'
        key_map[cid] = case
        clusters.append({'id': cid, 'articles': articles, 'verdictConfirmed': True, 'signals': {**nulls, **measured}})
        labels.append({'id': cid, 'used': case in USED})
    symmetric = [{**c, 'signals': {**c['signals'], 'engagement': None, 'crossPlatformSpread': None}} for c in clusters]

    outputs = {'clusters.json': clusters, 'clusters_symmetric.json': symmetric, 'labels.json': labels, 'key_map.json': key_map}
    for name, data in outputs.items():
        (HERE / name).write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n')
    manifest = {
        'inputs': {name: {'path': str(path.relative_to(WORK)), 'digest': sha(path)} for name, path in INPUTS.items()},
        'outputs': {name: sha(HERE / name) for name in outputs},
        'builder': sha(Path(__file__)),
        'population': len(clusters), 'used': sum(l['used'] for l in labels), 'k': 7,
        'tieRule': 'pessimistic: ranked and fewer than 7 other ranked candidates score >= it',
    }
    (HERE / 'manifest.json').write_text(json.dumps(manifest, indent=1) + '\n')
    print(json.dumps({k: manifest[k] for k in ('population', 'used', 'k')}))


if __name__ == '__main__':
    main()
