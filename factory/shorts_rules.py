"""Shorts format rules from the reference-channel study (REPORT.md in the research/ref_channel_UC... folder).

Three parts, all simple:
- SPEC_TEMPLATE + check_spec(spec): beat timings written into the episode spec before rendering;
- measure(video, words): report-only picture/audio numbers on a finished Short (gate SHORTS_RULES);
- title helpers: ends with '?', one key word in single quotes, about 24 chars;
- check_pair(title, thumb_text): report-only title/thumbnail pair check.

  .venv/bin/python factory/shorts_rules.py measure VIDEO [--asr asr.json]
  .venv/bin/python factory/shorts_rules.py title "층간소음에" "망치" "들면 몇 년 나옴?"
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
import numpy as np

# Targets (reference top-15 medians; report-only until calibrated against our own retention numbers).
RULES = dict(
    hook_question_end_max=3.5, expectation_window=(4.0, 5.0), twist_max=6.5,
    subscribe_window=(7.0, 8.0), subscribe_max_dur=1.0, number_pops=(5, 7),
    setting_mean_target=1.5, setting_max=4.5, setting_threshold=1.2, first_word_max=0.2,
    pause_min=0.5, pause_max_count=0, loop_diff_max=25.0, title_len=(20, 28),
)
BANNED_END_CARD = ('댓글', '남겨주세요', '구독과 좋아요')

# Copy into the episode spec (`shorts_spec` in review_inputs.json or the episode entry) and fill in.
SPEC_TEMPLATE = {
    'opening_template': 'A',            # A/B/C in factory/unslop/STYLE_VIDEO.md "Opening templates"; rotate
    'hook_question': {'text': '…몇 년 나왔을까요?', 'end_s': 3.2},
    'expectation': {'text': '…정도 나올 것 같지만', 'at_s': 4.5},
    'twist': {'text': '실제 판결은 …', 'at_s': 6.2},
    'subscribe_gag': {'at_s': 7.3, 'dur_s': 0.8, 'gag': 'character gag, no words like 댓글 남겨주세요'},
    'loop': {'last_line': '…그날 밤 배달을 받던', 'first_shot': 'S1', 'cut_at': 'modifier'},
    'number_pops': [
        {'at_s': 9.0, 'value': '벌금 300만 원', 'source': 'judgment / facts.md line',
         'life_unit': '치킨 150마리', 'basis': '치킨 1마리 2만 원 기준'},
    ],
}


def _issue(out, field, msg):
    out.append(dict(field=field, issue=msg))


def check_spec(spec):
    """Spec timing/content rules -> list of issues (empty = OK)."""
    r, out = RULES, []
    hq = spec.get('hook_question') or {}
    if not hq.get('text', '').rstrip().endswith('?'):
        _issue(out, 'hook_question', 'must be a question ending with ?')
    if hq.get('end_s') is None or hq['end_s'] > r['hook_question_end_max']:
        _issue(out, 'hook_question', f'must end by {r["hook_question_end_max"]} s')
    ex = spec.get('expectation') or {}
    lo, hi = r['expectation_window']
    if ex.get('at_s') is None or not lo <= ex['at_s'] <= hi:
        _issue(out, 'expectation', f'expectation line ("~나올 것 같지만") at {lo}-{hi} s')
    tw = spec.get('twist') or {}
    if tw.get('at_s') is None or tw['at_s'] > r['twist_max'] or (ex.get('at_s') is not None and tw['at_s'] <= ex['at_s']):
        _issue(out, 'twist', f'real-verdict twist after the expectation and by {r["twist_max"]} s')
    sg = spec.get('subscribe_gag') or {}
    lo, hi = r['subscribe_window']
    if sg.get('at_s') is None or not lo <= sg['at_s'] <= hi or sg.get('dur_s', 99) > r['subscribe_max_dur']:
        _issue(out, 'subscribe_gag', f'one character gag at {lo}-{hi} s, at most {r["subscribe_max_dur"]} s')
    if any(w in json.dumps(spec, ensure_ascii=False) for w in ('댓글로 남겨', '댓글 남겨')):
        _issue(out, 'subscribe_gag', 'no end-card "댓글 남겨주세요"')
    lp = spec.get('loop') or {}
    if not lp.get('last_line') or not lp.get('first_shot'):
        _issue(out, 'loop', 'last line cut at a modifier and linked to the first shot')
    elif re.search(r'[.?!]$', lp['last_line'].strip()):
        _issue(out, 'loop', 'last line must stop mid-phrase (no final punctuation)')
    pops = spec.get('number_pops') or []
    lo, hi = r['number_pops']
    if not lo <= len(pops) <= hi:
        _issue(out, 'number_pops', f'{lo}-{hi} life-unit number pops (have {len(pops)})')
    for i, p in enumerate(pops):
        if not p.get('source'):
            _issue(out, f'number_pops[{i}]', 'legal number needs its source (exact figure)')
        if p.get('life_unit') and not p.get('basis'):
            _issue(out, f'number_pops[{i}]', f'conversion "{p["value"]} = {p["life_unit"]}" must state its basis')
    return out


# ---------- title ----------

def make_title(before, keyword, after='몇 년 나옴?'):
    return f"{before.strip()} '{keyword.strip()}' {after.strip()}".strip()


def check_title(title):
    lo, hi = RULES['title_len']
    out = []
    if not title.endswith('?'):
        out.append('ends with ?')
    if len(re.findall(r"'[^']+'", title)) != 1 or title.count("'") != 2:
        out.append('exactly one key word in single quotes')
    if not lo <= len(title) <= hi:
        out.append(f'{lo}-{hi} chars (have {len(title)})')
    return out


# ---------- title / thumbnail pair (report-only) ----------
# Portions adapted from youtube-agent-skill (MIT, © 2026 UtilLayer, © 2026 Jake Schincariol): skills/yt-package/title.py and
# SKILL.md — the thumbnail should add to the title rather than repeat it, stay short, and the title
# must work in its first ~40 characters on mobile. Korean particle handling is ours.
# Notice: research/youtube-agent-skill/src/LICENSE; see factory/THIRD_PARTY.md.

PARTICLES = ('으로', '은', '는', '이', '가', '을', '를', '로', '에', '의', '와', '과', '도', '만')
PAIR_RULES = dict(thumb_eojeol_max=3, mobile_preview_chars=40)


def strip_particle(word):
    """One trailing particle off a word; the stem must keep at least two characters for one-character
    particles ('나이' stays, '노동자에' -> '노동자') and one for '으로'."""
    w = re.sub(r"[^\w가-힣]", '', word)
    for p in sorted(PARTICLES, key=len, reverse=True):
        if w.endswith(p) and len(w) - len(p) >= (1 if len(p) > 1 else 2):
            return w[:-len(p)]
    return w


def _stems(text):
    text = re.sub(r'#\S+', ' ', text)
    return [s for s in (strip_particle(w) for w in text.split()) if s]


def check_pair(title, thumb_text):
    """Report-only: thumbnail words that repeat the title, thumbnail length in eojeol, mobile preview."""
    title_stems = set(_stems(title))
    thumb_words = thumb_text.split()
    repeated = sorted({s for s in _stems(thumb_text) if s in title_stems})
    n = PAIR_RULES['mobile_preview_chars']
    preview = title[:n]
    issues = []
    if repeated:
        issues.append(f'thumbnail repeats title words: {", ".join(repeated)}')
    if len(thumb_words) > PAIR_RULES['thumb_eojeol_max']:
        issues.append(f'thumbnail text {len(thumb_words)} eojeol (max {PAIR_RULES["thumb_eojeol_max"]})')
    if len(title) > n:
        issues.append(f'title {len(title)} chars; mobile shows "{preview}…"')
    return dict(status='ADVISORY', report_only=True, issues=issues, repeated=repeated,
                thumb_eojeol=len(thumb_words), mobile_preview=preview, truncated=len(title) > n)


# ---------- measurement (report-only) ----------

def _frames(video, fps, w, h):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(video), '-vf', f'fps={fps},scale={w}:{h},format=rgb24',
                          '-f', 'rawvideo', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)


def _hist(fr, m):
    """HSV histogram (12 hues x 3 sat x 4 val + grey bin) of the unmasked pixels."""
    x = fr[m].astype(np.float32) / 255
    mx, mn = x.max(1), x.min(1)
    s = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0)
    r, g, b = x.T
    d = np.maximum(mx - mn, 1e-6)
    hue = np.where(mx == r, ((g - b) / d) % 6, np.where(mx == g, (b - r) / d + 2, (r - g) / d + 4)) / 6
    hb = np.where(s < 0.15, 12, np.minimum((hue * 12).astype(int), 11))
    idx = hb * 12 + np.minimum((s * 3).astype(int), 2) * 4 + np.minimum((mx * 4).astype(int), 3)
    c = np.bincount(idx, minlength=13 * 12).astype(np.float32)
    return c / c.sum()


def setting_changes(video, threshold=RULES['setting_threshold'], fps=4):
    """Background/setting changes (ported from the research folder's data/setting.py): HSV histogram L1
    distance from the segment's anchor frame at 4 fps, subtitle band and corner masked, segments >= 0.5 s."""
    W, H = 36, 64
    a = _frames(video, fps, W, H)
    if not len(a):
        return dict(n=0, times=[], mean_len=0.0, max_len=0.0)
    dur = len(a) / fps
    m = np.ones((H, W), bool)
    m[int(H * 0.58):int(H * 0.72), :] = False
    m[int(H * 0.88):, int(W * 0.8):] = False
    hs = [_hist(x, m) for x in a]
    seg, anchor = [0.0], hs[0]
    for i in range(1, len(a)):
        if np.abs(hs[i] - anchor).sum() > threshold and i / fps - seg[-1] >= 0.5:
            seg.append(i / fps)
            anchor = hs[i]
    lens = np.diff(seg + [dur])
    return dict(n=len(seg), per_min=round(len(seg) / dur * 60, 1), mean_len=round(float(lens.mean()), 2),
                max_len=round(float(lens.max()), 2), times=seg)


def pauses(audio_or_video, words, minimum=RULES['pause_min'], noise='-40dB'):
    """Silences longer than `minimum` inside the narration span (first word start to last word end)."""
    log = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(audio_or_video), '-af',
                          f'silencedetect=n={noise}:d={minimum}', '-f', 'null', '-'], capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r'silence_start: (-?[\d.]+)', log)]
    ends = [float(x) for x in re.findall(r'silence_end: (-?[\d.]+)', log)]
    a, b = (words[0]['start'], words[-1]['end']) if words else (0, 0)
    return [(round(s, 2), round(e, 2)) for s, e in zip(starts, ends) if s >= a and e <= b]


def audio_onset(video, noise='-40dB'):
    """First non-silent audio (s). Whisper often stamps the first word at 0.0, so the onset is measured."""
    log = subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-i', str(video), '-af',
                          f'silencedetect=n={noise}:d=0.03', '-f', 'null', '-'], capture_output=True, text=True).stderr
    m = re.search(r'silence_start: (-?[\d.]+)', log)
    if not m or float(m.group(1)) > 0.01:
        return 0.0
    e = re.search(r'silence_end: (-?[\d.]+)', log)
    return round(float(e.group(1)), 3) if e else None


def loop_diff(video):
    """Mean |RGB| difference (/255) of the last frame, and the best frame of the last 0.5 s, vs the first frame."""
    a = _frames(video, 30, 64, 114)
    first, tail = a[0].astype(np.int16), a[-15:].astype(np.int16)
    diffs = [float(np.abs(f - first).mean()) for f in tail]
    return dict(last=round(diffs[-1], 1), best_last_half_second=round(min(diffs), 1))


def words_from_asr(asr):
    asr = asr.get('asr', asr)
    return [dict(text=w.get('word', '').strip(), start=float(w['start']), end=float(w['end']))
            for s in asr.get('segments', []) for w in s.get('words', []) if w.get('word', '').strip()]


def measure(video, words):
    r = RULES
    st = setting_changes(video)
    ps = pauses(video, words)
    lp = loop_diff(video)
    first = audio_onset(video)
    checks = dict(
        setting=dict(mean_len=st['mean_len'], max_len=st['max_len'], per_min=st.get('per_min'), changes=st['n'],
                     ok=st['mean_len'] <= r['setting_mean_target'] * 1.2 and st['max_len'] <= r['setting_max']),
        first_word=dict(start_s=first, asr_first_word_s=round(words[0]['start'], 2) if words else None,
                        ok=first is not None and first <= r['first_word_max']),
        pauses=dict(count=len(ps), spans=ps[:10], ok=len(ps) <= r['pause_max_count']),
        loop=dict(**lp, ok=lp['last'] <= r['loop_diff_max']),
    )
    return dict(status='ADVISORY', report_only=True, review_state='DECIDED',
                evidence=dict(checks=checks, flagged=[k for k, v in checks.items() if not v['ok']], targets=r,
                              method='setting: HSV histogram L1 > 1.2 vs segment anchor, 4 fps, subtitle band masked '
                                     '(research data/setting.py); first word: audio onset (silencedetect -40dB); pauses: silencedetect -40dB >= 0.5 s inside speech; '
                                     'loop: 64 px RGB mean abs diff /255'))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    m = sub.add_parser('measure')
    m.add_argument('video')
    m.add_argument('--asr')
    t = sub.add_parser('title')
    t.add_argument('before')
    t.add_argument('keyword')
    t.add_argument('after', nargs='?', default='몇 년 나옴?')
    pr = sub.add_parser('pair', help='report-only title/thumbnail pair check')
    pr.add_argument('title')
    pr.add_argument('thumb_text')
    s = sub.add_parser('spec')
    s.add_argument('spec', nargs='?')
    a = ap.parse_args()
    if a.cmd == 'title':
        title = make_title(a.before, a.keyword, a.after)
        print(json.dumps(dict(title=title, issues=check_title(title)), ensure_ascii=False))
    elif a.cmd == 'pair':
        print(json.dumps(check_pair(a.title, a.thumb_text), ensure_ascii=False, indent=1))
    elif a.cmd == 'spec':
        spec = json.loads(Path(a.spec).read_text()) if a.spec else SPEC_TEMPLATE
        print(json.dumps(dict(issues=check_spec(spec)) if a.spec else spec, ensure_ascii=False, indent=1))
    else:
        words = words_from_asr(json.loads(Path(a.asr).read_text())) if a.asr else []
        print(json.dumps(measure(a.video, words), ensure_ascii=False, indent=1))


if __name__ == '__main__':
    sys.exit(main())
