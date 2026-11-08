#!/usr/bin/env python3
"""S001 Shorts: timing anchors for the webtoon scenes → compositor/public/s001/render.json.

Each cue gets its start/duration and named anchors (frames relative to the cue start) for the
moments the scenes react to: sentence starts and the instant a key word is spoken (character-
position estimate inside the synthesized sentence).
"""
import json, pathlib, re, shutil

HERE = pathlib.Path(__file__).parent
OUT = HERE.parents[1] / 'production' / 'compositor' / 'public' / 's001'
script = json.load(open(HERE / 'script.json'))
timing = json.load(open(HERE / 'timing.json'))
SENT = {i['id']: i for i in timing['items']}

WORDS = {   # cue: {anchor: (sentence index, word)}
    'C2': {'back': (2, '차를'), 'again': (2, '다시'), 'hit': (2, '들이받')},
    'C4': {'b1': (2, '부주의한'), 'b2': (2, '저 사람')},
    'C5': {'court': (1, '법원은')},
    'C7': {'jing': (1, '징역'), 'yu': (1, '집행유예')},
    'C8': {'w1': (1, '반성은'), 'w2': (1, '초범'), 'w3': (1, '들이받은'), 'w4': (1, '신고가')},
}


def W(sid, word):
    it = SENT[sid]
    t = it['text']; i = t.index(word)
    w = lambda s: len(re.sub(r'\s', '', s))
    return it['start'] + round((it['end'] - it['start']) * w(t[:i]) / max(1, w(t)))


def main():
    cues = []
    for c in script['cues']:
        cid, c0 = c['cue_id'], c['in_frame']
        a = {}
        for k in range(len(c['narration'])):
            it = SENT[f'{cid}_{k + 1}']
            a[f's{k + 1}'] = it['start'] - c0; a[f'e{k + 1}'] = it['end'] - c0
        for name, (k, word) in WORDS.get(cid, {}).items():
            a[name] = W(f'{cid}_{k}', word) - c0
        cues.append(dict(id=cid, scene=c['act'], **{'from': c0, 'dur': c['duration_frames']}, a=a))
    OUT.mkdir(parents=True, exist_ok=True)
    mix = HERE / 'audio' / 'mix_master.wav'
    if mix.exists():
        shutil.copy(mix, OUT / 'mix_master.wav')
    doc = dict(fps=30, durationInFrames=script['duration_frames'], cues=cues,
               subtitles=[dict(from_=s['from_'], to=s['to'], text=s['text']) for s in timing['subtitles']],
               audio='s001/mix_master.wav' if (OUT / 'mix_master.wav').exists() else None)
    json.dump(doc, open(OUT / 'render.json', 'w'), ensure_ascii=False, indent=1)
    json.dump(dict(cues={c['id']: c for c in cues}, total=script['duration_frames']), open(HERE / 'anchors.json', 'w'), ensure_ascii=False, indent=1)
    print('cues', len(cues), 'frames', doc['durationInFrames'], 'audio', doc['audio'])
    for c in cues:
        print(c['id'], c['from'], c['dur'], c['a'])


if __name__ == '__main__':
    main()
