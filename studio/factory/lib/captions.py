# Portions adapted from cinecode (MIT) - https://github.com/sarpstar/cinecode @67f9807,
# scripts/captions.py (word-timing grouping on pauses and clause ends) and references/craft.md §5.
# The Korean particle/unit rules, recursive phrase split, balanced wrap and hold rule are ours.
#
# MIT License
#
# Copyright (c) 2026 Sarp Yıldız (@sarpstar)
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
"""Shared Korean subtitle splitter for long-forms and Shorts (stdlib + ffmpeg).

  python -m factory.lib.captions WORDS.json [--audio NARRATION.wav] [--format longform|shorts]
         [--fps 30] [--offset 0] [--out captions.json]

Inputs: local Whisper word timings (mlx_whisper/openai-whisper JSON) and ffmpeg
`silencedetect` pauses. Rules:
- a cue breaks at a sentence end or a pause >= `gap` (default 0.22 s); a cue
  longer than two lines is split only at a phrase end (comma, connective ending,
  particle-ended noun phrase), never between a number and its unit and never
  before a stand-alone particle;
- at most 2 lines of about `line_max` characters (18 long-form, 16 Shorts),
  wrapped to balanced lengths; a one-word last line takes one word from above;
- hold = max(1.8 s, speech + 0.6 s) unless the next cue starts first.
Output rows: long-form {start,end,text} in seconds (Captions.tsx; `\n` between
lines, pre-line), Shorts {from_,to,text} in frames (render.json subtitles).
"""
import argparse
import json
import re
import subprocess
from pathlib import Path

PARTICLES = {
    # Stand-alone forms Whisper sometimes spaces off. '이', '나', '도', '만', '그' are left out: they are also
    # ordinary words (this, I, degree, ten thousand).
    '은', '는', '가', '을', '를', '에', '에서', '에게', '에게서', '께서', '의', '와', '과', '로', '으로', '까지',
    '부터', '한테', '처럼', '보다', '이나', '라고', '이라고', '마저', '조차', '밖에', '이다', '입니다', '였다',
    '이었다', '였습니다', '이었습니다', '요',
}
MAGNITUDE = ('억', '만', '천', '백')
# Counting words that belong to the next word: 한 사람, 두 가방, 약 20년.
# Bound nouns that cannot open a line: 뇌진탕 등, 실형 중.
DEPENDENT = {'등', '중', '때', '뿐', '쯤', '간'}
NUMERAL_DET = {'한', '두', '세', '네', '다섯', '여섯', '몇', '첫', '약', '총', '단'}
UNITS = (
    '퍼센트', '개월', '시간', '달러', '차례', '킬로', '원', '억', '만', '천', '백', '명', '년', '월', '일', '시', '분',
    '초', '대', '쪽', '건', '번', '회', '살', '세', '배', '개', '곳', '장', '권', '층', '호', '위', '등', '점', '표',
    '톤', '주', '평', '%', 'km', 'kg', 'cm', 'mm', 'm',
)
CONNECTIVE = ('면서', '지만', '는데', '은데', '니까', '거나', '든지', '려고', '려다', '다가', '고', '며', '서', '면')
CASE_END = ('에서', '에게', '으로', '까지', '부터', '이', '가', '을', '를', '로', '에', '와', '과', '도', '의',
            '엔', '에선', '으론', '로는', '에는', '에도', '처럼')
# -은/-는 is a topic marker (법원은) or a modifier ending (검은, 하는): a weaker phrase end.
TOPIC_END = ('은', '는')
SENTENCE_END = re.compile(r'[.?!…]+["\'”’)\]]*$')
CLAUSE_END = re.compile(r'[,;:·]["\'”’)\]]*$')
NUMBER_TOKEN = re.compile(r'^[\d][\d,.\-]*[가-힣%a-zA-Z]{0,3}$')
ENDS_DIGIT = re.compile(r'\d[\d,.]*$')
HOLD_MIN, HOLD_TAIL = 1.8, 0.6


def load_words(source, offset=0.0, display=None):
    """Whisper JSON -> eojeol tokens. A piece without a leading space continues the previous word."""
    data = json.loads(Path(source).read_text()) if isinstance(source, (str, Path)) else source
    if isinstance(data, dict):
        data = data.get('words') or [w for s in data.get('segments', []) for w in s.get('words', [])]
    rows = []
    for w in data:
        if isinstance(w, (list, tuple)):
            rows.append((w[0], float(w[1]), float(w[2])))
        else:
            rows.append((w.get('word', w.get('text', '')), float(w['start']), float(w['end'])))
    # Whisper marks a new eojeol with a leading space; only trust that when the source keeps spaces.
    spaced = any(raw[:1].isspace() for raw, _, _ in rows)
    tokens = []
    for raw, a, b in rows:
        text = raw.strip()
        if not text:
            continue
        if spaced and tokens and not raw[:1].isspace():
            tokens[-1]['text'] += text
            tokens[-1]['end'] = max(tokens[-1]['end'], b + offset)
            continue
        tokens.append(dict(text=text, start=a + offset, end=max(b, a) + offset))
    if display:
        for t in tokens:
            t['text'] = display(t['text'])
    return tokens


def silences_from_audio(audio, noise='-45dB', min_dur=0.2):
    """ffmpeg silencedetect -> [(start, end)] in seconds."""
    log = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(audio), '-af',
                          f'silencedetect=n={noise}:d={min_dur}', '-f', 'null', '-'],
                         capture_output=True, text=True, check=True).stderr
    starts = [float(x) for x in re.findall(r'silence_start: (-?[\d.]+)', log)]
    ends = [float(x) for x in re.findall(r'silence_end: (-?[\d.]+)', log)]
    return [(max(0.0, a), b) for a, b in zip(starts, ends)]


def is_particle(text):
    return re.sub(r'[^\w%]', '', text) in PARTICLES


def glued(a, b, strict=False):
    """True when no line may break between token texts a and b; `strict` (cue level) also keeps dates whole."""
    if is_particle(b) or a in NUMERAL_DET or re.sub(r'[^가-힣]', '', b) in DEPENDENT:
        return True
    if SENTENCE_END.search(a):
        return False
    if strict and NUMBER_TOKEN.match(a) and NUMBER_TOKEN.match(b):
        return True
    if (ENDS_DIGIT.search(a) or NUMBER_TOKEN.match(a)) and b.startswith(UNITS) and not NUMBER_TOKEN.match(b):
        return True
    # 2억 1천만 원: one amount. Dates (2001년 12월) may wrap between their parts.
    return bool(NUMBER_TOKEN.match(a) and NUMBER_TOKEN.match(b) and a.endswith(MAGNITUDE))


def priority(text):
    """How good a phrase end the token makes: 3 clause punctuation, 2 connective ending, 1 particle-ended phrase."""
    if SENTENCE_END.search(text):
        return 4
    if CLAUSE_END.search(text):
        return 3
    core = re.sub(r'[^가-힣]', '', text)
    if len(core) >= 2 and core.endswith(CONNECTIVE):
        return 2
    if len(core) >= 2 and core.endswith(CASE_END):
        return 1
    if len(core) >= 2 and core.endswith(TOPIC_END):
        return 0.5
    return 0


# ---- Korean bonds: how strongly token a holds on to the next token b (0 free .. 3 never break if avoidable) ----
# Bound (dependent) nouns and positional nouns that cannot open a line: 시작한 | 건, 배포할 | 수, 20분 | 안에, 면접 | 끝.
BOUND = ('것', '수', '건', '데', '줄', '때', '뿐', '만', '듯', '채', '바', '적', '지', '안', '위', '밖', '끝', '앞', '뒤',
         '전', '후', '중', '등', '쯤', '간', '동안')
BOUND_TAIL = ('', '이', '가', '은', '는', '을', '를', '에', '에서', '에는', '도', '만', '으로', '로', '의', '과', '와',
              '이다', '입니다', '이에요', '예요', '인', '이었다', '이었습니다', '였어요', '이죠', '죠')
# Auxiliary verbs after -어/-아/-고: 숨어 | 있었다는, 보여 | 주며.
AUX_HEAD = ('있', '없', '주', '줬', '줍', '보', '봤', '싶', '버리', '버렸', '놓', '두', '뒀')
AUX_TAIL = ('어', '아', '여', '해', '고', '져', '워', '와', '봐', '줘', '내')
# Adnominal (modifier) endings that need their head noun: 시작한 | 건, 대표라는 | 사람이, 올라간 | SNS, 같은 | 방식으로.
ADNOM_WORDS = ('라는', '다는', '하는', '되는', '있는', '없는', '같은', '쫓는', '꾸는', '드는', '주는', '보는', '오는',
               '가는', '쓰는', '하던', '되던', '않은', '않는', '숨은', '털린', '훔친', '섞인', '묶인', '보낸', '앞선',
               '막은', '잡은', '받은', '찾은', '넣은', '남은', '맡은', '얻은', '읽은', '움직인')
ADNOM_LAST = set('한된할될던간인운온진친른린낸긴즌')
# Endings that make a word a predicate / clause end rather than a bare noun or adverb.
VERBAL_LAST = set('다요죠고며면서지데니게나야까든라네군')


def core(text):
    return re.sub(r'[^가-힣A-Za-z0-9]', '', text)


def is_bound(b):
    c = re.sub(r'[^가-힣]', '', b)
    return any(c == f + tail for f in BOUND for tail in BOUND_TAIL) and not NUMBER_TOKEN.match(b)


def is_adnominal(a):
    c = re.sub(r'[^가-힣]', '', a)
    if not c or CLAUSE_END.search(a) or SENTENCE_END.search(a) or NUMBER_TOKEN.match(a):
        return False
    return c.endswith(ADNOM_WORDS) or (len(c) >= 2 and c[-1] in ADNOM_LAST)


def bond(a, b):
    """0 = a natural break between a and b; 3 = breaking here splits a grammatical unit (avoid if any other option)."""
    if SENTENCE_END.search(a) or CLAUSE_END.search(a):
        return 0
    cb = re.sub(r'[^가-힣]', '', b)
    ca = re.sub(r'[^가-힣]', '', a)
    if is_bound(b):
        return 3
    if re.fullmatch(r'\d+월', a) and re.match(r'\d+일', b):
        return 3  # a date stays together: 10월 | 20일
    if ca.endswith(AUX_TAIL) and cb.startswith(AUX_HEAD) and len(ca) >= 2:
        return 3
    if ca.endswith('지') and cb.startswith(('못', '않', '말')) and len(ca) >= 2:
        return 3  # negation: 잡지 | 못했어요
    if is_adnominal(a):
        return 3
    if a in NUMERAL_DET or re.sub(r'[^가-힣]', '', a) in NUMERAL_DET:
        return 3
    if priority(a) == 0 and ca.endswith('히') and len(ca) >= 2:
        return 2  # -히 adverb before its verb: 영원히 | 처벌할 (avoid, but better than a scrap cue)
    if priority(a) == 0 and ca and ca[-1] not in VERBAL_LAST and not a.endswith(('은', '는', '을')) \
            and not NUMBER_TOKEN.match(a):
        return 3  # bare noun / adverb holds its head: 지갑 | 관리팀의, 회사 내부 | AI 도구를, 왜 | 바로
    if not ca and core(a) and priority(a) == 0:
        return 3  # Latin token (AI, SNS) followed by its noun
    if is_adnominal(b) and ca.endswith(('거나', '이', '가', '을', '를', '에', '에서', '과', '와')):
        return 3  # an argument stays with its relative clause: 영상이 | 올라간, 대부분이 | 움직인
    if ca.endswith('의') and len(ca) >= 2:
        return 2  # genitive holds its noun: 법원의 | 유죄 판단
    if ca.endswith(('과', '와')) and len(ca) >= 2 and not cb[-1:] in VERBAL_LAST:
        return 2  # noun coordination (사진과 | 영상이): avoid on a line; never at a cue end (split_long)
    if a.endswith(('은', '는', '을')) and priority(a) < 1:
        return 1
    return 0


def paused(tokens, i, silences, gap):
    """Is there a pause >= gap between tokens i and i+1 (word gap or a detected silence between their centres)?"""
    a, b = tokens[i], tokens[i + 1]
    if b['start'] - a['end'] >= gap:
        return True
    lo, hi = (a['start'] + a['end']) / 2, (b['start'] + b['end']) / 2
    return any(e - s >= gap and lo <= (s + e) / 2 <= hi for s, e in silences)


def width(tokens):
    return len(' '.join(t['text'] for t in tokens))


def fits(tokens, line_max):
    """Wraps into lines of at most line_max without splitting a grammatical unit (bond 3) between the lines."""
    lines = wrap(tokens, line_max)
    if not all(width(line) <= line_max for line in lines):
        return False
    return len(lines) < 2 or bond(lines[0][-1]['text'], lines[1][0]['text']) < 3


def split_long(tokens, line_max, min_side=8, soft=frozenset()):
    """Recursively split a run that does not wrap into two lines at the best phrase end.

    `soft` holds token ids followed by a pause that was not a phrase end: a weak candidate."""
    if fits(tokens, line_max) or len(tokens) < 2:
        return [tokens]
    cands = []
    for j in range(len(tokens) - 1):
        if glued(tokens[j]['text'], tokens[j + 1]['text'], strict=True):
            continue
        left, right = tokens[:j + 1], tokens[j + 1:]
        ok = fits(left, line_max) and fits(right, line_max)
        whole = min(width(left), width(right)) >= min_side  # no one-word scrap cue
        rank = max(priority(tokens[j]['text']), 1 if id(tokens[j]) in soft else 0)
        bd = bond(tokens[j]['text'], tokens[j + 1]['text'])
        if re.sub(r'[^가-힣]', '', tokens[j]['text']).endswith(('과', '와')) and not CLAUSE_END.search(tokens[j]['text']):
            bd = 3  # a cue must not end mid-coordination
        cands.append((bd < 2, bd < 3, ok, -bd, whole, rank, -abs(width(left) - width(right)), j))
    if not cands:
        return [tokens]
    *_, j = max(cands)
    return split_long(tokens[:j + 1], line_max, min_side, soft) + split_long(tokens[j + 1:], line_max, min_side, soft)


SOFT_LINE = 18  # a cue up to this width stays on one line; longer cues wrap (each line may reach line_max)


def wrap(tokens, line_max):
    """At most two balanced lines; a single-word last line takes one word from above."""
    if width(tokens) <= min(line_max, SOFT_LINE) or len(tokens) < 2:
        return [tokens]
    cands = []
    for j in range(len(tokens) - 1):
        if glued(tokens[j]['text'], tokens[j + 1]['text']):
            continue
        a, b = tokens[:j + 1], tokens[j + 1:]
        # Balance in 3-char steps so a phrase end can win over a near-equal split.
        pr = priority(tokens[j]['text'])
        lone = len(b) == 1 and len(a) >= 2  # a last line that is a lone predicate (…/ 있었습니다.)
        bd = bond(tokens[j]['text'], tokens[j + 1]['text'])
        cands.append((max(width(a), width(b)) <= line_max, -max(bd - 1, 0), pr >= 3,
                      -(abs(width(a) - width(b)) // 4), pr, not lone, -bd, j))
    if not cands:
        return [tokens]
    *_, j = max(cands)
    top, bottom = tokens[:j + 1], tokens[j + 1:]
    # Orphan: a one-word last line much shorter than the line above.
    if len(bottom) == 1 and len(top) >= 2 and width(bottom) * 2 < width(top) \
            and not glued(top[-2]['text'], top[-1]['text']) and width(top[-1:] + bottom) <= line_max \
            and bond(top[-2]['text'], top[-1]['text']) == 0:
        top, bottom = top[:-1], top[-1:] + bottom
    return [top, bottom]


def split(tokens, silences=(), line_max=18, gap=0.22, hold_min=HOLD_MIN, hold_tail=HOLD_TAIL):
    """Tokens (text/start/end, seconds) -> cues with lines and hold times."""
    tokens = [t for t in tokens if t['text']]
    runs, cur, soft = [], [], set()
    for i, t in enumerate(tokens):
        cur.append(t)
        if i == len(tokens) - 1 or SENTENCE_END.search(t['text']) or t.get('hard'):
            runs.append(cur)
            cur = []
        elif not glued(t['text'], tokens[i + 1]['text'], strict=True) and paused(tokens, i, silences, gap):
            # A pause ends a cue only at a phrase end; after a modifier (검은 | 그랜저가) it stays a weak candidate.
            if priority(t['text']) >= 1 and bond(t['text'], tokens[i + 1]['text']) < 2:
                runs.append(cur)
                cur = []
            else:
                soft.add(id(t))
    # A pause that leaves a scrap (돌아갑니다. alone) is folded back; split_long then re-splits at a phrase end.
    merged = []
    for run in runs:
        prev = merged[-1] if merged else None
        if prev and not SENTENCE_END.search(prev[-1]['text']) and not prev[-1].get('hard') and min(width(prev), width(run)) < 6:
            prev.extend(run)
        else:
            merged.append(run)
    parts = [g for run in merged for g in split_long(run, line_max, soft=frozenset(soft))]
    # Rule 5: a short or mid-phrase cue is merged with its neighbour (same sentence) when the two fit in two lines.
    groups = []
    for p in parts:
        prev = groups[-1] if groups else None
        if prev and not SENTENCE_END.search(prev[-1]['text']) and not prev[-1].get('hard') and fits(prev + p, line_max) \
                and (min(width(prev), width(p)) < 8 or bond(prev[-1]['text'], p[0]['text']) >= 2):
            groups[-1] = prev + p
        else:
            groups.append(p)
    cues = []
    for g in groups:
        lines = wrap(g, line_max)
        cues.append(dict(start=g[0]['start'], speech_end=g[-1]['end'], group=g[0].get('group'),
                         lines=[' '.join(t['text'] for t in line) for line in lines],
                         tokens=[t['text'] for t in g]))
    for k, c in enumerate(cues):
        end = c['start'] + max(hold_min, c['speech_end'] - c['start'] + hold_tail)
        if k + 1 < len(cues):
            end = min(end, cues[k + 1]['start'])
        c['end'] = max(end, c['speech_end'])
        c['text'] = '\n'.join(c['lines'])
    return cues


NORM = re.compile(r'[^0-9a-z가-힣]')


def align_text(text, words, window=None):
    """Authored display text timed by ASR words (character match; unmatched words interpolated).

    The subtitle shows the script's words (digits, names), never the ASR spelling."""
    targets = [w for w in text.split() if w]
    asr_chars, times = '', []
    for w in words:
        n = NORM.sub('', w['text'].lower())
        asr_chars += n
        times += [(w['start'] + (w['end'] - w['start']) * i / max(1, len(n)),
                   w['start'] + (w['end'] - w['start']) * (i + 1) / max(1, len(n))) for i in range(len(n))]
    target = ''.join(NORM.sub('', w.lower()) for w in targets)
    import difflib
    m = difflib.SequenceMatcher(None, asr_chars, target, autojunk=False)
    at = {b + j: times[a + j] for a, b, n in m.get_matching_blocks() for j in range(n)}
    lo, hi = window or ((words[0]['start'], words[-1]['end']) if words else (0.0, 0.0))
    out, pos = [], 0
    for w in targets:
        n = len(NORM.sub('', w.lower()))
        hits = [at[k] for k in range(pos, pos + n) if k in at]
        out.append(dict(text=w, start=min(h[0] for h in hits) if hits else None,
                        end=max(h[1] for h in hits) if hits else None, chars=max(1, n),
                        open_start=pos not in at, open_end=(pos + n - 1) not in at))
        pos += n
    # Fill unmatched words (Korean-numeral readings of digits, names) between their timed neighbours.
    i = 0
    while i < len(out):
        if out[i]['start'] is not None:
            i += 1
            continue
        j = i
        while j < len(out) and out[j]['start'] is None:
            j += 1
        a = out[i - 1]['end'] if i else lo
        b = out[j]['start'] if j < len(out) else hi
        total = sum(o['chars'] for o in out[i:j])
        t = a
        for o in out[i:j]:
            o['start'] = t
            t += (b - a) * o['chars'] / total
            o['end'] = t
        i = j
    # A word matched only in part (3억 vs ASR 삼억) reaches back to its neighbour's edge.
    for k, o in enumerate(out):
        if o['open_start']:
            o['start'] = min(o['start'], out[k - 1]['end'] if k else lo)
        if o['open_end']:
            o['end'] = max(o['end'], out[k + 1]['start'] if k + 1 < len(out) else hi)
    for o in out:
        o['start'], o['end'] = max(lo, min(o['start'], hi)), max(lo, min(o['end'], hi))
        for key in ('chars', 'open_start', 'open_end'):
            del o[key]
    return out


def longform_from_sentences(sentences, words, silences=(), line_max=18):
    """Long-form: sentences [{id,start,end,display_text}] (seconds, exact) + Whisper words -> captions.

    A cue never crosses a sentence; each cue keeps sentence_id."""
    tokens = []
    for c in sentences:
        ws = [w for w in words if c['start'] <= (w['start'] + w['end']) / 2 <= c['end']]
        part = align_text(c['display_text'], ws, (c['start'], c['end']))
        for t in part:
            t['group'] = c['id']
        if part:
            part[-1]['hard'] = True
            part[0]['start'] = c['start']
        tokens += part
    cues = split(tokens, silences, line_max=line_max)
    return [dict(start=round(q['start'], 3), end=round(q['end'], 3), text=q['text'], sentence_id=q['group']) for q in cues]


def shorts_from_subtitles(subtitles, words, silences=(), fps=30, line_max=16):
    """Shorts: authored subtitle rows {from_,to,text} (frames) re-split on ASR timing; text unchanged."""
    tokens = []
    for r in subtitles:
        a, b = r['from_'] / fps, r['to'] / fps
        ws = [w for w in words if a <= (w['start'] + w['end']) / 2 <= b]
        tokens += align_text(r['text'].replace('\n', ' '), ws, (a, b))
    return to_shorts(split(tokens, silences, line_max=line_max), fps)


def lint(cues, line_max=18, cps_max=None):
    """Rule violations in finished cues (used by tests and the code lint gate). With cps_max set, cues carrying
    start/end (seconds) are also checked for reading speed (non-space chars per second) and minimum hold
    (0.3 s per word + 0.5 s; manim-skill lint-subtitles idea)."""
    issues = []
    for k, c in enumerate(cues):
        if cps_max is not None and c.get('start') is not None and c.get('end') is not None:
            span = float(c['end']) - float(c['start'])
            chars = len(re.sub(r'\s', '', c['text']))
            if span <= 0 or chars / span > cps_max:
                issues.append(dict(cue=k, code='reading_speed', text=c['text'],
                                   cps=round(chars / span, 1) if span > 0 else None, cps_max=cps_max))
            need = 0.3 * len(c['text'].split()) + 0.5
            if span < need:
                issues.append(dict(cue=k, code='hold_too_short', text=c['text'], hold_s=round(span, 2), need_s=round(need, 2)))
        lines = c.get('lines') or c['text'].split('\n')
        if len(lines) > 2:
            issues.append(dict(cue=k, code='over_two_lines', text=c['text']))
        for line in lines:
            if len(line) > line_max:
                issues.append(dict(cue=k, code='line_too_long', text=line, chars=len(line)))
        first = (c.get('tokens') or c['text'].split())[:1]
        if first and is_particle(first[0]):
            issues.append(dict(cue=k, code='starts_with_particle', text=c['text']))
        if k + 1 < len(cues):
            a = (c.get('tokens') or c['text'].split())[-1]
            b = (cues[k + 1].get('tokens') or cues[k + 1]['text'].split())[0]
            if ENDS_DIGIT.search(a) and b.startswith(UNITS):
                issues.append(dict(cue=k, code='number_unit_split', text=f'{a} | {b}'))
    return issues


def to_longform(cues):
    return [dict(start=round(c['start'], 3), end=round(c['end'], 3), text=c['text']) for c in cues]


def srt_time(seconds):
    """Seconds -> SRT timecode HH:MM:SS,mmm."""
    ms = max(0, round(seconds * 1000))
    return f'{ms // 3600000:02}:{ms // 60000 % 60:02}:{ms // 1000 % 60:02},{ms % 1000:03}'


def to_srt(cues):
    """Cues with start/end in seconds and `\n` between lines -> SRT text."""
    return ''.join(f"{i}\n{srt_time(c['start'])} --> {srt_time(c['end'])}\n{c['text']}\n\n" for i, c in enumerate(cues, 1))


def to_shorts(cues, fps=30):
    rows = [dict(from_=round(c['start'] * fps), to=round(c['end'] * fps), text=c['text']) for c in cues]
    for r in rows:
        r['to'] = max(r['from_'] + 1, r['to'])
    return rows


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('words')
    ap.add_argument('--audio', help='narration WAV for ffmpeg silencedetect')
    ap.add_argument('--format', choices=['longform', 'shorts'], default='longform')
    ap.add_argument('--line-max', type=int)
    ap.add_argument('--gap', type=float, default=0.22)
    ap.add_argument('--fps', type=float, default=30)
    ap.add_argument('--offset', type=float, default=0.0)
    ap.add_argument('--out')
    a = ap.parse_args()
    line_max = a.line_max or (18 if a.format == 'longform' else 16)
    silences = silences_from_audio(a.audio, min_dur=a.gap) if a.audio else []
    silences = [(s + a.offset, e + a.offset) for s, e in silences]
    cues = split(load_words(a.words, a.offset), silences, line_max=line_max, gap=a.gap)
    rows = to_longform(cues) if a.format == 'longform' else to_shorts(cues, a.fps)
    text = json.dumps(rows, ensure_ascii=False, indent=1)
    Path(a.out).write_text(text + '\n') if a.out else print(text)
    for issue in lint(cues, line_max):
        print('CHECK', json.dumps(issue, ensure_ascii=False))


if __name__ == '__main__':
    main()
