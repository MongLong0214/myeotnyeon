#!/usr/bin/env python3
"""Structural checks for the v2 light cut (the v1.3 validator assumes the fixed 480 s grid).

Checks: cue frames contiguous; picture segments tile the timeline with no gap/overlap and every
plate exists with enough frames; overlays and subtitles inside the timeline; subtitles do not
overlap; every narration sentence has audio placed inside its cue; every claim id is defined in
the ledger with an archived source (or is a production note); master audio length = video length;
optional --media FILE: video duration/fps/size and audio loudness.
Prints PASS/FAIL lines and exits 1 on any FAIL.
"""
import json, pathlib, subprocess, sys

HERE = pathlib.Path(__file__).parent
PUB = HERE.parents[1] / 'production' / 'compositor' / 'public'
fails, notes = [], []


def check(ok, msg):
    (notes if ok else fails).append(msg)
    print(('PASS ' if ok else 'FAIL ') + msg)


def frames(path):
    r = subprocess.run(['ffprobe', '-v', 'error', '-select_streams', 'v', '-count_packets', '-show_entries', 'stream=nb_read_packets', '-of', 'csv=p=0', str(path)],
                       capture_output=True, text=True)
    return int(r.stdout.strip() or 0)


def main():
    script = json.load(open(HERE / 'script.json'))
    timing = json.load(open(HERE / 'timing.json'))
    render = json.load(open(PUB / 'ep001' / 'render.json'))
    ledger = json.load(open(HERE / 'ledger.json'))
    T = script['duration_frames']
    check(render['durationInFrames'] == T == timing['duration_frames'], f'duration consistent ({T} f = {T / 30:.1f} s)')
    cues = script['cues']
    check(cues[0]['in_frame'] == 0 and all(a['out_frame_exclusive'] == b['in_frame'] for a, b in zip(cues, cues[1:])) and cues[-1]['out_frame_exclusive'] == T,
          f'{len(cues)} cues contiguous')
    segs = sorted(render['segments'], key=lambda s: s['from'])
    tiled = segs[0]['from'] == 0 and all(a['from'] + a['dur'] == b['from'] for a, b in zip(segs, segs[1:])) and segs[-1]['from'] + segs[-1]['dur'] == T
    check(tiled, f'{len(segs)} picture segments tile the timeline')
    lens, bad = {}, []
    for s in segs:
        if s.get('ok') is False:
            bad.append(f"missing plate {s.get('label')} at {s['from']}"); continue
        if s.get('src'):
            n = lens.setdefault(s['src'], frames(PUB / s['src']))
            need = s.get('startFrom', 0) + s['dur'] * s.get('rate', 1)
            if need > n + 1:
                bad.append(f"{s['src']} needs {need:.0f} f, has {n}")
    check(not bad, 'all plates present with enough frames' + ('' if not bad else ': ' + '; '.join(bad[:6]) + (f' (+{len(bad) - 6})' if len(bad) > 6 else '')))
    check(all(0 <= o['from'] and o['from'] + o['dur'] <= T for o in render['overlays']), f"{len(render['overlays'])} overlays inside the timeline")
    subs = render['subtitles']
    check(all(0 <= s['from_'] < s['to'] <= T for s in subs) and all(a['to'] <= b['from_'] for a, b in zip(subs, subs[1:])), f'{len(subs)} subtitles ordered, non-overlapping')
    check(max(len(s['text'].split('\n')) for s in subs) <= 2, 'subtitles at most 2 lines')
    cue_of = {c['cue_id']: c for c in cues}
    na_ok = all(cue_of[i['cue']]['in_frame'] <= i['start'] < i['end'] <= cue_of[i['cue']]['out_frame_exclusive'] and (HERE / i['file']).exists() for i in timing['items'])
    check(na_ok, f"{len(timing['items'])} narration sentences have audio inside their cue")
    n_sent = sum(len(c['narration']) for c in cues)
    check(n_sent == len(timing['items']), f'every sentence synthesized ({n_sent})')
    claims, sources = ledger['claims'], ledger['sources']
    used = sorted({cid for c in cues for cid in c['claim_ids']})
    undefined = [c for c in used if c not in claims]
    check(not undefined, f'{len(used)} claim ids used, all defined' + (f' (undefined {undefined})' if undefined else ''))
    no_src = [c for c in used if c in claims and not claims[c][2] and claims[c][4] != 'UNKNOWN' and claims[c][0] not in ('meta', 'analysis')]
    check(not no_src, 'every factual claim has a source' + (f' (none: {no_src})' if no_src else ''))
    raw = HERE.parents[1] / 'research' / 'raw'
    unarchived = [sid for sid, v in sources.items() if not any((raw / f'{v[0]}.{e}').exists() for e in ('txt', 'html', 'pdf'))]
    check(not unarchived, f'{len(sources)} sources archived' + (f' (missing {unarchived})' if unarchived else ''))
    mix = PUB / 'ep001' / 'mix_master.wav'
    if mix.exists():
        r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', str(mix)], capture_output=True, text=True)
        d = float(r.stdout.strip())
        check(abs(d - T / 30) < 0.05, f'master audio {d:.3f} s matches video')
    else:
        check(False, 'master audio copied to compositor/public/ep001')
    if '--media' in sys.argv:
        f = pathlib.Path(sys.argv[sys.argv.index('--media') + 1])
        r = subprocess.run(['ffprobe', '-v', 'error', '-show_entries', 'stream=codec_type,width,height,r_frame_rate:format=duration', '-of', 'json', str(f)], capture_output=True, text=True)
        info = json.loads(r.stdout)
        v = next(s for s in info['streams'] if s['codec_type'] == 'video')
        dur = float(info['format']['duration'])
        check(v['width'] == 1920 and v['height'] == 1080 and v['r_frame_rate'] == '30/1', 'media 1920x1080 @ 30 fps')
        check(abs(dur - T / 30) < 0.1, f'media duration {dur:.2f} s')
        e = subprocess.run(['ffmpeg', '-hide_banner', '-i', str(f), '-af', 'ebur128=peak=true', '-f', 'null', '-'], capture_output=True, text=True).stderr
        tail = e[e.rindex('Summary:'):]
        lufs = float(tail.split('I:')[1].split('LUFS')[0]); peak = float(tail.split('Peak:')[1].split('dBFS')[0])
        check(-17.0 <= lufs <= -15.0 and peak <= -1.0, f'media loudness {lufs} LUFS, true peak {peak} dBFS')
    print(f"\n{'FAIL' if fails else 'PASS'}: {len(notes)} passed, {len(fails)} failed")
    sys.exit(1 if fails else 0)


if __name__ == '__main__':
    main()
