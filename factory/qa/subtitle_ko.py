"""Korean subtitle line/cue break lint (H17a, H23a-c) with the kiwipiepy morphological analyser.

Every break is checked: the line break inside a cue and the boundary between two cues of one sentence.
Falls back to factory.lib.captions.bond() rules when kiwipiepy is not installed.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from factory.lib import captions as cap  # noqa: E402

try:
    from kiwipiepy import Kiwi
    _KIWI = Kiwi()
except Exception:  # pragma: no cover - fallback path
    _KIWI = None

SENT_END = re.compile(r'[.?!…]["\'”’)\]]*$')
CLAUSE_END = re.compile(r'[,;:·]["\'”’)\]]*$')
POSITIONAL = {'안', '위', '밖', '끝', '앞', '뒤', '전', '후', '중', '동안', '사이', '속', '옆', '아래', '밑'}
DATE_UNIT = {'년', '월', '일', '시', '분', '초'}


def parse_srt(path):
    text = Path(path).read_text(encoding='utf-8-sig')
    cues = []
    for block in re.split(r'\n\s*\n', text.strip()):
        rows = block.strip().splitlines()
        if len(rows) < 2:
            continue
        i = 1 if '-->' in rows[1] else 0
        m = re.match(r'(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)', rows[i])
        if not m:
            continue
        g = list(map(int, m.groups()))
        a = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000
        b = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000
        lines = [r.strip() for r in rows[i + 1:] if r.strip()]
        cues.append(dict(idx=len(cues) + 1, start=a, end=b, lines=lines, text='\n'.join(lines)))
    return cues


def _tokens(text):
    return [(t.form, t.tag, t.start, t.start + t.len) for t in _KIWI.tokenize(text)]


def _judge_kiwi(left, right):
    """left/right: text on each side of one break. Returns (severity, code, why) or None."""
    text = left + ' ' + right
    cut = len(left)
    toks = _tokens(text)
    before = [t for t in toks if t[3] <= cut]
    after = [t for t in toks if t[2] >= cut]
    if not before or not after:
        return None
    a, b = before[-1], after[0]
    a_tag, b_tag = a[1], b[1]
    a_word = left.split()[-1] if left.split() else ''
    if SENT_END.search(left) or CLAUSE_END.search(left):
        # A clause end is the best break; only a dependent-noun start after a comma is still wrong (", 건").
        if b_tag == 'NNB' and not re.match(r'\d', right):
            return ('FAIL', 'H23a_dependent_noun_start', f'line/cue starts with dependent noun {b[0]}/{b_tag}')
        return None
    # H23a: things that can never open a line or cue
    if b_tag == 'NNB':
        if a_tag == 'SN':
            return ('FAIL', 'H17a_number_unit_split', f'number {a[0]} | unit {b[0]}')
        return ('FAIL', 'H23a_dependent_noun_start', f'starts with dependent noun {b[0]}/{b_tag}')
    if b_tag.startswith('J'):
        return ('FAIL', 'H23a_particle_start', f'starts with particle {b[0]}/{b_tag}')
    if b_tag == 'VX':
        return ('FAIL', 'H23a_auxiliary_start', f'auxiliary verb {b[0]} split from {a[0]}')
    if b_tag.startswith(('E', 'XS')) or b_tag == 'VCP':
        return ('FAIL', 'H23a_ending_start', f'starts with ending/suffix/copula {b[0]}/{b_tag}')
    if b[0] in POSITIONAL and b_tag.startswith('NN') and a_tag in ('ETM', 'SN', 'NNB', 'NNG', 'NNP'):
        return ('FAIL', 'H23a_positional_noun_start', f'positional noun {b[0]} split from {a[0]}')
    # H23b: modifier | head noun, determiner | noun, number | unit, date parts, noun compounds
    if b_tag == 'VCN':
        return ('FAIL', 'H23a_negative_copula_start', f'starts with 아니- ({b[0]}) split from {a_word}')
    if a_tag == 'NP' and b_tag.startswith('NN'):
        return ('FAIL', 'H23b_pronoun_noun_split', f'{a_word} | noun {b[0]}')
    if a_tag == 'ETM' and (b_tag.startswith('N') or b_tag in ('SL', 'SN', 'XPN', 'MM')):
        return ('FAIL', 'H23b_adnominal_noun_split', f'adnominal {a_word} | noun {b[0]}')
    if a_tag == 'MM':
        return ('FAIL', 'H23b_determiner_split', f'determiner {a[0]} | {b[0]}')
    if a_tag == 'SN' and b_tag.startswith('N'):
        return ('FAIL', 'H17a_number_unit_split', f'number {a[0]} | {b[0]}')
    if a_tag in ('NNB', 'NNG') and a[0] in DATE_UNIT and b_tag == 'SN' and re.match(r'\d+(월|일|시|분)', right):
        return ('FAIL', 'H23b_date_split', f'date split {a_word} | {right.split()[0]}')
    if a_tag in ('NNG', 'NNP', 'SL', 'SH') and (b_tag in ('NNG', 'NNP', 'SL')):
        return ('FAIL', 'H23b_noun_compound_split', f'noun {a_word} | noun {b[0]} (compound or bare noun)')
    if a_tag == 'XPN':
        return ('FAIL', 'H23b_prefix_split', f'prefix {a[0]} | {b[0]}')
    # Weak but allowed only with a reason (H23c priority): adverb | verb, genitive | noun, argument | relative clause
    if a_tag == 'MAG' and b_tag.startswith('V'):
        return ('REVIEW', 'H23c_adverb_verb_split', f'adverb {a_word} | verb {b[0]}')
    if a_tag == 'JC' and b_tag.startswith(('NN', 'VA', 'XPN')):
        return ('REVIEW', 'H23c_coordination_split', f'coordinated noun {a_word} | {b[0]}')
    if a_tag in ('NNG', 'NNP') and b_tag in ('NR', 'MM', 'SN'):
        return ('REVIEW', 'H23c_noun_quantity_split', f'noun {a_word} | quantity {b[0]}')
    if a_tag == 'MAG' and b_tag == 'MAG':
        return ('REVIEW', 'H23c_adverb_adverb_split', f'{a_word} | {b[0]}')
    if a_tag == 'JKG':
        return ('REVIEW', 'H23c_genitive_split', f'genitive {a_word} | {b[0]}')
    if a_tag.startswith('JK') and b_tag.startswith('V'):
        rest = [t for t in after[:4]]
        if any(t[1] == 'ETM' for t in rest):
            return ('REVIEW', 'H23c_argument_relative_split', f'argument {a_word} | relative clause {right.split()[0]}')
    return None


def _judge_rules(left, right):
    a, b = left.split()[-1], right.split()[0]
    s = cap.bond(a, b)
    if cap.is_particle(b):
        return ('FAIL', 'H23a_particle_start', f'starts with particle {b}')
    if s >= 3:
        return ('FAIL', 'H23_bond3', f'{a} | {b} (rule bond 3)')
    if s == 2:
        return ('REVIEW', 'H23c_bond2', f'{a} | {b} (rule bond 2)')
    return None


def judge(left, right):
    left, right = left.strip(), right.strip()
    if not left or not right:
        return None
    return _judge_kiwi(left, right) if _KIWI else _judge_rules(left, right)


def lint_cues(cues, line_max=18, max_lines=2):
    """All breaks of all cues -> list of dict(cue, kind, left, right, severity, code, why, start, end)."""
    out, breaks = [], []
    for k, c in enumerate(cues):
        lines = c['lines']
        if len(lines) > max_lines:
            out.append(dict(cue=c['idx'], kind='cue', severity='FAIL', code='H5_over_two_lines', why=f'{len(lines)} lines',
                            text=c['text'], start=c['start'], end=c['end']))
        for ln in lines:
            if len(ln) > line_max:
                out.append(dict(cue=c['idx'], kind='line', severity='FAIL', code='H5_line_too_long',
                                why=f'{len(ln)} chars > {line_max}', text=ln, start=c['start'], end=c['end']))
        for i in range(len(lines) - 1):
            left = ' '.join(lines[:i + 1])
            right = ' '.join(lines[i + 1:])
            # context: whole cue, plus the next cue if the sentence continues
            if k + 1 < len(cues) and not SENT_END.search(lines[-1]):
                right = right + ' ' + ' '.join(cues[k + 1]['lines'])
            breaks.append((c, 'line', left, right, lines[i], lines[i + 1]))
        if k + 1 < len(cues) and not SENT_END.search(lines[-1] if lines else ''):
            nxt = cues[k + 1]
            breaks.append((c, 'cue', ' '.join(lines), ' '.join(nxt['lines']), lines[-1], nxt['lines'][0]))
    for c, kind, left, right, l1, l2 in breaks:
        v = judge(left, right)
        row = dict(cue=c['idx'], kind=kind, before=l1, after=l2, start=c['start'], end=c['end'],
                   severity=v[0] if v else 'OK', code=v[1] if v else '', why=v[2] if v else '')
        if kind == 'cue' and v is None:
            # H17a: a cue that stops mid-phrase (no ending, no particle) even when the morphemes allow it
            last = _tokens(left)[-1][1] if _KIWI else ''
            if _KIWI and not (last.startswith(('E', 'J', 'S')) or last in ('VCP',)):
                row.update(severity='REVIEW', code='H17a_cue_ends_mid_phrase', why=f'cue ends on {last} without ending/punctuation')
        out.append(row)
    return out, ('kiwipiepy' if _KIWI else 'rules(captions.bond)')
