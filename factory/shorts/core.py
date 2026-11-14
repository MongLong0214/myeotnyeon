"""Shorts factory core: schema validation, fact values and pop arithmetic, spoken forms, subtitle chunks, the
compile step (episode spec -> legacy b_format spec) and every pre-render check that can be decided from the spec.
Pure Python; Korean break judging uses factory/qa/subtitle_ko (kiwipiepy in work/.venv when present)."""
import ast
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BF = ROOT / 'episodes/quiz/batch_1107/b_format'
BC_DIR = ROOT / 'episodes/beastclash'
LIB = json.loads((Path(__file__).with_name('library.json')).read_text())
SCHEMA = json.loads((ROOT / 'factory/schema/episode.schema.json').read_text())
PKG = ROOT / 'upload/pkg'


class Fail(Exception):
    """A stop with an actionable message; `errors` is a list of 'where: what -> how to fix' strings."""
    def __init__(self, step, errors):
        self.step, self.errors = step, list(errors)
        super().__init__(f'{step}: ' + '; '.join(self.errors))


# ---------------------------------------------------------------- JSON Schema (draft 2020-12 subset)
def _type_ok(v, t):
    return {'object': isinstance(v, dict), 'array': isinstance(v, list), 'string': isinstance(v, str),
            'boolean': isinstance(v, bool), 'null': v is None,
            'integer': isinstance(v, int) and not isinstance(v, bool),
            'number': isinstance(v, (int, float)) and not isinstance(v, bool)}[t]


def validate(v, s, path='$', root=SCHEMA):
    """Errors for instance v against schema s. Supports $ref, type, enum, const, required, properties,
    additionalProperties, propertyNames, maxProperties, items, min/maxItems, uniqueItems, min/maxLength, pattern,
    minimum, maximum, allOf, if/then."""
    if '$ref' in s:
        node = root
        for part in s['$ref'].lstrip('#/').split('/'):
            node = node[part]
        return validate(v, node, path, root)
    e = []
    if 'type' in s and not any(_type_ok(v, t) for t in ([s['type']] if isinstance(s['type'], str) else s['type'])):
        return [f'{path}: expected {s["type"]}, got {type(v).__name__}']
    if 'const' in s and v != s['const']:
        e.append(f'{path}: must be {s["const"]!r}')
    if 'enum' in s and v not in s['enum']:
        e.append(f'{path}: {v!r} is not allowed; choose one of {s["enum"]}')
    if isinstance(v, str):
        if len(v) < s.get('minLength', 0):
            e.append(f'{path}: too short ({len(v)} < {s["minLength"]})')
        if len(v) > s.get('maxLength', 1 << 30):
            e.append(f'{path}: too long ({len(v)} > {s["maxLength"]}) -> shorten it')
        if 'pattern' in s and not re.search(s['pattern'], v):
            e.append(f'{path}: {v!r} does not match {s["pattern"]}')
    if isinstance(v, (int, float)) and not isinstance(v, bool):
        if 'minimum' in s and v < s['minimum']:
            e.append(f'{path}: {v} < {s["minimum"]}')
        if 'maximum' in s and v > s['maximum']:
            e.append(f'{path}: {v} > {s["maximum"]}')
    if isinstance(v, list):
        if len(v) < s.get('minItems', 0):
            e.append(f'{path}: needs at least {s["minItems"]} items')
        if len(v) > s.get('maxItems', 1 << 30):
            e.append(f'{path}: at most {s["maxItems"]} items')
        if s.get('uniqueItems') and len({json.dumps(x, sort_keys=True) for x in v}) != len(v):
            e.append(f'{path}: items must be unique')
        if 'items' in s:
            for i, x in enumerate(v):
                e += validate(x, s['items'], f'{path}[{i}]', root)
    if isinstance(v, dict):
        for k in s.get('required', []):
            if k not in v:
                e.append(f'{path}: missing required field "{k}"')
        props = s.get('properties', {})
        if len(v) > s.get('maxProperties', 1 << 30):
            e.append(f'{path}: at most {s["maxProperties"]} fields')
        for k, x in v.items():
            if 'propertyNames' in s:
                e += [m.replace(f'{path}.{k}', f'{path} key "{k}"') for m in validate(k, s['propertyNames'], f'{path}.{k}', root)]
            if k in props:
                e += validate(x, props[k], f'{path}.{k}', root)
            elif s.get('additionalProperties') is False:
                e.append(f'{path}: unknown field "{k}" (allowed: {sorted(props)})')
            elif isinstance(s.get('additionalProperties'), dict):
                e += validate(x, s['additionalProperties'], f'{path}.{k}', root)
    for sub in s.get('allOf', []):
        if 'if' in sub:
            if not validate(v, sub['if'], path, root):
                e += validate(v, sub.get('then', {}), path, root)
        else:
            e += validate(v, sub, path, root)
    return e


# ---------------------------------------------------------------- numbers: parse, compute, format
EN_WORDS = {w: i for i, w in enumerate('zero one two three four five six seven eight nine ten eleven twelve thirteen '
                                       'fourteen fifteen sixteen seventeen eighteen nineteen'.split())}
EN_WORDS.update({w: 10 * i for i, w in enumerate('x x twenty thirty forty fifty sixty seventy eighty ninety'.split()) if i >= 2})
KO_NATIVE = {'한': 1, '하나': 1, '두': 2, '둘': 2, '세': 3, '셋': 3, '네': 4, '넷': 4, '다섯': 5, '여섯': 6, '일곱': 7, '여덟': 8,
             '아홉': 9, '열': 10, '스무': 20, '스물': 20, '서른': 30, '마흔': 40}


def _int(s):
    return int(float(s.replace(',', '')))


def en_num(tok):
    """'14' / 'fourteen' / 'twenty-five' -> int or None"""
    tok = tok.lower().strip()
    if re.fullmatch(r'\d[\d,]*', tok):
        return _int(tok)
    parts = re.split(r'[- ]', tok)
    if all(p in EN_WORDS for p in parts):
        return sum(EN_WORDS[p] for p in parts)
    return None


def nums_in(text, L):
    """Every number a reader sees in text, as integers (ko amounts in won; en/ja word numbers too)."""
    out = set()
    t = text.replace(' ', ' ')
    if L == 'ko':
        for m in re.finditer(r'(?:(\d[\d,]*)\s*억)?\s*(?:(\d[\d,]*)\s*만)?(?:\s*(\d[\d,]*)\s*원)?', t):
            if m.group(1) or m.group(2):
                out.add(_int(m.group(1) or '0') * 10 ** 8 + _int(m.group(2) or '0') * 10 ** 4 + _int(m.group(3) or '0'))
    if L == 'ja':
        for m in re.finditer(r'(?:(\d[\d,]*)\s*億)?\s*(?:(\d[\d,]*)\s*万)', t):
            out.add(_int(m.group(1) or '0') * 10 ** 8 + _int(m.group(2) or '0') * 10 ** 4)
    if L == 'en':
        for m in re.finditer(r'\$?(\d[\d,]*(?:\.\d+)?)\s*(million|billion|thousand)', t, re.I):
            out.add(int(float(m.group(1).replace(',', '')) * {'thousand': 1e3, 'million': 1e6, 'billion': 1e9}[m.group(2).lower()]))
        for m in re.finditer(r'\b([a-z]+(?:-[a-z]+)?)\b', t.lower()):
            n = en_num(m.group(1))
            if n is not None and m.group(1) not in ('zero',):
                out.add(n)
    for m in re.finditer(r'\d[\d,]*(?:\.\d+)?', t):
        out.add(int(float(m.group(0).replace(',', ''))) if '.' not in m.group(0) else float(m.group(0)))
    return out


# number + unit: "징역 3년" must not pass on a quote that only has "3억 원" (review 11-14 P0-1)
UNITS = {'ko': {'년': 'year', '개월': 'month', '일': 'day', '시간': 'hour', '원': 'money', '차례': 'times', '번': 'times', '회': 'times', '명': 'people', '%': '%'},
         'en': {'year': 'year', 'yr': 'year', 'month': 'month', 'mo': 'month', 'day': 'day', 'hour': 'hour', 'dollar': 'money', '%': '%'},
         'ja': {'年': 'year', 'か月': 'month', 'ヶ月': 'month', 'カ月': 'month', 'ケ月': 'month', '日': 'day', '時間': 'hour', '円': 'money', '人': 'people', '%': '%'}}
_NUM = r'\d[\d,]*(?:\.\d+)?'
_ENW = '|'.join(sorted(EN_WORDS, key=len, reverse=True))


def _num(x):
    x = x.replace(',', '')
    return float(x) if '.' in x else int(x)


def unit_tokens(text, L):
    """([(pos, number, unit, as written)], rest): numbers written with a unit (ko/ja 억·만 amounts count as money), and the
    text with those blanked so the bare-number fallback (nums_in) sees only numbers that have no unit"""
    t = text.replace('\u00a0', ' ')
    U = UNITS[L]
    alt = '|'.join(sorted(map(re.escape, U), key=len, reverse=True))
    toks = []

    def take(m, n, u):
        toks.append((m.start(), n, u, m.group(0).strip()))
        return ' ' * len(m.group(0))
    if L in ('ko', 'ja'):
        big, man, won = ('억', '만', '원') if L == 'ko' else ('億', '万', '円')
        rx = rf'(?=\d)(?:(\d[\d,]*)\s*{big})?\s*(?:(\d[\d,]*)\s*{man})?(?:\s*(\d[\d,]*)\s*{won})?(?:\s*({alt}))?'
        t = re.sub(rx, lambda m: take(m, _int(m.group(1) or '0') * 10 ** 8 + _int(m.group(2) or '0') * 10 ** 4 + _int(m.group(3) or '0'), U.get(m.group(4), 'money'))
                   if m.group(1) or m.group(2) else m.group(0), t)
        t = re.sub(rf'({_NUM})\s*({alt})', lambda m: take(m, _num(m.group(1)), U[m.group(2)]), t)
    else:
        t = re.sub(rf'\$\s?({_NUM})(?:\s*(thousand|million|billion))?',
                   lambda m: take(m, int(float(m.group(1).replace(',', '')) * {None: 1, 'thousand': 1e3, 'million': 1e6, 'billion': 1e9}[m.group(2) and m.group(2).lower()]), 'money'), t, flags=re.I)
        num = rf'{_NUM}|(?:{_ENW})(?:[- ](?:{_ENW}))?'
        t = re.sub(rf'(?<![a-z\d])({num})[\s-]*({alt})s?(?![a-z])',
                   lambda m: take(m, en_num(m.group(1)) if not m.group(1)[0].isdigit() else _num(m.group(1)), U[m.group(2).lower()]), t, flags=re.I)
    return sorted(toks), t


def nums_missing(text, quotes, L):
    """numbers in `text` the quotes do not carry, as written: a number with a unit needs the same number + unit in the quotes
    (3년 is not 3억 원); a number without a unit falls back to the bare number"""
    tt, rest = unit_tokens(text, L)
    have = {(n, u) for _, n, u, _ in unit_tokens(quotes, L)[0]}
    return list(dict.fromkeys(raw for _, n, u, raw in tt if (n, u) not in have)) + [str(n) for n in sorted(nums_in(rest, L) - nums_in(quotes, L))]


# sentence type words; a type word in the answer must be in the sentence quotes, with its own number + unit
SENTENCE_TYPES = {'ko': {'징역': '징역', '금고': '금고', '벌금': '벌금', '집행유예': '집행유예', '집유': '집행유예', '무죄': '무죄', '선고유예': '선고유예', '사회봉사': '사회봉사', '무기': '무기'},
                  'en': {'prison': 'prison', 'jail': 'jail', 'probation': 'probation', r'\bfine': 'fine', 'suspend': 'suspended', 'acquit': 'acquitted', r'\blife\b': 'life'},
                  'ja': {'懲役': '懲役', '拘禁刑': '拘禁刑', '禁錮': '禁錮', '罰金': '罰金', '執行猶予': '執行猶予', '無罪': '無罪'}}
_TYPE_UNITS = {'벌금': {'money'}, 'fine': {'money'}, '罰金': {'money'}, '사회봉사': {'hour'}}


def sentence_pairs(text, L):
    """(type words, {(type, number, unit)}): each number + unit goes to the type word before it in the same sentence
    (en: the nearest one on either side), e.g. "금고 1년에 집행유예 2년" -> (금고, 1, year), (집행유예, 2, year)"""
    T = SENTENCE_TYPES[L]
    low = text.lower()
    marks = sorted((m.start(), m.end(), T[rx]) for rx in T for m in re.finditer(rx if L == 'en' else re.escape(rx), low))
    pairs = set()
    for pos, n, u, raw in unit_tokens(text, L)[0]:
        cand = [(pos - e, w) for s, e, w in marks if e <= pos and not re.search(r'[.!?]\s|[。\n]', low[e:pos])]
        if L == 'en':
            cand += [(s - pos - len(raw), w) for s, e, w in marks if s >= pos and not re.search(r'[.!?]\s|[。\n]', low[pos:s])]
        cand = [(d, w) for d, w in cand if u in _TYPE_UNITS.get(w, {'year', 'month', 'day'})]
        if cand:
            pairs.add((min(cand)[1], n, u))
    return {w for _, _, w in marks}, pairs


def sentence_errors(where, text, quotes, L, nums=True):
    """P0-1a: type words and (type, number + unit) pairs of an answer text must be in the sentence quotes"""
    q = '\n'.join(quotes)
    tw, tp = sentence_pairs(text, L)
    qw, qp = sentence_pairs(q, L)
    E = [f'{where}: "{text}" says "{w}" but the sentence quotes do not -> use the sentence type the source writes' for w in sorted(tw - qw)]
    E += [f'{where}: "{text}" says {w} {n} {u} but the sentence quotes do not give {w} that number -> copy the sentence from the quote' for w, n, u in sorted(tp - qp, key=str) if w in qw]
    miss = nums_missing(text, q, L) if nums else []  # hook numbers may come from any fact (policy.meta_numbers)
    if miss:
        E.append(f'{where}: "{text}" has numbers {miss} not in the sentence quotes (same number and unit)')
    return E


class Val:
    """A typed fact value. amount: int (won / dollars / yen); count: int; date: (y, m); duration: ('m'|'d', n)."""
    def __init__(self, kind, v, unit=None):
        self.kind, self.v, self.unit = kind, v, unit

    def __repr__(self):
        return f'{self.kind}:{self.v}'


def parse_value(kind, text, L):
    t = text.replace('약 ', '').replace('約', '').strip()
    if kind == 'amount':
        if L == 'ko':
            m = re.search(r'(?:(\d[\d,]*)\s*억)?\s*(?:(\d[\d,]*)\s*만)?\s*(\d[\d,]*)?\s*원?', t)
            if m and any(m.groups()):
                return Val('amount', _int(m.group(1) or '0') * 10 ** 8 + _int(m.group(2) or '0') * 10 ** 4 + _int(m.group(3) or '0'))
        if L == 'ja':
            m = re.search(r'(?:(\d[\d,]*)\s*億)?\s*(?:(\d[\d,]*)\s*万)?\s*(\d[\d,]*)?\s*円', t)
            if m and any(m.groups()):
                return Val('amount', _int(m.group(1) or '0') * 10 ** 8 + _int(m.group(2) or '0') * 10 ** 4 + _int(m.group(3) or '0'))
        if L == 'en':
            m = re.search(r'\$\s?(\d[\d,]*(?:\.\d+)?)\s*(million|billion|thousand)?', t, re.I)
            if m:
                mul = {'thousand': 1e3, 'million': 1e6, 'billion': 1e9}.get((m.group(2) or '').lower(), 1)
                return Val('amount', int(round(float(m.group(1).replace(',', '')) * mul)))
    if kind == 'count':
        m = re.search(r'\d[\d,]*', t)
        if m:
            return Val('count', _int(m.group(0)))
        for w in re.findall(r'[a-z]+(?:-[a-z]+)?', t.lower()):
            if en_num(w) is not None:
                return Val('count', en_num(w))
        for w, n in KO_NATIVE.items():
            if t.startswith(w):
                return Val('count', n)
    if kind == 'date':
        m = re.search(r'(20\d\d|19\d\d)\s*[년年]\s*(\d{1,2})\s*[월月]', t)
        if m:
            return Val('date', (int(m.group(1)), int(m.group(2))))
        mon = ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']
        m = re.search(r'\b(' + '|'.join(mon) + r')[a-z]*\.?\s+(?:\d{1,2},?\s+)?(20\d\d)', t, re.I)
        if m:
            return Val('date', (int(m.group(2)), mon.index(m.group(1).lower()[:3]) + 1))
    if kind == 'duration':
        tl = t.lower()
        y = re.search(r'(\d+|[a-z]+(?:-[a-z]+)?)[\s-]*(?:년|年|years?|yrs?)', tl)
        mo = re.search(r'(\d+|[a-z]+(?:-[a-z]+)?)[\s-]*(?:개월|か月|ヶ月|カ月|months?|mo\b)', tl)
        d = re.search(r'(\d+|[a-z]+(?:-[a-z]+)?)[\s-]*(?:일|日|days?)', tl)
        g = lambda m: en_num(m.group(1)) if m else None  # noqa: E731
        if (y and g(y) is not None) or (mo and g(mo) is not None):
            return Val('duration', ('m', 12 * (g(y) or 0) + (g(mo) or 0)))
        if d and g(d) is not None:
            return Val('duration', ('d', g(d)))
    if kind == 'measure':
        m = re.search(r'(\d[\d,]*(?:\.\d+)?)\s*(lbs?|pounds?|tons?|ft|feet|foot|in|inches|miles per hour|mph|kg|m|km/h)\b', t, re.I)
        if m:
            return Val('measure', float(m.group(1).replace(',', '')), m.group(2).lower())
    return None


def fmt_num(v):
    """a measure as the source wrote it: 16.5 stays 16.5 (never rounded to 16), 3000 -> 3,000"""
    return f'{v:,.0f}' if float(v) == int(v) else f'{v:,}'


def fmt_int(n, L):
    return f'{int(round(n)):,}'


def fmt_amount(n, L):
    n = int(round(n))
    if L == 'ko':
        e, r = divmod(n, 10 ** 8)
        m = r // 10 ** 4
        mm = f'{m:,}만' if m else ''  # never 5천만: Hangul numerals on screen fail H16
        return ' '.join(x for x in [f'{e:,}억' if e else '', mm] if x) or f'{n:,}'
    if L == 'ja':
        e, r = divmod(n, 10 ** 8)
        m = r // 10 ** 4
        return ''.join(x for x in [f'{e}億' if e else '', f'{m}万' if m else '']) or f'{n:,}'
    if n >= 10 ** 6:
        return f'${n / 10 ** 6:.1f}'.rstrip('0').rstrip('.') + ' million'
    return f'${n:,}'


def fmt_date(v, L):
    y, m = v
    return {'ko': f'{y}년 {m}월', 'ja': f'{y}年{m}月'}.get(L, ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'][m - 1] + f' {y}')


def fmt_duration(v, L):
    u, n = v
    if u == 'd':
        return {'ko': f'{n:,}일', 'ja': f'{n:,}日'}.get(L, f'{n:,} days')
    y, m = divmod(n, 12)
    if L == 'ko':
        return ' '.join(x for x in [f'{y}년' if y else '', f'{m}개월' if m else ''] if x)
    if L == 'ja':
        return ''.join(x for x in [f'{y}年' if y else '', f'{m}か月' if m else ''])
    return ' '.join(x for x in [f'{y} yrs' if y > 1 else ('1 yr' if y else ''), f'{m} mo' if m else ''] if x)


UNIT_FMT = {'months': {'ko': '{}개월', 'en': '{} months', 'ja': '{}か月'}, 'days': {'ko': '{}일', 'en': '{} days', 'ja': '{}日'},
            'hours': {'ko': '{}시간', 'en': '{} hours', 'ja': '{}時間'}}


def fmt(v, L):
    if v.kind == 'amount':
        return fmt_amount(v.v, L)
    if v.kind == 'date':
        return fmt_date(v.v, L)
    if v.kind == 'duration':
        return fmt_duration(v.v, L)
    if v.kind in UNIT_FMT:
        return UNIT_FMT[v.kind][L].format(fmt_int(v.v, L))
    if v.kind == 'measure':
        return f'{fmt_num(v.v)} {v.unit}'
    return fmt_int(v.v, L)


def _months(v):
    if v.kind != 'duration':
        raise ValueError(f'needs a duration, got {v.kind}')
    return v.v[1] if v.v[0] == 'm' else v.v[1] / 30.44


def _days(v):
    if v.kind != 'duration':
        raise ValueError(f'needs a duration, got {v.kind}')
    return v.v[1] if v.v[0] == 'd' else round(v.v[1] * 30.44)


FUNCS = {
    'span': lambda a, b: Val('duration', ('m', (b.v[0] - a.v[0]) * 12 + b.v[1] - a.v[1] + 1)),  # inclusive months
    'months': lambda a: Val('months', round(_months(a))),
    'days': lambda a: Val('days', _days(a)),
    'hours': lambda a: Val('hours', 24 * _days(a)),
}


def evaluate(expr, values):
    """Evaluate a pop variable: F2.loan, F2.loan - F2.request, span(F1.start, F1.end), months(...), days(...), hours(...)."""
    def ev(n):
        if isinstance(n, ast.Expression):
            return ev(n.body)
        if isinstance(n, ast.Attribute) and isinstance(n.value, ast.Name):
            key = f'{n.value.id}.{n.attr}'
            if key not in values:
                raise ValueError(f'unknown value {key} (define it in facts[].values)')
            return values[key]
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Name) and n.func.id in FUNCS and not n.keywords:
            return FUNCS[n.func.id](*[ev(a) for a in n.args])
        if isinstance(n, ast.BinOp) and isinstance(n.op, (ast.Add, ast.Sub)):
            a, b = ev(n.left), ev(n.right)
            if a.kind != b.kind or a.kind not in ('amount', 'count'):
                raise ValueError(f'cannot combine {a.kind} and {b.kind}')
            return Val(a.kind, a.v + b.v if isinstance(n.op, ast.Add) else a.v - b.v)
        raise ValueError(f'not allowed in a pop variable: {ast.dump(n)[:60]}')
    return ev(ast.parse(expr, mode='eval'))


def fact_values(spec):
    """{'F1.start': Val} for every facts[].values entry; raises Fail on unparsable text or text missing from quotes."""
    out, errs, L = {}, [], spec['locale']
    for f in spec['facts']:
        quotes = ' '.join(q['text'] for q in f['quotes'])
        for name, d in (f.get('values') or {}).items():
            if norm_ws(d['text']) not in norm_ws(quotes):
                errs.append(f'facts {f["id"]}.values.{name}: "{d["text"]}" is not written in this fact\'s quotes -> copy it exactly from a quote')
            v = parse_value(d['kind'], d['text'], L)
            if v is None:
                errs.append(f'facts {f["id"]}.values.{name}: cannot read "{d["text"]}" as {d["kind"]} -> use digits with a unit, e.g. 3억 원 / 12차례 / 2020년 12월 / 징역 3년')
            else:
                out[f'{f["id"]}.{name}'] = v
    if errs:
        raise Fail('facts', errs)
    return out


def norm_ws(s):
    s = s.replace(' ', ' ').replace('“', '"').replace('”', '"').replace('‘', "'").replace('’', "'")
    s = re.sub(r'(\d),\s+(\d{3})', r'\1,\2', s)  # PDF text layers write 3, 000
    return re.sub(r'\s+', ' ', s).strip()


def human_calc(p, values, L):
    """description line for a pop's computed vars, without fact ids: 'months(F3.sentence)' -> '1년 = 12개월'; plain fact refs are dropped
    (q049 meta leaked 'amt = F1.bet = 500만')"""
    out = []
    for k, e in p['vars'].items():
        e = e.strip()
        if re.fullmatch(r'F\d+\.\w+', e):
            continue
        h = re.sub(r'F\d+\.\w+', lambda m: fmt(values[m.group()], L) if m.group() in values else m.group(), e)
        h = re.sub(r'^\w+\((.*)\)$', r'\1', h)
        out.append(f'{h} = {fmt(evaluate(e, values), L)}')
    return out


def render_pop(p, values, L):
    """-> (big, small, calc) with every {var} computed from fact values."""
    got = {k: evaluate(e, values) for k, e in p['vars'].items()}
    out = []
    for tpl in (p['big'], p.get('small', '')):
        for k in re.findall(r'{(\w+)}', tpl):
            if k not in got:
                raise ValueError(f'template uses {{{k}}} but vars has no "{k}"')
        out.append(re.sub(r'{(\w+)}', lambda m: fmt(got[m.group(1)], L), tpl))
    calc = '; '.join(f'{k} = {e} = {fmt(got[k], L)}' for k, e in p['vars'].items())
    return out[0], out[1], calc


# ---------------------------------------------------------------- spoken forms
SINO = '일이삼사오육칠팔구'
NATIVE1 = ['', '한', '두', '세', '네', '다섯', '여섯', '일곱', '여덟', '아홉']
NATIVE10 = ['', '열', '스물', '서른', '마흔', '쉰', '예순', '일흔', '여든', '아흔']
NATIVE_COUNTERS = ('번', '명', '개', '살', '시간', '차례', '곳', '대', '마리', '잔', '장', '권', '달', '사람', '군데', '가지', '시')
ATTACH = ('억', '만', '천', '조')


def sino4(n):
    out = ''
    for v, u in [(1000, '천'), (100, '백'), (10, '십'), (1, '')]:
        q, n = divmod(n, v)
        if q:
            out += ('' if q == 1 and v > 1 else SINO[q - 1]) + u
    return out


def sino(n):
    if n == 0:
        return '영'
    parts = []
    for unit, size in [('조', 10 ** 12), ('억', 10 ** 8), ('만', 10 ** 4), ('', 1)]:
        q, n = divmod(n, size)
        if q:
            parts.append(unit if (q == 1 and unit == '만') else ('일' if q == 1 and unit in ('억', '조') else sino4(q)) + unit)
    return ''.join(parts)


def native(n):
    if n == 20:
        return '스무'
    return NATIVE10[n // 10] + NATIVE1[n % 10]


def ko_say(text):
    """Digits -> Korean reading (native numbers before 번/명/개/살/시간/차례..., sino otherwise); A/B/C -> 에이/비/씨."""
    t = text.replace('"', '').replace('“', '').replace('”', '').replace("'", '').replace('‘', '').replace('’', '')
    t = re.sub(r'(?<![A-Za-z])([ABC])(?![A-Za-z])', lambda m: {'A': '에이', 'B': '비', 'C': '씨'}[m.group(1)], t)
    t = t.replace('%', '퍼센트').replace('~', ' ~ ')

    def rep(m):
        n = int(m.group(1).replace(',', ''))
        sp, rest = m.group(2), m.group(3)
        if rest.startswith(NATIVE_COUNTERS) and 0 < n < 100 and not rest.startswith(('번째',)):
            return native(n) + ' ' + rest
        if rest.startswith(ATTACH):
            return sino(n) + rest
        return sino(n) + (' ' if rest and re.match(r'[가-힣]', rest) else sp) + rest
    t = re.sub(r'(\d[\d,]*)(\s?)([가-힣]{0,2})', rep, t)
    t = re.sub(r'\s+', ' ', t).replace(' ~ ', '부터 ')
    return t.strip()


def en_words(n):
    ones = 'zero one two three four five six seven eight nine ten eleven twelve thirteen fourteen fifteen sixteen seventeen eighteen nineteen'.split()
    tens = 'x x twenty thirty forty fifty sixty seventy eighty ninety'.split()

    def w3(n):
        if n < 20:
            return ones[n]
        if n < 100:
            return tens[n // 10] + ('' if n % 10 == 0 else '-' + ones[n % 10])
        return ones[n // 100] + ' hundred' + ('' if n % 100 == 0 else ' ' + w3(n % 100))
    if n < 1000:
        return w3(n)
    if n < 10 ** 6:
        return w3(n // 1000) + ' thousand' + ('' if n % 1000 == 0 else ' ' + w3(n % 1000))
    return w3(n // 10 ** 6) + ' million' + ('' if n % 10 ** 6 == 0 else ' ' + en_words(n % 10 ** 6))


def en_say(text):
    t = text.replace('"', '').replace('“', '').replace('”', '')
    for a, b in [(r'\byrs?\b', 'years'), (r'\b1 years\b', '1 year'), (r'\bmo\b', 'months'), (r'\bhrs?\b', 'hours'), (r'\bmins?\b', 'minutes'), (r'\blbs?\b', 'pounds'), (r'\bmph\b', 'miles an hour'), (r'\bvs\.?(?=\s)', 'versus')]:
        t = re.sub(a, b, t)
    t = re.sub(r'\$(\d[\d,]*(?:\.\d+)?)\s*(million|billion|thousand)?', lambda m: f"{m.group(1)} {m.group(2) or ''} dollars", t)
    t = re.sub(r'(\d+)\.(\d+)', lambda m: f'{en_words(int(m.group(1)))} point {" ".join(en_words(int(c)) for c in m.group(2))}', t)
    t = re.sub(r'\d[\d,]*', lambda m: en_words(int(m.group(0).replace(',', ''))), t)
    t = t.replace('%', ' percent')
    t = re.sub(r'\s+', ' ', t).replace(' ,', ',').strip()
    return re.sub(r'(^|[.?!]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), t)


def ja_say(text):
    t = re.sub(r'[「」『』]', '', text)
    return re.sub(r'(?<![A-Za-z])([ABC])(?![A-Za-z])', lambda m: {'A': 'エー', 'B': 'ビー', 'C': 'シー'}[m.group(1)], t)


def say(text, L):
    return {'ko': ko_say, 'en': en_say, 'ja': ja_say}[L](text)


def units(text, L):
    """speech units for duration estimates (ko syllables, en vowel groups, ja characters)"""
    if L == 'ko':
        return len(re.sub('[^가-힣]', '', text))
    if L == 'ja':
        return len(re.sub(r'[\s、。？！,.?!]', '', text))
    return sum(max(1, len(re.findall(r'[aeiouy]+', w))) for w in re.findall(r"[a-zA-Z']+", text))


RATE = {'ko': 6.4, 'en': 4.6, 'ja': 8.0}


# ---------------------------------------------------------------- subtitle chunks (ko); en/ja use linebreak.py
_NUM_HEAD = re.compile(r'\d[\d,.]*\s*(년|억|만|천|시간|분)$')


def split_number(left, right):
    """True when a break between left and right cuts one amount in two: '징역 1년' / '6개월' (zzs054 R8), '4억' / '5천만 원'"""
    return bool(_NUM_HEAD.search(left.rstrip(' ,')) and re.match(r'\d', right.lstrip()))


def repeated_shots(utterances):
    """adjacent shots across the whole cut that would look the same (same scene and, for people, same look and face); zzs054 R6"""
    seq = [(u['id'], sh) for u in utterances for sh in (u.get('shots') or [])]
    key = lambda sh: (sh.get('s'), sh.get('look'), sh.get('expr'), sh.get('move'), sh.get('y'))  # noqa: E731
    # props (paper, stamp, tally...) carry different text each time, so only people shots count
    return [f'{a} -> {b}: {key(x)[0]}' + (f' {key(x)[1]}/{key(x)[2]}' if key(x)[1] else '')
            for (a, x), (b, y) in zip(seq, seq[1:]) if x.get('look') and key(x) == key(y)]


def chunk_ko(text, mx=12, mn=3):
    """One-line B3 cues: split after , . ? ! then balance each long piece at spaces; a break the Korean analyser
    rates FAIL is never chosen, REVIEW costs extra."""
    from factory.qa import subtitle_ko
    pieces = [p.strip() for p in re.split(r'(?<=[.?!…])\s+|(?<=,)(?!\d)\s*', text) if p.strip()]  # never split 8,000
    out = []
    for p in pieces:
        words = p.split()
        if len(p) <= mx or len(words) == 1:
            out.append(p)
            continue
        n = len(words)
        best = [0.0] + [math.inf] * n
        prev = [0] * (n + 1)
        k = max(2, math.ceil(len(p) / mx))
        ideal = len(p) / k
        for j in range(1, n + 1):
            for i in range(j):
                seg = ' '.join(words[i:j])
                if len(seg) > mx and j - i > 1:
                    continue
                c = (len(seg) - ideal) ** 2 + (500 if len(seg) < mn else 0)
                if j < n:
                    v = subtitle_ko.judge(' '.join(words[:j]), ' '.join(words[j:]))
                    c += 1e6 if v and v[0] == 'FAIL' else 60 if v else 0
                    c += 1e6 if split_number(' '.join(words[:j]), ' '.join(words[j:])) else 0
                if best[i] + c < best[j]:
                    best[j], prev[j] = best[i] + c, i
        segs, j = [], n
        while j > 0:
            segs.append(' '.join(words[prev[j]:j]))
            j = prev[j]
        out += segs[::-1]
    return out


# ---------------------------------------------------------------- text fit (mirrors B3Kit emKo / i18n em)
def em(text, L):
    if L == 'ko':
        return sum(1 if re.match('[가-힣]', ch) else .3 if ch == ' ' else .62 if ch.isdigit() else .5 for ch in text)
    return sum(1 if re.match('[　-鿿＀-￯가-힯]', ch) else (.66 if re.match('[A-Z0-9$]', ch) else .54) if L == 'en' else .56
               for ch in text)


def fit(text, size, box, L):
    return min(size, math.floor(box / max(1e-6, max([em(x, L) for x in text.split('\n')] or [1]))))


# ---------------------------------------------------------------- look palette distinctness (FightRig LOOKS)
def look_palette():
    src = (BF / 'FightRig.tsx').read_text()
    pal = {}
    for k, sh, pa in re.findall(r"^\s*(\w+):\s*\{\s*shirt:\s*'(#[0-9A-Fa-f]{6})'.*?pants:\s*'(#[0-9A-Fa-f]{6})'", src, re.M):
        pal[k] = (sh, pa)
    return pal


def _rgb(h):
    return [int(h[i:i + 2], 16) for i in (1, 3, 5)]


def confusable(a, b, pal=None, shirt_max=45, pants_max=45):
    pal = pal or look_palette()
    if a == b or a not in pal or b not in pal:
        return False
    d = lambda x, y: math.dist(_rgb(x), _rgb(y))  # noqa: E731
    return d(pal[a][0], pal[b][0]) < shirt_max and d(pal[a][1], pal[b][1]) < pants_max


# ---------------------------------------------------------------- B3: beats, compile, pre-render checks
B3_ORDER = re.compile(r'^open hook guess twist (fact ){1,4}answer2 loop$')
FIXED = {
    'ko': dict(choices='실제 형량은?', answer='정답은 {L}, {c}.', opinion_tts='가볍다 적당 무겁다?', opinion='이 형량,\n가볍다 / 적당 / 무겁다?', sep=', ', last=', ', end='.'),
    'en': dict(choices='The sentence?', answer='Answer {L}. {c}.', opinion_tts='Too light, fair, or too harsh?', opinion='This sentence:\nToo light / Fair / Too harsh?', sep=', ', last=', or ', end='?'),
    'ja': dict(choices='判決は？', answer='正解は{L}、{c}。', opinion_tts='軽い、妥当、重い？', opinion='この判決、\n軽い / 妥当 / 重い？', sep='、', last='、それとも', end='？'),
}
FINALITY_TEXT = {
    '확정': '판결은 확정됐습니다.', '항소 미확인': '항소 여부는 확인되지 않았습니다.', '항소': '판결에 항소가 제기돼 아직 확정되지 않았습니다.',
    '상고 미확인': '상고 여부는 확인되지 않았습니다.', '상고': '상고가 제기돼 아직 확정되지 않았습니다.',
    'final': 'The sentence is final.', 'appeal_unknown': 'No appeal has been reported.', 'appealed': 'The sentence has been appealed and is not final.',
    'not_final': 'The judgment is not final.',
}
FINALITY_TEXT_JA = {'final': '判決は確定しました。', 'appeal_unknown': '控訴の有無は確認されていません。', 'appealed': '控訴され、判決は確定していません。',
                    'not_final': '判決は確定していません。'}


def finality_text(fin, L):
    """the standard finality sentence of the description, in the episode's language"""
    return (FINALITY_TEXT_JA if L == 'ja' else FINALITY_TEXT)[fin]


KOKORO_VOICE = {'en': ('af_heart', [1.0, 1.1, 1.2]), 'ja': ('jf_alpha', [1.0, 1.1, 1.2])}


def beat_keys(lines):
    """['open','hook','guess','twist','fact1',...,'answer2','loop'] in spec order"""
    out, k = [], 0
    for ln in lines:
        if ln['beat'] == 'fact':
            k += 1
            out.append(f'fact{k}')
        else:
            out.append(ln['beat'])
    return out


def legacy_ids(keys):
    m = {'open': 'L01', 'hook': 'L02', 'guess': 'L03', 'twist': 'L04', 'answer2': 'L12', 'loop': 'L14'}
    return [m.get(k) or f'L{4 + int(k[4:]):02d}' for k in keys]


def shot_legacy(sh, ln, spec, values, L):
    """episode shot -> B3Kit shot dict; sizes from the fit rules"""
    D, s = LIB['defaults'], sh['scene']
    if s == 'stage':
        return {'s': spec['stage']}
    if s in ('judge', 'prosecutor'):
        return {'s': s}
    if s == 'react':
        look = sh.get('look') or ln.get('actor') or spec['defendant']
        out = {'s': 'react', 'look': look, 'expr': sh['expr'], 'move': sh['move'], 'y': D['react_framing_y'][sh.get('framing', 'close')]}
        if sh.get('other'):
            out['other'] = True
        return out
    if s == 'cell':
        return {'s': 'cell', 'look': sh.get('look') or ln.get('actor') or spec['defendant'], 'expr': sh['expr']}
    if s == 'calendar':
        y, m = values[sh['date']].v
        return {'s': 'calendar', 'year': str(y), 'month': m}
    if s == 'bubble':
        return {'s': 'bubble', 'lines': sh['lines'], 'size': max(D['min_size']['bubble'], fit(sh['lines'][0], D['max_size']['bubble'], D['fit_box_px']['bubble'], L) // 10 * 10)}
    if s == 'paper':
        return {'s': 'paper', 'lines': sh['lines'], 'size': max(D['min_size']['paper'], min(fit(x, D['max_size']['paper'], D['fit_box_px']['paper'], L) for x in sh['lines']) // 2 * 2)}
    if s == 'stamp':
        return {'s': 'stamp', 'lines': [sh['label']], 'stamp': sh['stamp'], 'size': max(D['min_size']['stamp_paper'], fit(sh['label'], D['max_size']['stamp_paper'], D['fit_box_px']['stamp_paper'], L) // 2 * 2)}
    if s == 'tally':
        return {'s': 'tally', 'n': values[sh['count']].v, 'label': sh['label']}
    if s == 'money':
        return {'s': 'money', 'nolabel': True, 'n': sh.get('bundles', 3)}
    if s == 'phone':
        return {'s': 'phone', 'msgs': sh['msgs']}
    raise ValueError(s)


def compile_b3(spec, values):
    """Episode spec -> the legacy b_format spec that synth/pace/b3post/render already consume."""
    rf = spec.get('format', 'quiz') == 'result_first'  # no A/B/C board and no answer line; answer2 is the sentence card
    L, F = spec['locale'], FIXED[spec['locale']]
    keys = beat_keys(spec['lines'])
    ids = legacy_ids(keys)
    ch, ans = spec['quiz']['choices'], spec['quiz']['answer']
    letter = 'ABC'[ans]
    out_lines = []
    sfx = [[spec['stage'], 0, LIB['defaults']['sfx']['open']], ['twist', 0, LIB['defaults']['sfx']['twist']]]

    def mk(i, mode, text, ln=None, shots=(), **kw):
        d = dict(id=i, mode=mode, tts=(ln or {}).get('say') or say(text, L) if text else '', shown=text)
        d['chunks'] = (chunk_ko(text) if L == 'ko' else 'auto') if text else None
        d['fact'] = (ln or {}).get('fact', 'Q')
        if ln and (ln.get('actor') or any(s['scene'] in ('react', 'cell') for s in ln.get('shots', []))):
            d['actor'] = ln.get('actor') or spec['defendant']
        d['shots'] = list(shots)
        if ln and ln.get('emphasis'):
            d['emphasis'] = ln['emphasis']
        d.update(kw)
        return d
    for k, i, ln in zip(keys, ids, spec['lines']):
        mode = spec['stage'] if k == 'open' else k
        shots = [{'s': spec['stage'], **({'day': True} if spec.get('stage_day') else {})}] if k == 'open' else [] if k == 'loop' else [shot_legacy(s, ln, spec, values, L) for s in ln.get('shots', [])]
        if ln.get('sfx'):
            sfx.append([mode, 0, ln['sfx']])
        if k == 'answer2' and not rf:
            sc = [say(c, L) for c in ch]
            if L == 'en':
                sc = [sc[0]] + [x[:1].lower() + x[1:] for x in sc[1:]]
            opts = F['sep'].join(sc[:2]) + F['last'] + sc[2] + F['end']
            out_lines.append(mk('L09', 'choices', F['choices']))
            out_lines.append(dict(mk('L10', 'options', opts), tts=opts, shown=None, chunks=None, hold_after=.45, **({'target': 5.6} if L == 'ko' else {})))
            said = spec['quiz'].get('answer_text') or ch[ans]  # answer_text: longer answer wording (ja001: 実刑 -> 実刑判決, whisper mishears a bare 実刑)
            a = F['answer'].format(L=letter, c=said)
            ac = [a] if L == 'ko' and len(a) <= 14 else 'auto' if L != 'ko' else chunk_ko(a)
            if isinstance(ac, list) and len(ac) > 1 and re.fullmatch(r'정답은? \S+,', ac[0]) and len(ac[0]) + 1 + len(ac[1]) <= 14:  # longer: b3post joins the short cue as 2 lines  # never a standalone "정답 C," cue (0.27 s in q049)
                ac = [ac[0] + ' ' + ac[1]] + ac[2:]
            out_lines.append(dict(mk('L11', 'answer', a, emphasis=said), chunks=ac))
        out_lines.append(mk(i, mode, ln['text'], ln, shots))
        if k == 'answer2' and not rf:  # result_first ends on the sentence reveal, then loops (owner 11-14: no comment card)
            op = LIB['defaults']['opinion_shot']
            out_lines.append(dict(mk('L13', 'opinion', None, None, [{'s': 'react', 'look': spec['defendant'], 'expr': op['expr'], 'move': op['move'], 'y': LIB['defaults']['react_framing_y'][op['framing']]}]),
                                  tts=F['opinion_tts'], shown=None, chunks=None, actor=spec['defendant'], hold_after=.3))
    pops = []
    for p in spec.get('pops', []):
        big, small, calc = render_pop(p, values, L)
        pops.append(dict(line=ids[keys.index(p['beat'])], at=p['at'], big=big, small=small, calc=calc, human=human_calc(p, values, L)))
    c = spec['case']
    leg = dict(qid=spec['id'], locale=L, variant='B3', b3=True, look='full2', grave=c['grave'], kind=spec['stage'], number_label='',
               stage=spec['stage'], cover_text=spec['cover'], defendant=spec['defendant'], choices=ch, correct=ans, answer=ch[ans],
               answer_label=c['court'], opinion='' if rf else F['opinion'], format=spec.get('format', 'quiz'), option_offsets=[0.0, 0.33, 0.66], hook_text=spec['hook'], sfx=sfx, pops=pops,
               lines=out_lines, source_spec=f'episodes/specs/{spec["id"]}.json')
    if L == 'en':
        v, sp = KOKORO_VOICE[L]
        leg.update(engine='Kokoro-82M v1.0 (Apache-2.0, local, offline)', voice=v, kokoro_speeds=sp)
    if L == 'ja':  # owner-adopted ja voice (ja001-ja003): VOICEVOX 冥鳴ひまり
        leg.update(engine='VOICEVOX 0.26.1 (local engine), VOICEVOX:冥鳴ひまり', voice='冥鳴ひまり ノーマル (style 14)', vv_style=14, vv_speeds=[1.0, 1.05, 1.15, 1.25, 1.35])
    return leg


def tag_hit(tags, hay, L):
    hay_l = hay.lower()
    return any(w.lower() in hay_l for t in tags for w in LIB['tag_words'].get(t, {}).get(L, []))


def stages_for(hay, L):
    """stage keys whose tags match the text (the `stages` command, driven by the case text instead of --tags)"""
    return [k for k, s in LIB['stages'].items() if tag_hit(s['tags'], hay, L)]


def bigrams(s):
    s = re.sub(r'[^0-9A-Za-z가-힣぀-ヿ一-鿿]', '', s.lower())
    return {s[i:i + 2] for i in range(len(s) - 1)}


def history(spec):
    """previous packages of the same channel (numeric id below this one), newest first: [(id, stage, correct, format)]"""
    reg = json.loads((ROOT / 'factory/channels/registry.json').read_text())
    ch = next(c for c in reg['channels'] if c['key'] == spec['channel'])
    pre = ch['package_prefix']
    me = int(re.sub(r'\D', '', spec['id']))
    rows = []
    for p in PKG.glob(f'{pre}[0-9][0-9][0-9]_B'):
        n = int(re.sub(r'\D', '', p.name))
        cj = p / 'case.json'
        if n < me and cj.exists():
            try:
                c = json.loads(cj.read_text())
            except ValueError:
                continue
            rows.append((n, p.name[:-2], c.get('stage'), c.get('correct'), c.get('format') or 'quiz'))
    return [r[1:] for r in sorted(rows, reverse=True)]


# A: words that name the sentence type; a pre-quiz line using one that only the correct choice has gives the answer away (q049 "집행유예였습니다")
VERDICT_TOKENS = {'ko': [['집행유예', '집유'], ['금고'], ['벌금'], ['무죄'], ['선고유예'], ['사회봉사']],
                  'en': [['suspended'], ['probation'], ['fine'], ['acquit', 'not guilty']],
                  'ja': [['執行猶予'], ['罰金'], ['無罪'], ['禁錮']]}


def early_reveal(spec):
    """errors for answer-identifying words on any line, card or pop before the quiz (beats before answer2, and the hook)"""
    L = spec['locale']
    ch, ans = spec['quiz']['choices'], spec['quiz']['answer']
    low = lambda x: str(x).lower()
    wrong = ' '.join(low(c) for i, c in enumerate(ch) if i != ans)
    toks = [g for g in VERDICT_TOKENS.get(L, []) if any(t in low(ch[ans]) for t in g) and not any(t in wrong for t in g)]
    toks = [t for g in toks for t in g] + [ch[ans]]
    keys = beat_keys(spec['lines'])
    E = []
    def scan(where, field, text):
        for t in toks:
            if text and low(t) in low(text):
                E.append(f'{where}: {field} "{text}" says "{t}" before the quiz -> the correct choice is "{ch[ans]}"; hold it for the reveal (say e.g. "판결은 의외였습니다")')
                return
    for x in spec.get('hook', []):
        scan('hook', 'hook text', x)
    for k, ln in zip(keys, spec['lines']):
        if k in ('answer2', 'loop'):
            break
        scan(f'lines[{k}]', 'narration', ln['text'])
        for j, sh in enumerate(ln.get('shots', [])):
            for f in ('lines', 'msgs', 'label', 'stamp', 'caption'):
                v = sh.get(f)
                for x in (v if isinstance(v, list) else [v] if v else []):
                    scan(f'lines[{k}].shots[{j}]({sh["scene"]})', f, x)
    for p in spec.get('pops', []):
        if p['beat'] in keys and keys.index(p['beat']) < keys.index('answer2'):
            for f in ('big', 'small'):
                scan(f'pops[{p["beat"]}]', f, p.get(f))
    return E


# B: ko option cards / answer heading, sized as BStandard.tsx draws them (letterSpacing -.04em / -.03em, word-break keep-all)
def choice_fit_ko(spec):
    ch, ans = spec['quiz']['choices'], spec['quiz']['answer']
    E = []
    for i, c in enumerate(ch):
        if em(c, 'ko') * 84 * .96 > 660:  # quiz row card: 860 px wide, 84 px type, ~660 px for the text
            E.append(f'quiz.choices[{i}] "{c}" is too wide for the option card ({em(c, "ko"):.1f} em > 8.2 em, ~8 Hangul) -> shorten it, e.g. "금고1년 집유2년"')
        size = 40 if len(c) > 6 else 46
        for w in c.split():
            if em(w, 'ko') * size * .96 > 245:  # answer column card: 273 px wide, words never break
                E.append(f'quiz.choices[{i}] word "{w}" does not fit the 273 px answer card (max ~6 Hangul per word) -> shorten it')
    a = spec['quiz'].get('answer_text') or ch[ans]
    size = 118 if len(a) > 8 else 150
    if em(a, 'ko') * size * .97 > 1000:
        E.append(f'answer heading "{a}" wraps ({em(a, "ko"):.1f} em at {size} px > {1000 / size / .97:.1f} em; max ~{int(1000 / size / .97)} Hangul) -> shorten the correct choice / answer_text')
    return E


def check_b3(spec, values):
    """Every pre-render check decidable from the spec. Returns (errors, warnings)."""
    E, W, L = [], [], spec['locale']
    lines = spec['lines']
    keys = beat_keys(lines)
    seq = ' '.join('fact' if k.startswith('fact') else k for k in keys) + ' '
    if not B3_ORDER.match(seq.replace('loop ', 'loop')):
        E.append(f'lines: beat order is "{seq.strip()}" -> must be open, hook, guess, twist, fact (1-4 times), answer2, loop')
    facts = {f['id']: f for f in spec['facts']}
    srcs = {s['id'] for s in spec['sources']}
    pal = look_palette()
    stage = LIB['stages'].get(spec.get('stage'), {})
    looks = {spec['defendant']} | set(stage.get('chars', []))
    for f in spec['facts']:
        for q in f['quotes']:
            if q['source'] not in srcs:
                E.append(f'facts {f["id"]}: quote source {q["source"]} is not in sources')
    if spec['case']['sentence_fact'] not in facts:
        E.append(f'case.sentence_fact: {spec["case"]["sentence_fact"]} is not a fact id')
    else:
        sf = facts[spec['case']['sentence_fact']]
        if len({q['source'] for q in sf['quotes']}) < 2:
            E.append(f'facts {sf["id"]} (the sentence) needs quotes from 2 different sources')
        sq = [q['text'] for q in sf['quotes']]
        E += sentence_errors('quiz.answer (the correct choice)', spec['quiz']['choices'][spec['quiz']['answer']], sq, L)
        if spec['quiz'].get('answer_text'):
            E += sentence_errors('quiz.answer_text', spec['quiz']['answer_text'], sq, L)
        if spec.get('format') == 'result_first':  # the hook is the sentence outcome
            for i, h in enumerate(spec['hook']):
                E += sentence_errors(f'hook[{i}]', h, sq, L, nums=False)
    at = spec['quiz'].get('answer_text')
    if at and spec['quiz']['choices'][spec['quiz']['answer']] not in at:
        E.append(f'quiz.answer_text "{at}" must contain the correct choice "{spec["quiz"]["choices"][spec["quiz"]["answer"]]}"')
    if keys and keys[0] == 'open' and lines[0]['fact'] in facts and stage.get('tags'):
        f0 = facts[lines[0]['fact']]
        hay0 = lines[0]['text'] + ' ' + f0['claim'] + ' ' + ' '.join(q['text'] for q in f0['quotes'])
        if not tag_hit(stage['tags'], hay0, L):
            E.append(f'stage: nothing in the open line or its fact matches stage {spec["stage"]} tags {stage["tags"]} -> pick a stage the case happens in; '
                     f'stages that match: {", ".join(stages_for(hay0, L)) or "none (ask the coordinator)"}')
    if spec.get('stage_day') and spec['stage'] != 'cash':
        E.append('stage_day: only the cash stage has a day variant -> remove stage_day')
    want = next((c.get('spec_format') for c in json.loads((ROOT / 'factory/channels/registry.json').read_text())['channels'] if c['key'] == spec['channel']), None)
    if want and spec.get('format', 'quiz') != want:
        E.append(f'format: channel {spec["channel"]} requires "format": "{want}" (registry spec_format; owner 11-14: no quiz board, no comment prompt) -> set it and follow SPEC.md for that format')
    # result_first (format B, owner A/B test 11-14): the sentence is on frame 0 on purpose, so gap A does not apply; B and C still do
    E += (early_reveal(spec) if spec.get('format', 'quiz') == 'quiz' else []) + (choice_fit_ko(spec) if L == 'ko' else [])
    used = {q['source'] for f in spec['facts'] for q in f['quotes']}
    if len(used) < 2:
        E.append('sources: quotes must come from at least 2 different sources')
    for k, ln in zip(keys, lines):
        where = f'lines[{k}]'
        f = facts.get(ln['fact'])
        if not f:
            E.append(f'{where}.fact: {ln["fact"]} is not a fact id')
            continue
        fq = '\n'.join(q['text'] for q in f['quotes'])
        hay = ln['text'] + ' ' + f['claim'] + ' ' + fq
        missing = nums_missing(ln['text'], fq, L)  # quotes only: a claim is the operator's paraphrase
        if missing:
            E.append(f'{where}: numbers {missing} in "{ln["text"]}" are not in {f["id"]} quotes (same number and unit) -> use the number as the source writes it')
        shots = ln.get('shots', [])
        if k in ('open', 'loop'):
            if shots:
                E.append(f'{where}.shots: leave empty; the builder sets {"the stage" if k == "open" else "the loop replay"}')
            continue
        mx = 3 if spec.get('format', 'quiz') == 'result_first' else 2  # result_first has no quiz board to carry background changes (11-14 decision)
        if not shots or len(shots) > mx:
            E.append(f'{where}.shots: needs 1-{mx} shots' + (' (3 only with "format": "result_first")' if len(shots) > mx else ''))
            continue
        est = units(ln.get('say') or say(ln['text'], L), L) / RATE[L]
        if est / len(shots) > 2.6:
            E.append(f'{where}: ~{est:.1f}s of speech on {len(shots)} shot(s) -> add a shot or shorten the line (max 2.6 s per shot)')
        if ln.get('actor') is None and any(s['scene'] in ('react', 'cell') for s in shots):
            W.append(f'{where}: no actor; react/cell will show the defendant ({spec["defendant"]})')
        actor = ln.get('actor') or spec['defendant']
        for j, s in enumerate(shots):
            sw = f'{where}.shots[{j}]({s["scene"]})'
            sc = s['scene']
            if sc in ('react', 'cell'):
                lk = s.get('look') or actor
                looks.add(lk)
                if lk != actor and not s.get('other'):
                    E.append(f'{sw}: shows {lk} on a line about {actor} -> remove look, or set "other": true if the line is about {lk}')
                if spec['case']['grave'] and s['expr'] in LIB['comic_exprs']:
                    E.append(f'{sw}: expression {s["expr"]} is a gag; not allowed in a grave case')
            if sc == 'cell' and not (tag_hit(['jail'], hay, L) or (k == 'answer2' and tag_hit(['jail'], spec['quiz']['choices'][spec['quiz']['answer']], L))):
                E.append(f'{sw}: a prison cell needs a prison/jail line (or answer2 after a prison sentence)')
            if sc in ('judge', 'prosecutor', 'money', 'phone') and not tag_hit(LIB['scenes'][sc]['tags'], hay, L):
                E.append(f'{sw}: nothing in the line or its fact matches this prop ({LIB["scenes"][sc]["tags"]}) -> pick a prop the line talks about')
            if sc == 'stage' and not tag_hit(stage.get('tags', []), hay, L):
                E.append(f'{sw}: the line does not match stage tags {stage.get("tags")}')
            if sc in ('bubble', 'paper', 'phone', 'stamp'):
                texts = s.get('lines') or s.get('msgs') or [s.get('label', ''), s.get('stamp', '')]
                if not any(str(x).strip() for x in texts):
                    E.append(f'{sw}: empty card text')
                elif not any(bigrams(x) & bigrams(hay) for x in texts if x.strip()) and not (sc == 'bubble' and k == 'guess'):
                    E.append(f'{sw}: card text {texts} shares no word with the line or its fact -> write what the line says')
                for x in texts:
                    if nums_missing(str(x), ln['text'] + '\n' + fq, L):
                        E.append(f'{sw}: card number in "{x}" is not in the line or fact quotes (same number and unit)')
            if sc == 'calendar':
                v = values.get(s['date'])
                if not v or v.kind != 'date':
                    E.append(f'{sw}.date: {s["date"]} must name a date value')
                elif s['date'].split('.')[0] != ln['fact'] and str(v.v[0]) not in ln['text']:
                    E.append(f'{sw}: the date comes from {s["date"].split(".")[0]} but the line is about {ln["fact"]}')
            if sc == 'tally':
                v = values.get(s['count'])
                if not v or v.kind != 'count':
                    E.append(f'{sw}.count: {s["count"]} must name a count value')
                else:
                    if not 1 <= v.v <= 15:
                        E.append(f'{sw}: tally of {v.v}; the board fits 1-15 marks (3 groups of 5) -> use paper with the number instead')
                    if v.v not in nums_in(ln['text'], L):
                        E.append(f'{sw}: tally shows {v.v} but the line text does not say {v.v}')
                    else:  # the tally must be on screen while its number is spoken (shots split the line evenly)
                        pos = [m.start() / max(1, len(ln['text'])) for m in re.finditer(r'(?<![\d,])' + str(v.v) + r'(?![\d,])', ln['text'])]
                        n = len(shots)
                        if pos and not any(j / n - .15 <= x <= (j + 1) / n + .15 for x in pos):
                            E.append(f'{sw}: tally of {v.v} is shot {j + 1} of {n} but "{v.v}" is said in another part of the line -> reorder the shots')
            # text fit (pixels of the B3Kit cards)
            D = LIB['defaults']
            if sc == 'bubble':
                if fit(s['lines'][0], 999, D['fit_box_px']['bubble'], L) < D['min_size']['bubble']:
                    E.append(f'{sw}: bubble line 1 "{s["lines"][0]}" too long to fit -> shorten')
                if len(s['lines']) > 1 and fit(s['lines'][1], 999, D['fit_box_px']['bubble2'], L) < D['fixed_size']['bubble2']:
                    E.append(f'{sw}: bubble line 2 "{s["lines"][1]}" clips at 90 px -> shorten')
            if sc == 'paper' and any(fit(x, 999, D['fit_box_px']['paper'], L) < D['min_size']['paper'] for x in s['lines']):
                E.append(f'{sw}: a paper line is too long to fit -> shorten')
            if sc == 'stamp':
                if fit(s['label'], 999, D['fit_box_px']['stamp_paper'], L) < D['min_size']['stamp_paper']:
                    E.append(f'{sw}: stamp label too long')
                if L == 'ko' and em(s['stamp'], L) * D['fixed_size']['stamp_word'] > D['fit_box_px']['stamp_word_ko']:
                    E.append(f'{sw}: stamp word "{s["stamp"]}" clips the red box (ko max ~2.8 Hangul) -> use a shorter word (실형, 유죄, 무죄)')
            if sc == 'tally' and em(s['label'], L) * D['fixed_size']['tally_label'] > D['fit_box_px']['tally_label']:
                E.append(f'{sw}: tally label clips -> shorten')
            if sc == 'phone' and any(em(x, L) * 44 > 380 for x in s['msgs']):
                E.append(f'{sw}: a phone message clips -> shorten')
    # hook auto-shrink must not go below the readable minimum
    D = LIB['defaults']
    h0, h1 = spec['hook']
    if fit(h0, D['fixed_size']['hook1'], D['fit_box_px']['hook'], L) < D['min_size']['hook1']:
        E.append(f'hook[0]: "{h0}" shrinks below {D["min_size"]["hook1"]} px -> shorten')
    m2 = D['min_size']['hook2'] if L != 'en' else D['min_size']['hook2_latin']
    if fit(h1, D['fixed_size']['hook2'], D['fit_box_px']['hook'], L) < m2:
        E.append(f'hook[1]: "{h1}" shrinks below {m2} px -> shorten')
    if len(spec['cover'].split('\n')) > 2:
        E.append('cover: at most 2 lines')
    # characters that look alike must not share an episode
    for a in sorted(looks):
        for b in sorted(looks):
            if a < b and confusable(a, b, pal) and not (a in stage.get('chars', []) and b in stage.get('chars', [])):
                E.append(f'characters {a} and {b} look alike (shirt and trousers) -> use a different look for one of them')
    # pops: templates never carry digits
    for p in spec.get('pops', []):
        for fld in ('big', 'small'):
            if re.search(r'\d', re.sub(r'{\w+}', '', p.get(fld, ''))):
                E.append(f'pops[{p["beat"]}].{fld}: "{p[fld]}" types a number -> put the number in vars from facts')
        if p['beat'] not in keys:
            E.append(f'pops: beat {p["beat"]} does not exist in lines')
        try:
            big, small, _ = render_pop(p, values, L)
            if fit(big, 118, 980, L) < 80:
                E.append(f'pops[{p["beat"]}].big: "{big}" shrinks to {fit(big, 118, 980, L)} px (< 80) -> fewer words in big, move detail to small')
            if L == 'ko':
                from factory.qa import gate
                for fld, txt in (('big', big), ('small', small)):
                    for key, (rx, item, sev) in gate.BANNED.items():
                        m = re.search(rx, txt)
                        if m and sev == 'FAIL':
                            E.append(f'pops[{p["beat"]}].{fld}: renders "{txt}" which breaks {item} ("{m.group(0)}") -> change the template')
            if fit(small, 64, 980, L) < 44:
                E.append(f'pops[{p["beat"]}].small: "{small}" too long')
        except (ValueError, KeyError, TypeError, AttributeError) as e:
            E.append(f'pops[{p["beat"]}]: {e}')
    # channel history: stage repeat and answer-position streaks
    hist = history(spec)
    if hist and hist[0][1] == spec['stage']:
        E.append(f'stage: {spec["stage"]} was the stage of the previous episode {hist[0][0]} -> pick another stage')
    qh = [h for h in hist if h[3] != 'result_first']  # result_first never shows the choice order: not checked, not counted
    if spec.get('format', 'quiz') != 'result_first' and len(qh) >= 2 and qh[0][2] == qh[1][2] == spec['quiz']['answer']:
        E.append(f'quiz.answer: answer {"ABC"[spec["quiz"]["answer"]]} would be the 3rd in a row ({qh[1][0]}, {qh[0][0]}) -> reorder the choices')
    return E, W


# Placeholder tokens that must never reach the screen (ja001: chunks "auto" left unexpanded rendered as "a/u", "t/o").
PLACEHOLDERS = {'', 'auto', 'todo', 'tbd', 'tbc', 'xxx', 'xx', '...', '\u2026', '?', '??', '???', '-', 'placeholder', 'lorem', 'fixme', 'null', 'none'}
SCREEN_KEYS = ('text', 'say', 'hook', 'cover', 'choices', 'emphasis', 'label', 'caption', 'title', 'shown', 'chunks', 'tts')


# Hook rules from the 2026-11-14 channel analysis: static title-card openings with the first sound at ~2 s had the worst swipe-away.
LEAD_SILENCE_MAX = 0.30
TITLE_KO_MAX = 30
TITLE_KO_ENDINGS = ('몇 년?', '몇 년 나왔을까?', '형량은?')
TITLE_KO_BANNED = ('쟁점', '어떤 형', '최후')


def title_rules_ko(title):
    """R4: ko meta title <= 30 chars, ends with a '몇 년' style question, no 쟁점/어떤 형/최후"""
    t = (title or '').strip()
    E = []
    if len(t) > TITLE_KO_MAX:
        E.append(f'title R4: {len(t)} chars > {TITLE_KO_MAX} -> shorten "{t}" (drop a modifier, keep the number and the person)')
    if not t.endswith(TITLE_KO_ENDINGS):
        E.append(f'title R4: must end with one of {" / ".join(TITLE_KO_ENDINGS)} -> e.g. "..., 몇 년?"')
    E += [f'title R4: contains "{w}" -> remove it (weak hook word)' for w in TITLE_KO_BANNED if w in t]
    return E


def first_sound_s(wav, db=-38.0):
    """seconds from the start of `wav` to the first sample louder than `db` dBFS (None if silent)"""
    import numpy as np
    import soundfile as sf
    x, sr = sf.read(str(wav), dtype='float32', always_2d=True)
    hit = np.nonzero(np.abs(x).max(1) > 10 ** (db / 20))[0]
    return round(float(hit[0]) / sr, 3) if len(hit) else None


def lead_silence_rule(t0, take=''):
    """R2: the first narration sound must start within 0.30 s of frame 0"""
    if t0 is None:
        return ['narration R2: no audible narration found -> rerun --from tts']
    if t0 > LEAD_SILENCE_MAX:
        return [f'narration R2: first sound at {t0:.2f} s > {LEAD_SILENCE_MAX} s after frame 0 (take {take}) -> trim the lead silence of the L01 take '
                f'or pick another take (rerun --from tts --force-tts), then --from timing']
    return []


def meta_leaks(text):
    """C: internal tokens that must never reach meta.txt (fact ids, formula notation, placeholders)"""
    E = [f'meta: internal token "{m.group()}" -> write the conversion in words or drop the line' for m in re.finditer(r'(?: = )?F\d+\.\w*| = F\d*', text)]
    E += [f'meta: placeholder "{m.group()}"' for m in re.finditer(r'\b(TODO|TBD)\b|\{\w+\}', text)]
    return E


def placeholder_text(obj, keys=SCREEN_KEYS, path='$'):
    """errors for on-screen / spoken text equal to a placeholder token (or empty), and for chunks that are not yet a list"""
    E = []
    bad = lambda x: isinstance(x, str) and x.strip().lower() in PLACEHOLDERS  # noqa: E731
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f'{path}.{k}'
            if k == 'chunks' and isinstance(v, str):
                E.append(f'{p} is "{v}", not a list of subtitle chunks -> run the chunk step (make_short.py compile / linebreak.py) or write the list')
            elif k in keys and bad(v):
                E.append(f'{p} is "{v}" (placeholder) -> write the real text')
            elif k in keys and isinstance(v, list) and all(isinstance(x, str) for x in v):
                E += [f'{p}[{i}] is "{x}" (placeholder) -> write the real text' for i, x in enumerate(v) if bad(x)]
            else:
                E += placeholder_text(v, keys, p)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            E += placeholder_text(v, keys, f'{path}[{i}]')
    return E


def desk_repeats(leg):
    """Two paper cards on the same desk colour read as the same shot (gate repeated_compositions)."""
    seen, E = {}, []
    for ui, u in enumerate(leg['lines']):
        for k, sh in enumerate(u.get('shots') or []):
            if sh['s'] == 'paper':  # paper vs paper only: a stamp card reads differently (gate never pairs them on references)
                col = (ui * 3 + k) % 5
                if col in seen:
                    E.append(f'{u["id"]} {sh["s"]} and {seen[col]} share desk colour {col} (look like the same shot) -> swap the order of the two shots in one of these lines, or use another scene')
                seen[col] = f'{u["id"]} {sh["s"]}'
    return E
