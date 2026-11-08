#!/usr/bin/env python3
"""im-not-ai v2.3.2 gate on an episode's display text (owner 2026-10-26: C-8, C-11, I-4, E-2, F-5 must be zero).
Offline, deterministic. Uses the checkout's own metrics where it has one (C-8 antithesis, C-11 ending-comma regex)
and the taxonomy's definitions for the rest. usage: textgate.py q011 [...] — prints JSON per episode.
Display text = header, tags, stamps, cards, reveal/answer text, choices, source line, captions (narration)."""
import json, pathlib, re, sys
IMNA = pathlib.Path.home() / '.claude/jobs/myeotnyeon-cto/tools/im-not-ai/skills/humanize-korean/references'
sys.path.insert(0, str(IMNA))
import metrics_v2 as M  # noqa: E402
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
from episodes import EPISODES, CHOICES  # noqa: E402

TEXT_KEYS = ('text', 'lines', 'big', 'bigSub', 'title', 'chips', 'tag')


def labels(ep):
    out = [*ep['head'], ep['answerHead'], ep['source'], *ep.get('choices', CHOICES)]
    if ep.get('hook', {}).get('ask'):
        out.append(ep['hook']['ask'])
    def walk(x, k=None):
        if isinstance(x, dict):
            for kk, v in x.items():
                walk(v, kk)
        elif isinstance(x, list):
            for v in x:
                walk(v, k)
        elif isinstance(x, str) and k in TEXT_KEYS:
            out.append(x)
    for c in ep['cues']:
        walk(c[5])
    return out


def narration(ep):
    return [s for c in ep['cues'] for s in c[2]]


# C-11: comma right after a connective ending (-고/-며/-지만/-면서/-아서/-어서 per metrics.py, plus -자/-는데 per taxonomy)
C11 = re.compile(r'(?:고|며|지만|면서|아서|어서|는데|은데|던데|[가-힣]자)\s*,')
C8_PAIR = re.compile(r'([가-힣]+)(인가|일까|일까요)\s*[,?]\s*([가-힣]+)(인가|일까|일까요)')
I4 = re.compile(r'필요가 있|해야 한다|해야 합니다|해야 할 것|하는 것이 중요|이 필요하다')
F5 = re.compile(r'[가-힣]+적(?:인)?\s+[가-힣]+')
F5_STOP = {'목적', '흔적', '실적', '전적', '적적', '표적', '지적', '적', '국적', '업적', '창적', '사적', '공적', '타적', '적적', '서적', '좌적', '이적', '해적', '외적'}
PROG = re.compile(r'고\s*있(다|습니다|어요|었다|었습니다)')


def ending(s):
    s = re.sub(r'[^가-힣]+$', '', s.strip())
    return s[-2:]


def gate(eid):
    ep = EPISODES[eid]
    lab, nar = labels(ep), narration(ep)
    doc = '\n'.join(lab + nar)
    f5 = [m for m in F5.findall(doc) if m.split()[0] not in F5_STOP and not m.split()[0].endswith(('국적', '목적', '지적'))]
    runs, cur, best = [], 1, 1
    ends = [ending(s) for s in nar]
    for a, b in zip(ends, ends[1:]):
        cur = cur + 1 if a == b else 1
        best = max(best, cur)
    e2 = sum(1 for i in range(len(ends) - 3) if len(set(ends[i:i + 4])) == 1) + len(PROG.findall(doc))
    res = {
        'C-8': M.antithesis_count(doc) + len(C8_PAIR.findall(doc)),
        'C-11': len(C11.findall(doc)),
        'I-4': len(I4.findall(doc)),
        'E-2': e2,
        'F-5': len(f5),
    }
    detail = {'C-11': C11.findall(doc), 'F-5': f5, 'endings': ends, 'longest_same_ending_run': best,
              'risk_band': M.compute_all_v2('\n'.join(nar))['risk_band']}
    return dict(episode=eid, counts=res, passed=all(v == 0 for v in res.values()), detail=detail, n_labels=len(lab), n_sentences=len(nar))


if __name__ == '__main__':
    for q in sys.argv[1:]:
        print(json.dumps(gate(q), ensure_ascii=False))
