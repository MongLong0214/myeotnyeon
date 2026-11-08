# MIT License
#
# Copyright (c) 2026 Mr omi
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
# OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR
# IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""Advisory frame QA adapted from claude-animated-shorts/templates/scripts/short_qa.py.

python -m factory.lib.frame_qa VIDEO OUT [--metadata shots.json]
Frame ranges are half-open [a,b); shots accept a/b, from/dur, or start_s/end_s.
Only transitions/white spikes are excused by planned cuts/flashes; explicit
holds excuse frozen spans. Detected pops are candidates, not proof of corruption.
"""
import argparse
from fractions import Fraction
import json
from pathlib import Path
import subprocess
import numpy as np
from PIL import Image, ImageDraw


def _run(args):
    return subprocess.run(list(map(str, args)), capture_output=True, check=True)


def measure_audio(path):
    """FFmpeg BS.1770 integrated loudness and oversampled true peak; None for silence."""
    p = _run(['ffmpeg', '-hide_banner', '-nostats', '-i', path, '-map', '0:a:0',
              '-af', 'loudnorm=I=-14:TP=-1:LRA=11:print_format=json', '-f', 'null', '-'])
    log = p.stderr.decode()
    data = json.loads(log[log.rindex('{'):log.rindex('}') + 1])
    def finite(key):
        v = float(data[key])
        return v if np.isfinite(v) else None
    return dict(integrated_lufs=finite('input_i'), true_peak_dbtp=finite('input_tp'),
                lra_lu=finite('input_lra'))


def shot_ranges(metadata, fps):
    rows = metadata if isinstance(metadata, list) else metadata.get('shots', metadata.get('cues', []))
    out = []
    for i, s in enumerate(rows):
        def numeric(keys, fallback):
            return next((s[k] for k in keys if isinstance(s.get(k), (int, float))), fallback)
        # Our cue.a is an animation-anchor DICT, not the original script's frame a.
        a = s['start_s'] * fps if 'start_s' in s else numeric(('a', 'from', 'start'), 0)
        b = s['end_s'] * fps if 'end_s' in s else numeric(('b', 'to', 'end'), a + s.get('dur', 0))
        out.append(dict(id=s.get('id', i), a=round(a), b=round(b)))
    return out


def exclusions(metadata, fps):
    m = metadata if isinstance(metadata, dict) else {}
    planned, holds = set(), set()
    for s in shot_ranges(metadata, fps):
        planned.update((s['a'] - 1, s['a'], s['a'] + 1))
    for a, b in m.get('planned', []) + m.get('xfade', []) + ([m['flash']] if 'flash' in m else []):
        planned.update(range(a - 1, b + 1))
    for a, b in m.get('holds', []):
        holds.update(range(a, b))
    return planned, holds


def classify(stats, diff, planned=(), holds=()):
    planned, holds = set(planned), set(holds)
    med = np.array([np.median(diff[max(0, i - 8):i + 9]) for i in range(len(diff))])
    pops = [i + 1 for i, d in enumerate(diff) if d > 3 * med[i] + 1 and i + 1 not in planned]
    frozen, start = [], None
    # diff[i] joins frame i to i+1. Include EOF and report half-open frame spans.
    for i in range(len(diff) + 1):
        still = i < len(diff) and diff[i] < .02 and i not in holds and i + 1 not in holds
        if still:
            if start is None: start = i
        elif start is not None:
            if i - start >= 12: frozen.append([start, i + 1])
            start = None
    return dict(black=[i for i, v in enumerate(stats['mean']) if v < .04],
                white=[i for i, v in enumerate(stats['mean']) if v > .93 and i not in planned],
                frozen=frozen, pops=pops)


def analyze(video, out, metadata=None, contact_sheets=True):
    video, out = Path(video).resolve(), Path(out)
    out.mkdir(parents=True, exist_ok=True)
    metadata = metadata or {}
    probe = json.loads(_run(['ffprobe', '-v', 'error', '-show_streams', '-show_format', '-of', 'json', video]).stdout)
    v = next(s for s in probe['streams'] if s['codec_type'] == 'video')
    fps = float(Fraction(v['avg_frame_rate']))
    w, h = 180, max(1, round(180 * v['height'] / v['width']))
    size = w * h * 3
    stats = {k: [] for k in ('mean', 'std', 'p2', 'p98', 'sat')}
    diff, sheets, prev, n = [], [], None, 0
    # Stream frames: memory does not scale with clip length (unlike the original).
    import tempfile
    with tempfile.TemporaryFile() as err:
        p = subprocess.Popen(['ffmpeg', '-v', 'error', '-i', str(video), '-map', '0:v:0',
                              '-vf', f'scale={w}:{h}:flags=area', '-fps_mode', 'passthrough',
                              '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE, stderr=err)
        try:
            while True:
                raw = p.stdout.read(size)
                if not raw: break
                if len(raw) != size: raise ValueError('Truncated decoded frame')
                f = np.frombuffer(raw, np.uint8).reshape(h, w, 3)
                rgb = f.astype(np.float32) / 255
                lum = rgb @ np.array([.2126, .7152, .0722], np.float32)
                mx, mn = rgb.max(-1), rgb.min(-1)
                vals = (lum.mean(), lum.std(), np.percentile(lum, 2), np.percentile(lum, 98),
                        np.where(mx > .06, (mx - mn) / np.maximum(mx, 1e-6), 0).mean())
                for key, val in zip(stats, vals): stats[key].append(float(val))
                if prev is not None: diff.append(float(np.abs(f.astype(np.int16) - prev).mean()))
                prev = f.astype(np.int16)
                if contact_sheets:
                    cw, ch = 108, max(1, round(108 * h / w))
                    if n % 60 == 0: sheet = Image.new('RGB', (cw * 10, ch * 6), 'black')
                    x, y = (n % 10) * cw, ((n % 60) // 10) * ch
                    sheet.paste(Image.fromarray(f).resize((cw, ch)), (x, y))
                    d = ImageDraw.Draw(sheet); d.rectangle((x, y, x + 48, y + 13), fill='black')
                    d.text((x + 2, y + 1), str(n), fill='yellow')
                    if n % 60 == 59:
                        name = f'sheet_{n - 59:05d}.jpg'; sheet.save(out / name, quality=85); sheets.append(name)
                n += 1
            if p.wait():
                err.seek(0); raise RuntimeError(err.read().decode()[-2000:])
        finally:
            p.stdout.close()
            if p.poll() is None: p.kill(); p.wait()
    if not n: raise ValueError('No video frames decoded')
    if contact_sheets and n % 60:
        name = f'sheet_{n - n % 60:05d}.jpg'; sheet.save(out / name, quality=85); sheets.append(name)
    planned, holds = exclusions(metadata, fps)
    findings = classify(stats, np.array(diff), planned, holds)
    audio = measure_audio(video) if any(s['codec_type'] == 'audio' for s in probe['streams']) else None
    shots = []
    for s in shot_ranges(metadata, fps) or [dict(id=0, a=0, b=n)]:
        a, b = max(0, s['a']), min(n, s['b'])
        if a < b: shots.append(dict(s, medians={k: float(np.median(vv[a:b])) for k, vv in stats.items()}))
    report = dict(video=str(video), advisory=True, fps=fps, frames=n, width=v['width'], height=v['height'],
                  codec=v['codec_name'], audio=audio, findings=findings, shots=shots, sheets=sheets,
                  motion_mean=float(np.mean(diff)) if diff else 0,
                  held_transitions=sum(d < .3 for d in diff),
                  limitations='Candidates require visual review; real-time playback not reviewed. No automatic pass/fail.')
    np.savez_compressed(out / 'perframe.npz', diff=diff, **stats)
    (out / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
    return report


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('video'); ap.add_argument('out'); ap.add_argument('--metadata', type=Path)
    args = ap.parse_args()
    r = analyze(args.video, args.out, json.loads(args.metadata.read_text()) if args.metadata else {})
    print(json.dumps({k: r[k] for k in ('frames', 'fps', 'audio', 'findings')}, indent=2))

if __name__ == '__main__': main()
