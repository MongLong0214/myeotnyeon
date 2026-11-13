"""Waveform / spectrum pictures and loudness numbers for one audio or video file (xilo idea, MIT; written anew).

  .venv/bin/python factory/lib/audio_evidence.py FILE OUT_DIR [--start S] [--end S]

Writes OUT_DIR/waveform.png (ffmpeg showwavespic), OUT_DIR/spectrum.png (showspectrumpic) and
OUT_DIR/audio_evidence.json (ebur128 integrated LUFS, true peak dBTP). Evidence only; nothing is judged.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


def _span(start, end):
    out = ['-ss', str(start)] if start is not None else []
    return out + (['-t', str(end - (start or 0))] if end is not None else [])


def _ff(src, start, end, *rest):
    return subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-y', *_span(start, end), '-i', str(src), *rest],
                          capture_output=True, text=True)


def loudness(src, start=None, end=None):
    err = _ff(src, start, end, '-vn', '-af', 'ebur128=peak=true', '-f', 'null', '-').stderr
    summary = err[err.rfind('Summary:'):] if 'Summary:' in err else err
    i = re.search(r'I:\s+(-?[\d.]+|-inf) LUFS', summary)
    tp = re.search(r'Peak:\s+(-?[\d.]+|-inf) dBFS', summary)
    num = lambda m: (float(m.group(1)) if m and m.group(1) != '-inf' else None)
    return dict(integrated_lufs=num(i), true_peak_dbtp=num(tp))


def render(audio_or_video, out_dir, start=None, end=None):
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    wave, spec = out / 'waveform.png', out / 'spectrum.png'
    for png, graph in ((wave, 'showwavespic=s=1600x300:split_channels=1'), (spec, 'showspectrumpic=s=1200x500:legend=1')):
        p = _ff(audio_or_video, start, end, '-vn', '-filter_complex', f'[0:a]{graph}', '-frames:v', '1', str(png))
        if p.returncode or not png.exists():
            raise RuntimeError(f'ffmpeg {graph.split("=")[0]}: ' + p.stderr.strip()[-300:])
    nums = dict(source=str(Path(audio_or_video).resolve()), start=start, end=end, **loudness(audio_or_video, start, end))
    (out / 'audio_evidence.json').write_text(json.dumps(nums, indent=1) + '\n')
    return dict(waveform=str(wave), spectrum=str(spec), json=str(out / 'audio_evidence.json'), **nums)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('file')
    ap.add_argument('out_dir')
    ap.add_argument('--start', type=float)
    ap.add_argument('--end', type=float)
    a = ap.parse_args()
    print(json.dumps(render(a.file, a.out_dir, a.start, a.end), indent=1))
    return 0


if __name__ == '__main__':
    sys.exit(main())
