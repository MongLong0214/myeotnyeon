"""Subtitle chunking for en/ja B3 specs (one cue = one line). Kokoro venv (fugashi + unidic-lite).
en: break at word boundaries, <= 32 chars per line, prefer breaks after , . ? !
ja: break at bunsetsu boundaries (content word + following particles/auxiliaries/suffixes, via MeCab/unidic-lite),
    <= 14 chars per line; a line never starts with small kana, a long-vowel mark or punctuation.
usage: linebreak.py <qid>   -> fills every line whose "chunks" is "auto" (or missing while "shown" is set) and prints them
       linebreak.py --check <qid>  -> only validates existing chunks"""
import sys, json, re
from pathlib import Path
D = Path(__file__).resolve().parent
EN_MAX, JA_MAX = 32, 14
NOSTART = set('ゃゅょぁぃぅぇぉっャュョァィゥェォッー、。，．,.!?！？」』）)・…〜')
WEAK = {'a','an','the','to','of','in','on','at','and','or','but','her','his','with','for','by','from','that','it','its','did','much','very','had','has','was'}
def balance(units, mx, sep=''):
    """split a list of unbreakable units into lines <= mx chars: balanced lengths, breaks after punctuation preferred,
    no orphan lines (DP over break points)."""
    import math
    n = len(units); L = lambda i, j: len(sep.join(units[i:j]))
    tot = L(0, n); k = max(1, math.ceil(tot / mx)); ideal = tot / k
    best = [0.0] + [math.inf] * n; prev = [0] * (n + 1)
    for j in range(1, n + 1):
        for i in range(j):
            ln = L(i, j)
            if ln > mx and j - i > 1: continue
            c = (ln - ideal) ** 2 + (400 if ln < 5 and n > 1 else 0) + (300 if j < n and re.sub(r'[^a-z]', '', units[j - 1].lower()) in WEAK else 0) - (60 if re.search(r'[,.?!:;、。？！]$', units[j - 1]) and j < n else 0) + 20
            if best[i] + c < best[j]: best[j] = best[i] + c; prev[j] = i
    out, j = [], n
    while j > 0: i = prev[j]; out.append(sep.join(units[i:j])); j = i
    return out[::-1]
EN_B3 = 28  # B3 phrase cues: aim shorter than the 32-char line limit so captions stay big inside title-safe
def en_chunks(t, mx=EN_B3):
    toks = []
    for w in t.split():  # a number stays with the word after it ("10 minutes", "$3,048 fine")
        if toks and re.fullmatch(r'\$?\d(?:[\d,.]*\d)?', toks[-1]): toks[-1] += ' ' + w
        else: toks.append(w)
    return balance(toks, mx, ' ')
_T = None
def bunsetsu(t):
    global _T
    import fugashi, unidic_lite
    if _T is None: _T = fugashi.Tagger('-d ' + unidic_lite.DICDIR)
    out = []; glue = False
    for w in _T(t):
        pos, sub = w.feature.pos1, w.feature.pos2
        attach = pos in ('助詞', '助動詞', '補助記号', '接尾辞') or sub == '非自立可能' and pos in ('動詞', '形容詞') or (out and out[-1][-1:] in '・' )
        # numbers + counters/units stay together (e.g. 50万円, 14回)
        num = out and re.search(r'[0-9０-９万億千百.]$', out[-1]) and (re.fullmatch(r'[0-9０-９万億千百.]+', w.surface) or '助数詞' in (w.feature.pos3 or ''))
        if out and (attach or num or glue): out[-1] += w.surface
        else: out.append(w.surface)
        glue = pos == '接頭辞'  # a prefix sticks to the next word
    return out
def ja_chunks(t, mx=JA_MAX):
    units = []
    for b in bunsetsu(t):  # a unit never starts with small kana / punctuation
        if units and b[0] in NOSTART: units[-1] += b
        else: units.append(b)
    for i in range(len(units) - 1):  # an opening bracket never ends a line
        while units[i] and units[i][-1] in '「『（(':
            units[i + 1] = units[i][-1] + units[i + 1]; units[i] = units[i][:-1]
    return balance([u for u in units if u], mx)
def chunks(t, L): return en_chunks(t) if L == 'en' else ja_chunks(t)
def check(ch, L):
    bad = []
    for x in ch:
        if L == 'en' and len(x) > EN_MAX: bad.append(f'>{EN_MAX}: {x}')
        if L == 'ja' and len(x) > JA_MAX: bad.append(f'>{JA_MAX}: {x}')
        if L == 'ja' and x[0] in NOSTART: bad.append(f'bad start: {x}')
    return bad
if __name__ == '__main__':
    only = sys.argv[1] == '--check'; q = sys.argv[-1]
    p = D / 'specs' / f'{q}.json'; spec = json.loads(p.read_text()); L = spec['locale']; bad = []
    for s in spec['lines']:
        if not s.get('shown'): continue
        if not only and (s.get('chunks') in (None, 'auto')): s['chunks'] = chunks(s['shown'], L)
        bad += [s['id'] + ' ' + b for b in check(s['chunks'], L)]
        print(s['id'], ' | '.join(s['chunks']))
    if not only: p.write_text(json.dumps(spec, ensure_ascii=False, indent=1))
    print('BAD' if bad else 'OK', *bad, sep='\n')
