"""Peak-synced SFX placement: each cue's loudest sample lands on its `at` second (cinecode sound.md peak-sync rule).

  .venv/bin/python factory/lib/sfx_bank.py cues.json DURATION_S OUT.wav

A cue is {id: earshot bank id ('cut_hit/punch', 'whoosh_fast/crisp') | file: local audio path, at: seconds of the
PEAK, gain_db: 0, apex/dur: optional earshot shape}. Earshot (github.com/Leonxlnx/earshot, MIT © 2026 Leon Lin) is
called as a subprocess from a local clone (EARSHOT_SRC, default research/x-3three_ai/src); none of its code is in
this tree. Its JSON `peak_s` gives the peak (earshot's definition: centre of the loudest 5 ms RMS window, 1 ms hop);
for files the peak is argmax |x|. Returns one report row per cue with the peak re-measured in the placed track by
the same definition the cue used (peak_method). Opt-in tool; nothing calls it by default.
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import soundfile as sf

ROOT = Path(__file__).resolve().parents[2]
EARSHOT_DEFAULT = ROOT / 'research/x-3three_ai/src'


def whoosh_before_cut(cut_s, fps=30, frames=2):
    """A whoosh peaks two frames before the cut it leads into."""
    return cut_s - frames / fps


def envelope_peak(x, sr):
    """Centre of the loudest 5 ms RMS window, 1 ms hop (the definition earshot's peak_s uses)."""
    m = np.abs(x).max(axis=1) if x.ndim == 2 else np.abs(x)
    w, h = max(1, sr // 200), max(1, sr // 1000)
    c = np.concatenate([[0.0], np.cumsum(m.astype(np.float64) ** 2)])
    st = np.arange(0, max(1, len(m) - w + 1), h)
    e = c[np.minimum(st + w, len(m))] - c[st]
    return (st[int(np.argmax(e))] + w / 2) / sr


def _argmax_peak(x, sr):
    return int(np.argmax(np.abs(x).max(axis=1))) / sr


def _decode(path, sr):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-f', 'f32le', '-ac', '2', '-ar', str(sr), '-'],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype='<f4').reshape(-1, 2).copy()


def _earshot(cue, sr, tmp):
    src = Path(os.environ.get('EARSHOT_SRC', EARSHOT_DEFAULT))
    if not (src / 'earshot').is_dir():
        raise FileNotFoundError(f'earshot clone not found at {src} (set EARSHOT_SRC to the clone holding earshot/)')
    out = Path(tmp) / (cue['id'].replace('/', '_') + '.wav')
    cmd = [sys.executable, '-m', 'earshot', 'sfx', 'render', cue['id'], '-o', str(out), '--json', '--sr', str(sr)]
    for k in ('apex', 'dur', 'seed'):
        if cue.get(k) is not None:
            cmd += [f'--{k}', str(cue[k])]
    p = subprocess.run(cmd, capture_output=True, text=True, env=dict(os.environ, PYTHONPATH=str(src)))
    if p.returncode:
        raise RuntimeError(f"earshot {cue['id']}: " + (p.stderr or p.stdout).strip()[-300:])
    meta = json.loads(p.stdout)['meta']
    return _decode(out, sr), float(meta['peak_s'])


def place(cues, duration_s, out_wav, sr=48000):
    n = int(round(duration_s * sr))
    mix, report = np.zeros((n, 2), dtype=np.float64), []
    with tempfile.TemporaryDirectory() as tmp:
        for cue in cues:
            if cue.get('id'):
                (clip, peak_s), method, measure = _earshot(cue, sr, tmp), 'earshot_5ms_rms', envelope_peak
            else:
                clip, method, measure = _decode(cue['file'], sr), 'argmax_abs', _argmax_peak
                peak_s = measure(clip, sr)
            clip = clip * 10 ** (cue.get('gain_db', 0) / 20)
            start = int(round(cue['at'] * sr)) - int(round(peak_s * sr))
            head = max(0, -start)
            seg = clip[head:max(head, min(len(clip), n - start))]
            track = np.zeros_like(mix)
            track[start + head:start + head + len(seg)] = seg
            mix += track
            measured = measure(track, sr) if len(seg) else None
            report.append(dict(cue=cue.get('id') or str(cue['file']), at=cue['at'], source_peak_s=round(peak_s, 5), peak_method=method,
                               measured_peak_s=None if measured is None else float(measured), error_ms=None if measured is None else round(float(measured - cue['at']) * 1000, 3),
                               trimmed_head=head > 0))
    Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
    sf.write(str(out_wav), mix.astype(np.float32), sr, subtype='PCM_24')
    return report


if __name__ == '__main__':
    cues = json.loads(Path(sys.argv[1]).read_text())
    print(json.dumps(place(cues, float(sys.argv[2]), sys.argv[3]), indent=1))
