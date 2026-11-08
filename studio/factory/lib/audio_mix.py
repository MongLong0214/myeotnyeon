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
"""Opt-in new-render mixer; adapted from templates/audio/{mix,dsp}.py.

Uses existing NumPy/SciPy and FFmpeg. PCM arrays are (channels, samples), 48 kHz.
--words accepts Supertonic's asr_master.json (Whisper segments/words, seconds).
Existing video/master files are never overwritten. Call before a NEW render:
python -m factory.lib.audio_mix --voice raw.wav --music bed.wav --words asr_master.json --out new_mix.wav
Per-take word lists may be joined with supertonic_words(audio_json, take_asrs).
"""
import argparse
import json
import math
from pathlib import Path
import subprocess
import tempfile
import numpy as np
from scipy import ndimage, signal
from .frame_qa import measure_audio

SR = 48000
TARGET_LUFS = -14.0
CEIL_DBTP = -1.0

def db_gain(db): return 10 ** (np.asarray(db) / 20)


def word_spans(data):
    """Global word timestamps in seconds; never treat sentence/frame timing as words."""
    if isinstance(data, dict):
        if 'segments' in data: rows = [w for s in data['segments'] for w in s.get('words', [])]
        elif 'words' in data: rows = data['words']
        else: raise ValueError('Expected words or Whisper segments; timing.json items are frame units')
    else: rows = data
    spans = []
    for w in rows:
        a, b = float(w.get('start', w.get('s', -1))), float(w.get('end', w.get('e', -1)))
        if not math.isfinite(a + b) or a < 0 or b <= a: raise ValueError('Invalid word timestamp')
        spans.append((a, b))
    if not spans: raise ValueError('No word timestamps supplied')
    return sorted(spans)


def supertonic_words(audio, take_asrs):
    """Join selected Supertonic take ASRs using fresh.py audio.json sample offsets.

    take_asrs maps item id to that selected take's Whisper JSON. Do not pass a
    master ASR here: master ASRs already contain global times and use word_spans.
    """
    words = []
    for item in audio['items']:
        offset = item['new_start_sample'] / SR
        for a, b in word_spans(take_asrs[item['id']]):
            words.append(dict(start=a + offset, end=b + offset))
    return words


def duck_db(words, samples, sr=SR, depth=-9., pre=.08, post=.12, attack=.07, release=.45):
    if samples < 1 or sr < 1 or attack <= 0 or release <= 0 or depth > 0:
        raise ValueError('Invalid ducking parameters')
    ctrl = 1000
    target = np.zeros(math.ceil(samples / sr * ctrl) + 2)
    merged = []
    for a, b in word_spans(words):
        if merged and a - merged[-1][1] < .3: merged[-1][1] = max(b, merged[-1][1])
        else: merged.append([a, b])
    for a, b in merged:
        lo, hi = max(0, int((a - pre) * ctrl)), min(len(target), math.ceil((b + post) * ctrl))
        target[lo:hi] = 1
    env = np.empty_like(target); e = 0.
    ka, kr = 1 - np.exp(-1 / (attack * ctrl)), 1 - np.exp(-1 / (release * ctrl))
    for i, t in enumerate(target):
        e += (t - e) * (ka if t > e else kr); env[i] = e
    return np.interp(np.arange(samples) / sr, np.arange(len(env)) / ctrl, env * depth)


def true_peak(x):
    peak = float(np.abs(signal.resample_poly(x, 4, 1, axis=-1)).max())
    return 20 * math.log10(peak) if peak else -math.inf


def limiter(x, ceil_db=CEIL_DBTP, sr=SR, look=.003, release=.08):
    """Linked stereo, 4x peak detection, lookahead reduction and smooth release.

    Recheck after gain modulation: interpolation may create fresh intersample peaks.
    """
    x = np.asarray(x, dtype=float)
    if x.ndim != 2 or x.shape[1] == 0 or not np.isfinite(x).all(): raise ValueError('Invalid PCM')
    if sr <= 0 or look < 0 or release <= 0: raise ValueError('Invalid limiter parameters')
    n = x.shape[1]
    up = np.abs(signal.resample_poly(x, 4, 1, axis=-1)).max(0)
    peaks = up[:4*n].reshape(n, 4).max(1)
    needed = np.minimum(1., db_gain(ceil_db - .05) / np.maximum(peaks, 1e-12))
    ahead = max(1, round(look * sr))
    needed = ndimage.minimum_filter1d(needed, 2 * ahead + 1, mode='nearest')
    gain = np.empty(n); g = 1.; kr = 1 - np.exp(-1 / (release * sr))
    for i, v in enumerate(needed):
        g = min(v, g + (1 - g) * kr); gain[i] = g
    y = x * gain
    excess = true_peak(y) - (ceil_db - .02)
    if excess > 0: y *= db_gain(-excess)
    return y


def read_pcm(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', str(path), '-map', '0:a:0',
                          '-ar', str(SR), '-ac', '2', '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    return np.frombuffer(raw, '<f4').reshape(-1, 2).T.astype(float)


def _write_pcm(path, x):
    subprocess.run(['ffmpeg', '-v', 'error', '-n', '-f', 'f32le', '-ar', str(SR), '-ac', '2',
                    '-i', '-', '-c:a', 'pcm_s24le', str(path)],
                   input=np.asarray(x.T, '<f4').tobytes(), capture_output=True, check=True)


def mix_new(voice, out, words, music=None, sfx=None, music_db=-18., sfx_db=0.):
    """Render a new WAV; target -14 LUFS (+/-0.2 LU), TP <= -1 dBTP.

    Output length follows voice (pad the voice to the new picture duration first).
    Reject longer stems rather than silently losing their tails. Impossible targets
    raise without publishing a master. No existing delivery is modified.
    """
    out = Path(out)
    if out.suffix.lower() != '.wav': raise ValueError('Output must be a new PCM WAV')
    if out.exists(): raise FileExistsError(out)
    spans = word_spans(words)
    v = read_pcm(voice); n = v.shape[1]
    if max(b for _, b in spans) > n / SR + .05: raise ValueError('Words exceed voice duration; use global master seconds')
    x = v.copy()
    for path, level, duck in ((music, music_db, True), (sfx, sfx_db, False)):
        if path is None: continue
        stem = read_pcm(path)
        if stem.shape[1] > n: raise ValueError('Stem exceeds voice duration')
        bed = np.zeros_like(v); bed[:, :stem.shape[1]] = stem
        gain = level + (duck_db([dict(start=a, end=b) for a, b in spans], n) if duck else 0)
        x += bed * db_gain(gain)
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=out.parent, prefix='.new_mix_') as tmp:
        raw = Path(tmp) / 'raw.wav'; _write_pcm(raw, x)
        initial = measure_audio(raw)
        if initial['integrated_lufs'] is None: raise ValueError('Silent mix cannot reach -14 LUFS')
        gain = TARGET_LUFS - initial['integrated_lufs']
        for attempt in range(6):
            candidate = Path(tmp) / f'limited_{attempt}.wav'
            y = limiter(x * db_gain(gain)); _write_pcm(candidate, y)
            measured = measure_audio(candidate)
            error = TARGET_LUFS - measured['integrated_lufs']
            if abs(error) <= .2 and measured['true_peak_dbtp'] <= CEIL_DBTP:
                # Exclusive publication also protects against concurrent lanes.
                with out.open('xb') as dest, candidate.open('rb') as source:
                    import shutil
                    shutil.copyfileobj(source, dest)
                return dict(output=str(out), samples=n, sample_rate=SR, words=len(spans), **measured)
            gain += error
        raise ValueError(f'Unable to meet loudness/peak target: {measured}')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for key in ('voice', 'out', 'words'): ap.add_argument('--' + key, type=Path, required=True)
    for key in ('music', 'sfx'): ap.add_argument('--' + key, type=Path)
    args = ap.parse_args()
    print(json.dumps(mix_new(args.voice, args.out, json.loads(args.words.read_text()), args.music, args.sfx), indent=2))

if __name__ == '__main__': main()
