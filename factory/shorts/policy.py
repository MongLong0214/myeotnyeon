"""Facts/source verification and the policy linter for an episode spec.

Sources: every URL is fetched once and its readable text stored at episodes/specs/<id>.sources/<S>.txt (first line
`url: ...`). If a site blocks the fetch, the operator saves the article text into that file by hand (RESEARCH.md);
the build never treats an unreadable source as verified. Every quote must appear verbatim (whitespace-insensitive)
in its source text."""
import html
import re
import subprocess
import urllib.request
from pathlib import Path

from factory.shorts.core import ROOT, Fail, norm_ws, beat_keys, FINALITY_TEXT, FINALITY_TEXT_JA, nums_missing

UA = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36'


def page_text(raw, ctype=''):
    m = re.search(r'charset=([\w-]+)', ctype) or re.search(rb'charset=["\']?([\w-]+)', raw[:4000])
    enc = (m.group(1).decode() if isinstance(m.group(1), bytes) else m.group(1)) if m else 'utf-8'
    try:
        t = raw.decode(enc, errors='ignore')
    except LookupError:
        t = raw.decode('utf-8', errors='ignore')
    t = re.sub(r'(?is)<(script|style|noscript)[^>]*>.*?</\1>', ' ', t)
    t = html.unescape(re.sub(r'<[^>]+>', ' ', t))
    return re.sub(r'\s+', ' ', t).strip()


READER = 'https://r.jina.ai/'


def reader_text(url):
    """Article text as a browser renders it (public reader service; only the article URL is sent). '' on any failure."""
    try:
        req = urllib.request.Request(READER + url)  # a browser User-Agent gets 403 from the reader (11-14)
        with urllib.request.urlopen(req, timeout=60) as r:
            return re.sub(r'\s+', ' ', r.read().decode('utf-8', 'ignore')).strip()
    except Exception:  # noqa: BLE001
        return ''


def snapshot_dir(spec):
    return ROOT / 'episodes/specs' / f'{spec["id"]}.sources'


def fetch_sources(spec, refresh=False):
    """-> {source id: (status, text)}; status 'fetched' | 'snapshot' | 'error: ...'"""
    d = snapshot_dir(spec)
    d.mkdir(parents=True, exist_ok=True)
    out = {}
    for s in spec['sources']:
        p = d / f'{s["id"]}.txt'
        if p.exists() and not refresh:
            body = p.read_text()
            out[s['id']] = ('snapshot', body.split('\n', 1)[1] if body.startswith('url:') else body)
            continue
        try:
            req = urllib.request.Request(s['url'], headers={'User-Agent': UA, 'Accept-Language': 'ko,en;q=0.8,ja;q=0.6'})
            with urllib.request.urlopen(req, timeout=30) as r:
                raw, ctype = r.read(), r.headers.get('Content-Type', '')
            if raw[:5] == b'%PDF-':  # PDFs: poppler pdftotext
                t = re.sub(r'\s+', ' ', subprocess.run(['pdftotext', '-q', '-', '-'], input=raw, capture_output=True).stdout.decode('utf-8', 'ignore'))
            else:
                t = page_text(raw, ctype)
        except Exception as e:  # noqa: BLE001 - the reader fallback below may still get the article
            t, direct_err = '', e
        else:
            direct_err = None
        if len(t) < 4000:  # script-drawn article bodies (news1 11-14: headline only) -> the page as a browser renders it
            rt = reader_text(s['url'])
            if len(rt) > len(t):
                t = rt
        try:
            if len(t) < 300:
                raise direct_err or ValueError('page has almost no text')
            p.write_text(f'url: {s["url"]}\n{t}')
            out[s['id']] = ('fetched', t)
        except Exception as e:  # noqa: BLE001 - every failure becomes an actionable message
            out[s['id']] = (f'error: {str(e)[:80]}', '')
    return out


def check_facts(spec, fetched):
    E = []
    for sid, (st, _) in fetched.items():
        if st.startswith('error'):
            E.append(f'sources {sid}: could not read the page ({st}) -> open it in a browser or Tavily extract, paste the article '
                     f'text into {snapshot_dir(spec).relative_to(ROOT)}/{sid}.txt (first line "url: <url>"), then rebuild')
    for f in spec['facts']:
        for q in f['quotes']:
            st, text = fetched.get(q['source'], ('error', ''))
            if st.startswith('error'):
                continue
            if norm_ws(q['text']) not in norm_ws(text):
                short = len(text) < 4000
                E.append(f'facts {f["id"]}: quote not found in {q["source"]}: "{q["text"][:50]}" -> copy the sentence exactly from '
                         f'{snapshot_dir(spec).relative_to(ROOT)}/{q["source"]}.txt' + (
                             f' (that file has only {len(text)} chars: the page body is probably drawn by script; paste the full article '
                             f'text into it by hand, keeping the first line "url: ...", then rerun)' if short else ''))
    E += verdict_date_errors(spec, [t for st, t in fetched.values() if not st.startswith('error')])
    if E:
        raise Fail('facts', E)


MONTHS_EN = 'January February March April May June July August September October November December'.split()


def verdict_date_errors(spec, source_texts=()):
    """a verdict date must be written in a quote or a source text (10월 20일 / Oct. 20 / 10月20日); otherwise it is "unknown" """
    d = spec.get('case', {}).get('verdict_date')
    if not d or d == 'unknown':
        return []
    m, day = int(d[5:7]), int(d[8:10])
    mon = MONTHS_EN[m - 1] if 1 <= m <= 12 else 'x'
    rx = rf'(?<!\d){m}\s?[월月]\s?{day}\s?[일日]|\b{mon[:3]}[a-z]*\.?\s+{day}(?!\d)|(?<!\d){day}\s+{mon[:3]}'
    hay = [q['text'] for f in spec['facts'] for q in f['quotes']] + list(source_texts)
    if any(re.search(rx, t, re.I) for t in hay):
        return []
    return [f'case.verdict_date: {d} ({m}월 {day}일 / {mon[:3]}. {day} / {m}月{day}日) is not written in any quote or source text -> a report date is not a '
            f'verdict date; set "verdict_date": "unknown" or quote the sentence that gives the date']


SEX = {'ko': r'성폭행|성폭력|강간|성추행|추행|성범죄|불법\s?촬영|몰카|성착취|성매매|음란', 'en': r'\brape|sexual|molest|indecent|porn|prostitut',
       'ja': r'性的|強姦|強制わいせつ|わいせつ|盗撮|買春|売春'}
CHILD = {'ko': r'아동|미성년|초등학생|중학생|고등학생|영아|신생아|유아|어린이|여아|남아', 'en': r'\bchild|\bminor\b|toddler|infant|\bteen|\bkid\b|\bboy\b|\bgirl\b|baby girl|baby boy',
         'ja': r'児童|未成年|幼児|乳児|小学生|中学生|高校生|子ども|女児|男児'}
GAG = {'ko': r'ㅋ|ㅎㅎ|웃기|개웃|꿀잼', 'en': r'\blol\b|lmao|haha|funny', 'ja': r'笑|ｗｗ|草'}
PLACEHOLDER = r'#N\b|#\d+\b|\bTBD\b|\bTODO\b|\bXXX\b|\?\?\?|lorem|placeholder|미정|확인\s?필요|\[[^\]]*\]|\{[^}]*\}|＿＿|__'
EN_NUMWORD = r'\b(two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|seventeen|eighteen|nineteen|twenty|thirty|forty|fifty|sixty|seventy|eighty|ninety|hundred|thousand|million)\b'
JA_KANJI_NUM = r'[一二三四五六七八九十百千]{2,}'
# says "final" in the non-negated form (not: 확정 전 / 확정되지 / 확정 안 / 미확정, not final / isn't final / not yet final, 未確定 / 確定していません)
NOT_FINAL = {'ko': r'(?<!미)확정(?!\s?전|되지|돼지|\s?안\s|이 아니)', 'en': r"(?<!\bnot )(?<!n't )(?<!not yet )\bfinal(?:ized)?\b|\bupheld\b",
             'ja': r'(?<!未)確定(?!していません|していない|しておらず|せず)'}
SAYS_FINAL = '|'.join([NOT_FINAL['ko'], NOT_FINAL['en'].split('|')[0], NOT_FINAL['ja']])
SAYS_APPEAL = r'항소|상고|appeal|控訴|上告'


def finality_errors(spec):
    """P0-3: a declared finality needs a fact quote that says so"""
    fin = spec.get('case', {}).get('finality')
    quotes = [q['text'] for f in spec.get('facts', []) for q in f['quotes']]
    fix = 'set 항소 미확인 / appeal_unknown or add the quote'
    if fin in ('확정', 'final') and not any(re.search(SAYS_FINAL, q, re.I) for q in quotes):
        return [f'case.finality: "{fin}" but no fact quote says the verdict is final (확정 / final / finalized / 確定) -> {fix}']
    if fin in ('항소', '상고', 'appealed') and not any(re.search(SAYS_APPEAL, q, re.I) for q in quotes):
        return [f'case.finality: "{fin}" but no fact quote mentions an appeal (항소 / 상고 / appeal / 控訴 / 上告) -> {fix}']
    return []


def meta_numbers(spec):
    """P0-4: numbers in title, description, hook, cover and the correct choice must be in some fact's quotes (wrong choices are exempt)"""
    quotes = '\n'.join(q['text'] for f in spec.get('facts', []) for q in f['quotes'])
    rows = [('title', spec['title']), ('description', spec['description'])]
    if spec['variant'] == 'B3':
        rows += [('cover', spec['cover']), ('hook[0]', spec['hook'][0]), ('hook[1]', spec['hook'][1]),
                 ('quiz.choices[answer]', spec['quiz']['choices'][spec['quiz']['answer']])]
    E = []
    for where, t in rows:
        miss = nums_missing(t, quotes, spec['locale'])
        if miss:
            E.append(f'{where}: numbers {miss} are not in any fact quote (same number and unit) -> write the number as a source writes it, or add the quote that has it')
    return E


def texts(spec):
    """(where, text, kind) for everything a viewer reads; kind 'screen' (subtitle/card) or 'meta'"""
    out = [('title', spec['title'], 'meta'), ('description', spec['description'], 'meta')]
    if spec['variant'] == 'B3':
        out += [('cover', spec['cover'], 'screen'), ('hook[0]', spec['hook'][0], 'screen'), ('hook[1]', spec['hook'][1], 'screen')]
        out += [(f'quiz.choices[{i}]', c, 'screen') for i, c in enumerate(spec['quiz']['choices'])]
    for k, ln in zip(beat_keys(spec['lines']), spec['lines']):
        out.append((f'lines[{k}].text', ln['text'], 'screen'))
        for j, s in enumerate(ln.get('shots', [])):
            for x in (s.get('lines') or []) + (s.get('msgs') or []) + [s.get('label') or '', s.get('stamp') or '']:
                if x:
                    out.append((f'lines[{k}].shots[{j}]', x, 'screen'))
    for p in spec.get('pops', []):
        out += [(f'pops[{p["beat"]}].big', re.sub(r'{\w+}', '', p['big']), 'screen'), (f'pops[{p["beat"]}].small', re.sub(r'{\w+}', '', p.get('small', '')), 'screen')]
    return out


def lint(spec):
    """Policy linter. Returns (errors, warnings)."""
    E, W = [], []
    L, c = spec['locale'], spec.get('case', {})
    if c.get('sexual_offence'):
        E.append('case.sexual_offence: sex crimes are never made (channel policy) -> pick another case')
    if c.get('victim_minor'):
        E.append('case.victim_minor: cases with child victims are never made -> pick another case')
    if c.get('deaths', 0) > 0 and not c.get('grave'):
        E.append('case.grave: a case with deaths must set "grave": true')
    corpus = texts(spec) + [(f'facts {f["id"]}.claim', f['claim'], 'meta') for f in spec['facts']]
    for where, t, kind in corpus:
        if re.search(SEX[L], t, re.I):
            E.append(f'{where}: sex-crime wording "{re.search(SEX[L], t, re.I).group(0)}" -> this case is out of policy')
        if re.search(CHILD[L], t, re.I):
            E.append(f'{where}: child wording "{re.search(CHILD[L], t, re.I).group(0)}" -> cases involving children are out of policy')
        if re.search(PLACEHOLDER, t, re.I) and not where.startswith('pops'):
            E.append(f'{where}: placeholder "{re.search(PLACEHOLDER, t, re.I).group(0)}" -> write the real text')
        if c.get('grave') and re.search(GAG[L], t, re.I):
            E.append(f'{where}: joke wording in a grave case')
        if kind == 'screen' and L == 'en' and re.search(EN_NUMWORD, t, re.I) and not where.startswith('pops'):
            E.append(f'{where}: write numbers as digits on screen ("{re.search(EN_NUMWORD, t, re.I).group(0)}")')
        if kind == 'screen' and L == 'ja' and re.search(JA_KANJI_NUM, t):
            E.append(f'{where}: write numbers as digits on screen ("{re.search(JA_KANJI_NUM, t).group(0)}")')
        fin = c.get('finality', '')
        if fin and fin not in ('확정', 'final') and re.search(NOT_FINAL[L], t, re.I) and not where.startswith('facts'):
            E.append(f'{where}: says the verdict is final, but case.finality is "{fin}"')
        if c.get('instance') in ('심급 미표기',) and re.search(r'[123]심|항소심|1審|2審', t):
            E.append(f'{where}: names a court instance the sources do not state')
    if L == 'ko':
        from factory.qa import gate
        for where, t, kind in corpus:
            if kind != 'screen' and not where.startswith('title'):
                continue
            for key, (rx, item, sev) in gate.BANNED.items():
                if key == 'disclaimer' and where == 'description':
                    continue
                m = re.search(rx, t)
                if m:
                    (E if sev == 'FAIL' else W).append(f'{where}: {item} "{m.group(0)}" ({key}) -> rewrite')
        if len(spec['title']) > 45:
            E.append(f'title: {len(spec["title"])} chars > 45 (ko) -> shorten')
        if spec['variant'] == 'B3':
            from factory.qa import subtitle_ko
            for where, t in [('cover', spec['cover']), ('opinion', '이 형량,\n가볍다 / 적당 / 무겁다?')]:
                ls = t.split('\n')
                for i in range(len(ls) - 1):
                    v = subtitle_ko.judge(ls[i], ls[i + 1])
                    if v and v[0] == 'FAIL':
                        E.append(f'{where}: line break "{ls[i]} / {ls[i + 1]}" breaks a phrase (H23: {v[1]}) -> move the \\n')
    else:
        if len(spec['title']) > (60 if L == 'en' else 40):
            E.append(f'title: too long for {L}')
    if spec['variant'] == 'B3' and c.get('finality') not in (FINALITY_TEXT_JA if L == 'ja' else FINALITY_TEXT):
        E.append(f'case.finality: "{c.get("finality")}" has no standard sentence' + (' in ja -> use final / appeal_unknown / appealed / not_final' if L == 'ja' else ''))
    E += finality_errors(spec) + meta_numbers(spec)
    return E, W
