from math import gcd
from pathlib import Path
import json
import shutil
import subprocess

import numpy as np
from scipy.ndimage import uniform_filter1d
from scipy.signal import resample_poly
import soundfile as sf

from cut import STAGE, V3, load, write

SR = 48000
ep = load(STAGE/'episode.json')
audio_dir = STAGE/'audio'
source_dir = V3/'audio'
names = {event['part'] for event in ep['sfx']} | {ep['sfx_bed']['part']}


def read(path):
    y, rate = sf.read(path, dtype='float32', always_2d=True)
    y = y.mean(axis=1)
    divisor = gcd(rate, SR)
    return y if rate == SR else resample_poly(y, SR//divisor, rate//divisor)


parts = {}
for name in names:
    y = read(source_dir/'parts'/f'{name}.wav')
    config = next(item for item in ep['sfx_parts'] if item['id'] == name)
    spectrum = np.fft.rfft(y)
    hz = np.fft.rfftfreq(len(y), 1/SR)
    spectrum[hz < 120] *= .15
    spectrum[(hz >= 120) & (hz < 250)] *= .6
    spectrum[(hz >= 500) & (hz <= 3000)] *= config.get('mid_boost', 3.2)
    y = np.fft.irfft(spectrum, len(y))
    parts[name] = (y * config.get('norm', .8) / max(1e-9, np.max(np.abs(y)))).astype('float32')
report = load(source_dir/'sfx_report.json')
write(audio_dir/'sfx_report.json', {n: report[n] for n in sorted(names)})

count = round(ep['duration']*SR)
voice = np.zeros(count, 'float32')
for take in load(audio_dir/'narration.json'):
    y = read(audio_dir/take['file'])
    start = round(take['start']*SR)
    voice[start:start+len(y)] = y

bed = ep['sfx_bed']
fx = np.resize(parts[bed['part']], count)
x, y = zip(*bed['curve'])
fx *= np.interp(np.arange(count)/SR, x, y)
fade = SR//6
fx[:fade] *= np.linspace(0, 1, fade)
fx[-fade:] *= np.linspace(1, 0, fade)
for event in ep['sfx']:
    start = round(event['t']*SR)
    y = parts[event['part']][:count-start]
    fx[start:start+len(y)] += y*event['gain']
env = np.sqrt(np.maximum(0, uniform_filter1d(voice*voice, size=round(.02*SR))))
duck = uniform_filter1d((env > .01).astype('float32'), size=round(.22*SR))
mix = fx*(1-.92*duck) + 1.2*voice
mix = np.tanh(1.5*mix)/np.tanh(1.5)*.96
sf.write(audio_dir/'sfx.wav', mix, SR)
args = ['ffmpeg', '-hide_banner', '-nostats', '-y', '-i', str(audio_dir/'sfx.wav')]
loudnorm = 'loudnorm=I=-13.3:TP=-2:LRA=11'
log = subprocess.run(args + ['-af', loudnorm+':print_format=json', '-f', 'null', '-'],
                     capture_output=True, text=True, check=True).stderr
measured = json.loads(log[log.rfind('{'):log.rfind('}')+1])
for key in ('I', 'TP', 'LRA', 'thresh'):
    loudnorm += f":measured_{key}={measured['input_'+key.lower()]}"
subprocess.run(args + ['-v', 'error', '-af', loudnorm+':linear=true,aresample=48000',
                       '-c:a', 'aac', '-b:a', '128k', str(audio_dir/'mix.m4a')], check=True)
