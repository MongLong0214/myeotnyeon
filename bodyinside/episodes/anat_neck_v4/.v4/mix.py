"""Build the v4 Sohee mix from the approved narration, two new lines and existing SFX."""
import json
from pathlib import Path
import shutil
import subprocess

import numpy as np
from scipy.ndimage import uniform_filter1d
import soundfile as sf
from math import gcd
from scipy.signal import resample_poly

from cut import ROOT, STAGE, V3, load, save

SR = 48000
AUDIO = ROOT / 'audio'
AUDIO.mkdir(exist_ok=True)
episode = load(ROOT / 'episode.json')
old = V3 / 'audio'
parts_dir = AUDIO / 'parts'
parts_dir.mkdir(exist_ok=True)
parts = {}


def read(path):
    x, rate = sf.read(path, dtype='float32', always_2d=True)
    y = x.mean(1)
    factor = gcd(rate, SR)
    return y if rate == SR else resample_poly(y, SR//factor, rate//factor)


for item in episode['sfx_parts']:
    name = item['id']
    src = old / 'parts' / (name + '.wav')
    shutil.copyfile(src, parts_dir / src.name)
    y = read(src)
    spectrum = np.fft.rfft(y)
    hz = np.fft.rfftfreq(len(y), 1/SR)
    spectrum[hz < 120] *= .15
    spectrum[(hz >= 120) & (hz < 250)] *= .6
    spectrum[(hz >= 500) & (hz <= 3000)] *= item.get('mid_boost', 3.2)
    y = np.fft.irfft(spectrum, len(y))
    parts[name] = (y * item.get('norm', .8) / max(1e-9, np.max(np.abs(y)))).astype('float32')
old_report = load(old / 'sfx_report.json')
save(AUDIO / 'sfx_report.json', {name: old_report[name] for name in parts})

count = round(episode['duration'] * SR)
voice = np.zeros(count, 'float32')
fx = np.zeros(count, 'float32')
new = STAGE / 'audio' / 'cand'
disc = read(new / 'L1_c0_t0.wav')
first, second = round(3.73 * SR), round(7.51 * SR)
recordings = [
    read(old / 'approved' / 'narr_0.wav'),
    read(old / 'approved' / 'narr_1.wav'),
    read(new / 'L0_c0_t1.wav'),
    read(old / 'narr_4.wav'),
    disc[:first], disc[first:second], disc[second:],
    read(old / 'approved' / 'narr_6.wav'),
]
offsets = [.15, .15, .13, .10, .225, None, None, .095]
meta = []
for i, (line, take, delay) in enumerate(zip(episode['narration'], recordings, offsets)):
    beat = episode['beats'][line['beat']]
    start = round((beat['t0'] + delay) * SR) if delay is not None else stop
    stop = start + len(take)
    assert stop <= count and stop/SR <= beat['t1'] + .03, (i, stop/SR, beat['t1'])
    voice[start:stop] = take
    filename = f'narr_{i}.wav'
    sf.write(AUDIO / filename, take, SR)
    script = line.get('spoken', line['text'])
    syllables = sum('가' <= c <= '힣' for c in script)
    meta.append(dict(line=i, beat=line['beat'], text=script, start=start/SR, end=stop/SR,
                     rate=round(syllables*SR/len(take), 2), file=filename))
save(AUDIO / 'narration.json', meta)

bed = episode['sfx_bed']
ambience = np.resize(parts[bed['part']], count).copy()
fade = int(.5 * SR)
ambience[:fade] *= np.linspace(0, 1, fade)
ambience[-fade:] *= np.linspace(1, 0, fade)
x, y = zip(*bed['curve'])
fx += ambience * np.interp(np.arange(count)/SR, x, y)
for evt in episode['sfx']:
    start = round(evt['t'] * SR)
    sound = parts[evt['part']][:count - start]
    fx[start:start + len(sound)] += sound * evt['gain']
fx = np.tanh(1.8*fx) / np.tanh(1.8)
envelope = np.sqrt(np.maximum(0, uniform_filter1d(voice*voice, size=round(.02*SR))))
duck = uniform_filter1d((envelope > .01).astype('float32'), size=round(.25*SR))
mix = fx*(1-.92*duck) + 1.2*voice
mix = np.tanh(1.5*mix) / np.tanh(1.5)*.96
sf.write(AUDIO / 'sfx.wav', mix, SR)
sf.write(AUDIO / 'sfx_only.wav', fx, SR)


def ffmpeg(*options, **kwargs):
    return subprocess.run(['ffmpeg', '-hide_banner', '-nostats', '-y', *options], check=True, **kwargs)


limited = str(AUDIO / 'sfx_pre.wav')
ffmpeg('-v','error','-i',str(AUDIO/'sfx.wav'),'-af','alimiter=limit=0.35:attack=3:release=60:level=false',limited)
loudness = f"loudnorm=I={episode['lufs']}:TP=-2.0:LRA=11"
analysis = ffmpeg('-i', limited, '-af', loudness+':print_format=json','-f','null','-',capture_output=True,text=True).stderr
measured = json.loads(analysis[analysis.rfind('{'):analysis.rfind('}')+1])
for setting in ('I', 'TP', 'LRA', 'thresh'):
    loudness += f":measured_{setting}={measured['input_'+setting.lower()]}"
ffmpeg('-v','error','-i',limited,'-af',loudness+':linear=true,aresample=48000','-c:a','aac','-b:a','192k',str(AUDIO/'v4.m4a'))
