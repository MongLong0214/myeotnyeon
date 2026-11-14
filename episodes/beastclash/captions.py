"""Beast Clash caption splitter (1-3 words per caption, one font size for every caption).

Rules, in order:
 1. Units never split: a kept name ("great white shark", plural too), a number with its unit ("22,000 lbs", "3 in."),
    and a verb with its particle ("rears up.", "closes in!", "backs away!"; a particle that ends its clause belongs
    to the word before it).
 2. Sentence punctuation (. ! ?) is a hard break. A caption never carries a lone word from the next sentence; the only
    caption that may cross a sentence end is a one-word exclamation followed by at least two words ("BAM! The shark").
    "vs" ends a caption rather than starting one.
    A unit abbreviation with a full stop ("in.", "ft.", "lbs.") is not a sentence end.
 3. Inside a sentence, captions are at most MAX_WORDS words and MAX_CHARS characters, so one font size fits every
    caption (Film.tsx CAP_FONT). The split with the fewest captions wins; ties go to breaks after , or :, then to
    captions that do not end on a function word ("the", "a", "to", ...), then to even lengths.
need_s(caption) is the shortest on-screen time a caption may get: 0.25 s per word, never under 0.4 s (gate.py
--cue-rule per_word asks 0.35 s; the factory timing step asks 0.4 s)."""
import re

MAX_WORDS, MAX_CHARS = 3, 18
PARTICLES = {'up', 'down', 'in', 'out', 'away', 'off', 'back', 'on', 'over', 'around', 'through', 'apart', 'aside'}
FUNCTION = {'the', 'a', 'an', 'your', 'my', 'his', 'her', 'its', 'their', 'our', 'to', 'of', 'and', 'or', 'but', 'than',
            'at', 'for', 'with', 'from', 'by', 'into', 'onto', 'can', 'will', 'is', 'are', 'was', 'were', 'more'}
UNIT = r'(?:lbs?|pounds?|tons?|ft|feet|foot|in|inch|inches|mph|kg|m|cm|km/h|miles)'
ABBR = re.compile(r'^(?:lbs|lb|ft|in|oz|vs|mph|kg|cm|km)\.$', re.I)


def bare(w):
    return re.sub(r"[^a-z0-9']", '', w.lower())


def ends_sentence(w):
    return bool(re.search(r'[.!?]["\')]*$', w)) and not ABBR.match(w)


def units_of(text, keep=()):
    ws = text.split()
    low = [bare(w) for w in ws]
    ph = {tuple(p.lower().split()) for p in keep}
    ph |= {p[:-1] + (p[-1] + 's',) for p in ph}
    ph = sorted(ph, key=len, reverse=True)
    out, k = [], 0
    while k < len(ws):
        m = next((len(p) for p in ph if tuple(low[k:k + len(p)]) == p), 0)
        # a qualifier stays with its number: "up to 9,920 pounds", "about 20 feet" (CEO bc004: "up / to 3 in." read badly)
        q = 2 if low[k:k + 2] == ['up', 'to'] else 1 if low[k] in ('about', 'over', 'nearly', 'almost', 'around', 'roughly') else 0
        if not m and q and k + q < len(ws) and re.match(r'^[\d,.]+[!?,.:]*$', ws[k + q]):
            m = q + 1 + (1 if k + q + 1 < len(ws) and re.match('^' + UNIT + r'\b\.?[!?,.:]*$', ws[k + q + 1], re.I) else 0)
        if not m and re.match(r'^[\d,.]+$', ws[k]) and k + 1 < len(ws) and re.match('^' + UNIT + r'\b\.?[!?,.:]*$', ws[k + 1], re.I):
            m = 2
        if not m and k + 1 < len(ws) and bare(ws[k + 1]) in PARTICLES and bare(ws[k]) not in FUNCTION and not ends_sentence(ws[k]) \
                and (k + 2 == len(ws) or re.search(r'[.!?,:;]$', ws[k + 1])):
            m = 2
        out.append(ws[k:k + max(1, m)])
        k += max(1, m)
    return out


def sentences(units):
    out = [[]]
    for u in units:
        out[-1].append(u)
        if ends_sentence(u[-1]):
            out.append([])
    return [s for s in out if s]


def _best(units):
    """fewest captions, then breaks after , :, then no function-word endings, then even lengths"""
    n = len(units)
    best = [None] * (n + 1)
    best[0] = (0, 0.0, [])
    for j in range(1, n + 1):
        for i in range(j):
            if best[i] is None:
                continue
            g = [w for u in units[i:j] for w in u]
            txt = ' '.join(g)
            if (len(g) > MAX_WORDS or len(txt) > MAX_CHARS) and j - i > 1:
                continue
            last = g[-1]
            pen = 0.0 if j == n else (-2.0 if re.search(r'[,:;]$', last) else 0.0) + (6.0 if bare(last) in FUNCTION else 0.0)
            pen += 1.5 if len(g) == 1 and n > 1 else 0.0
            pen += 1.0 if bare(g[0]) == 'vs' else 0.0   # "vs" closes the first name ("32 ft vs" / "21 feet!")
            pen += .05 * abs(len(txt) - 12)
            cand = (best[i][0] + 1, best[i][1] + pen, best[i][2] + [txt])
            if best[j] is None or cand[:2] < best[j][:2]:
                best[j] = cand
    return best[n][2]


def split(text, keep=()):
    """-> captions (list of str) for one narration line"""
    out, carry = [], None
    for s in sentences(units_of(text, keep)):
        if carry is not None:
            words = sum(len(u) for u in s)
            if words >= 2 and len(s[0]) + 1 <= MAX_WORDS:
                s = [carry + s[0]] + s[1:]
            else:
                out.append(' '.join(carry))
            carry = None
        if len(s) == 1 and len(s[0]) == 1 and re.search(r'!$', s[0][0]):
            carry = s[0]
            continue
        out += _best(s)
    if carry is not None:
        out.append(' '.join(carry))
    return out


def need_s(caption):
    return max(.4, .25 * len(caption.split()))
