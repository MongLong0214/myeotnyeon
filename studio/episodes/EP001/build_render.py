#!/usr/bin/env python3
"""Assemble compositor input (render.json) from script.json + timing.json.

Plates: each cue gets a video segment (shot, startFrom) or a still frame extracted from a
rendered plate (slow push applied in the compositor). Stills are pulled with ffmpeg so no
extra 3D renders are needed.
"""
import json, pathlib, subprocess, shutil

HERE = pathlib.Path(__file__).parent
PUB = HERE.parents[1] / 'production' / 'compositor' / 'public'
PLATES = PUB / 'plates'
OUT = PUB / 'ep001'

# cue → plate spec. kind 'video': (shot, startFrom, dim, blur); kind 'still': (shot, frame, dim, zoom)
PLATE = {
    'Q01': ('video', 'SH01', 0, 0.0), 'Q02': ('video', 'SH02', 0, 0.0), 'Q03': ('video', 'SH03', 0, 0.5),
    'Q04': ('video', 'SH04', 0, 0.0), 'Q05': ('video', 'SH05', 0, 0.0),
    'Q06': ('video', 'SH06', 0, 0.0), 'Q07': ('video', 'SH06', 300, 0.15), 'Q08': ('video', 'SH07', 0, 0.35),
    'Q09': ('video', 'SH08', 0, 0.0), 'Q10': ('video', 'SH09', 0, 0.0), 'Q11': ('video', 'SH10', 0, 0.1),
    'Q12': ('video', 'SH11', 0, 0.0), 'Q13': ('still', 'SH07', 299, 0.62),
    'Q14': ('video', 'SH13', 0, 0.2), 'Q15': ('video', 'SH13', 360, 0.55), 'Q16': ('video', 'SH13', 720, 0.55),
    'Q17': ('video', 'SH14', 0, 0.3), 'Q18': ('video', 'SH14', 450, 0.55),
    'Q19': ('video', 'SH15', 0, 0.25), 'Q20': ('still', 'SH15', 419, 0.45), 'Q21': ('still', 'SH10', 300, 0.45),
    'Q22': ('video', 'SH17', 0, 0.2), 'Q23': ('video', 'SH18', 0, 0.5),
    'Q24': ('video', 'SH19', 0, 0.5), 'Q25': ('video', 'SH19', 360, 0.55), 'Q26': ('video', 'SH19', 720, 0.55),
    'Q27': ('still', 'SH18', 419, 0.35), 'Q28': ('still', 'SH18', 419, 0.6),
    'Q29': ('video', 'SH21', 0, 0.55), 'Q30': ('video', 'SH21', 360, 0.6), 'Q31': ('video', 'SH21', 720, 0.6),
    'Q32': ('video', 'SH22', 0, 0.35), 'Q33': ('still', 'SH22', 449, 0.45),
    'Q34': ('video', 'SH23', 0, 0.55), 'Q35': ('video', 'SH23', 450, 0.6), 'Q36': ('video', 'SH23', 900, 0.6),
    'Q37': ('still', 'SH03', 239, 0.6), 'Q38': ('still', 'SH03', 239, 0.65),
    'Q39': None, 'Q40': None,
}


def extract_still(shot, frame):
    OUT.mkdir(parents=True, exist_ok=True)
    dst = OUT / f'still_{shot}_{frame}.png'
    src = PLATES / f'{shot}.mp4'
    if not dst.exists() and src.exists():
        subprocess.run(['ffmpeg', '-hide_banner', '-loglevel', 'error', '-y', '-i', str(src), '-vf', f'select=eq(n\\,{frame})', '-frames:v', '1', str(dst)], check=True)
    return f'ep001/{dst.name}' if dst.exists() else None


def main():
    script = json.load(open(HERE / 'script.json'))
    timing = json.load(open(HERE / 'timing.json'))
    cues, missing = [], []
    for c in script['cues']:
        spec = PLATE[c['cue_id']]
        plate = None
        if spec:
            kind, shot, a, dim = spec
            if kind == 'video':
                ok = (PLATES / f'{shot}.mp4').exists()
                plate = dict(kind='video', src=f'plates/{shot}.mp4', startFrom=a, dim=dim, ok=ok)
            else:
                src = extract_still(shot, a)
                plate = dict(kind='still', src=src, dim=dim, ok=src is not None)
            if not plate['ok']:
                missing.append((c['cue_id'], shot))
        cues.append(dict(cue_id=c['cue_id'], act=c['act'], from_=c['in_frame'], dur=c['duration_frames'], plate=plate, hud=c['hud'], gfx=c['gfx']))
    OUT.mkdir(parents=True, exist_ok=True)
    tb = extract_still('SH02', 160)
    if tb:
        shutil.copy(PUB / tb, OUT / 'thumb_bg.png')
    mix = HERE / 'audio' / 'mix_master.wav'
    if mix.exists():
        shutil.copy(mix, OUT / 'mix_master.wav')
    doc = dict(fps=30, durationInFrames=14400, hud_case=script['hud_case'], cues=cues,
               subtitles=[dict(from_=s['from_'], to=s['to'], text=s['text']) for s in timing['subtitles']],
               audio='ep001/mix_master.wav' if (OUT / 'mix_master.wav').exists() else None)
    json.dump(doc, open(OUT / 'render.json', 'w'), ensure_ascii=False, indent=1)
    print('cues', len(cues), 'subs', len(doc['subtitles']), 'audio', doc['audio'], 'missing plates', missing)


if __name__ == '__main__':
    main()
