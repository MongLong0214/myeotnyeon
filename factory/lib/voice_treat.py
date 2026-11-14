"""Narration polish chain: the CLEAN stage of cinecode scripts/voice_treat.py (ported; ffmpeg only, offline).

  .venv/bin/python factory/lib/voice_treat.py IN.wav OUT.wav [--preset clean]

clean: high-pass 80 Hz, de-ess, -2 dB at 300 Hz, +2 dB presence at 3.2 kHz, gentle 2.5:1 compression, then the
same 0.89 limiter as the source. Output keeps the input sample rate and channels (24-bit WAV). Opt-in tool;
nothing calls it by default. Media/space/imprint presets and the LUFS re-target of the source are not ported.

Ported from cinecode - https://github.com/sarpstar/cinecode @67f9807, scripts/voice_treat.py (CLEAN chain).

MIT License

Copyright (c) 2026 Sarp Yıldız (@sarpstar)

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
import argparse
import subprocess
import sys
from pathlib import Path

PRESETS = dict(clean="highpass=f=80,deesser=i=0.35,equalizer=f=300:t=q:w=1:g=-2,equalizer=f=3200:t=q:w=1:g=2,"
                     "acompressor=threshold=-22dB:ratio=2.5:attack=8:release=150:makeup=3dB")
LIMIT = 'alimiter=limit=0.89:level=false'


def treat(in_wav, out_wav, preset='clean'):
    if preset not in PRESETS:
        raise ValueError(f'unknown preset {preset!r}; have {sorted(PRESETS)}')
    Path(out_wav).parent.mkdir(parents=True, exist_ok=True)
    p = subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', str(in_wav), '-af', f'{PRESETS[preset]},{LIMIT}',
                        '-c:a', 'pcm_s24le', str(out_wav)], capture_output=True, text=True)
    if p.returncode:
        raise RuntimeError('voice_treat: ' + p.stderr.strip()[-300:])
    return str(out_wav)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('in_wav')
    ap.add_argument('out_wav')
    ap.add_argument('--preset', default='clean', choices=sorted(PRESETS))
    a = ap.parse_args()
    print(treat(a.in_wav, a.out_wav, a.preset))
    sys.exit(0)
