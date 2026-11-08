#!/usr/bin/env python3
"""S001 Shorts (vertical): based on EP001 v2 layout.

v2 (light cut): place cues back to back from the measured narration and build subtitles.

Each cue starts where the previous one ends; its length is lead + sentences (with a short
gap between them) + the cue's pad from script_text.json. Writes script.json (cues with
frames), timing.json and subtitles.ko.srt / .vtt. No fixed 480 s grid any more (owner
direction 2026-10-26: ~5 min, never padded).
"""
import json, pathlib, re

HERE = pathlib.Path(__file__).parent
FPS = 30
LEAD = {'C1': 4}      # Shorts: speak almost immediately
DEFAULT_LEAD = 3
SENT_GAP = 5           # Shorts: tight
MIN_CUE = {}
# Shorts captions: hand-placed breaks so a phrase is never split mid-word ("한 / 번 더")
CAPTION_SPLIT = {'C2_1': ['일주일마다\n전국 모텔을 옮겨 다니며', '대포폰 136대와\n유심칩 395개를 썼습니다.'], 'C3_1': ['피해자는 39명이고', '피해액은\n약 11억 원이었어요.'], 'C4_1': ['벌금, 집행유예, 실형 중\n무엇이었을까요?'], 'C4_2': ['판사는 단순 현금 수거책보다', '가담 정도가\n무겁다고 봤습니다.'], 'C4_3': ['피해 회복을 위한\n노력도 없었고요.'], 'C4_4': ['다만 범행을 인정했고', '벌금형보다 무거운\n전과는 없었죠.'], 'C5_1': ['정답은 실형,\n징역 10년입니다.'], 'C5_2': ['검찰 구형 5년의\n두 배였어요.'], 'C1_1': ['해외 피싱 조직의 전화가', '국내 010 번호로\n뜨게 만든 20대 두 명.']}


def chunks(text, maxline=11):
    """Split a sentence into subtitle chunks of ≤2 lines."""
    parts = [p.strip() for p in re.split(r'(?<=[,.?])\s+', text) if p.strip()]
    out = []
    for p in parts:
        if len(p) <= maxline * 2 - 2:
            out.append(p)
        else:
            words = p.split(' ')
            cur = ''
            for w in words:
                if len(cur) + len(w) + 1 > maxline * 2 - 4 and cur:
                    out.append(cur.strip()); cur = w
                else:
                    cur = (cur + ' ' + w).strip()
            if cur:
                out.append(cur)
    # merge very short tails into previous
    merged = []
    for c in out:
        if merged and len(c) < 7 and len(merged[-1]) + len(c) < maxline * 2:
            merged[-1] = merged[-1] + ' ' + c
        else:
            merged.append(c)
    return [wrap(c, maxline) for c in merged]


def wrap(c, maxline):
    if len(c) <= maxline:
        return c
    mid = len(c) // 2
    sp = [i for i, ch in enumerate(c) if ch == ' ']
    if not sp:
        return c
    i = min(sp, key=lambda k: abs(k - mid))
    return c[:i] + '\n' + c[i + 1:]


_chunks = chunks
NOBREAK_AFTER = ('약', '징역', '집행유예', '다른', '이미')


def chunks(text, maxline=11):
    glued = re.sub(r'(?<!\S)(' + '|'.join(NOBREAK_AFTER) + r') ', lambda m: m.group(1) + '\u00a0', text)
    return [c.replace('\u00a0', ' ') for c in _chunks(glued, maxline)]


def weight(s):
    return len(re.sub(r'\s', '', s)) + 3 * len(re.findall(r'[,.?]', s))


def tc(f):
    s = f / FPS
    return f"{int(s//3600):02d}:{int(s%3600//60):02d}:{int(s%60):02d},{int(round((s - int(s)) * 1000)):03d}"


def main():
    script = json.load(open(HERE / 'script_text.json'))
    idx = {x['id']: x for x in json.load(open(HERE / 'audio/na/index.json'))['items']}
    cur = 0
    cues, items, subs = [], [], []
    for c in script['cues']:
        cin = cur
        t = cin + LEAD.get(c['cue_id'], DEFAULT_LEAD) if c['narration'] else cin
        for i, s in enumerate(c['narration']):
            it = idx[f"{c['cue_id']}_{i+1}"]
            assert it['text'] == s, f"stale audio for {it['id']}"
            d = round(it['dur'] * FPS)
            start = t if i == 0 else t + SENT_GAP
            end = start + d
            items.append(dict(id=it['id'], cue=c['cue_id'], act=c['act'], start=start, end=end, file=it['file'], text=s))
            ch = CAPTION_SPLIT.get(it['id']) or chunks(s)
            assert ''.join(ch).replace('\n', ' ').replace('  ', ' ').replace(' ', '') == s.replace(' ', ''), f'caption split mismatch {it["id"]}'
            tot = sum(weight(x) for x in ch)
            acc = start
            for k, x in enumerate(ch):
                dd = round(d * weight(x) / tot) if k < len(ch) - 1 else end - acc
                subs.append(dict(from_=acc, to=acc + dd, text=x, cue=c['cue_id']))
                acc += dd
            t = end
        cout = max(t + round(c['pad_s'] * FPS), cin + MIN_CUE.get(c['cue_id'], 0))
        cues.append(dict(c, in_frame=cin, duration_frames=cout - cin, out_frame_exclusive=cout, required_claim_ids=c['claim_ids']))
        cur = cout
    for a, b in zip(subs, subs[1:]):
        if 0 < b['from_'] - a['to'] <= 8:
            a['to'] = b['from_']
    total = cur
    json.dump(dict(script, cues=cues, duration_frames=total, fps=FPS), open(HERE / 'script.json', 'w'), ensure_ascii=False, indent=1)
    json.dump(dict(fps=FPS, duration_frames=total, items=items, subtitles=[dict(from_=s['from_'], to=s['to'], text=s['text'], cue=s['cue']) for s in subs]),
              open(HERE / 'timing.json', 'w'), ensure_ascii=False, indent=1)
    with open(HERE / 'subtitles.ko.srt', 'w') as f:
        for i, s in enumerate(subs, 1):
            f.write(f"{i}\n{tc(s['from_'])} --> {tc(s['to'])}\n{s['text']}\n\n")
    with open(HERE / 'subtitles.ko.vtt', 'w') as f:
        f.write('WEBVTT\nKind: captions\nLanguage: ko\n\n')
        for i, s in enumerate(subs, 1):
            f.write(f"{tc(s['from_']).replace(',', '.')} --> {tc(s['to']).replace(',', '.')}\n{s['text']}\n\n")
    for c in cues:
        print(f"{c['cue_id']} {c['act']} in {c['in_frame']:5d} ({c['in_frame']/FPS:6.1f}s) dur {c['duration_frames']/FPS:5.1f}s")
    nar = sum(i['end'] - i['start'] for i in items) / FPS
    print('TOTAL', total, 'frames =', round(total / FPS, 1), 's | narration', round(nar, 1), 's | subtitles', len(subs),
          '| max chunk chars', max(len(s['text'].replace('\n', '')) for s in subs))


if __name__ == '__main__':
    main()
