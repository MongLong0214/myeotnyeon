"""Conform listen-checked Earshot parts to the picture and add the original narration."""
import json
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy.signal import butter, resample_poly, sosfilt

ROOT = Path(__file__).resolve().parent
AUDIO = ROOT / 'audio'
RATE = 48_000


def conform(x, length, speed, start, repeat):
    count = round(length*RATE)
    available = np.asarray(x[round(start*RATE):], dtype=np.float64)
    denominator = round(speed*100)
    scaled = resample_poly(available, 100, denominator)
    if repeat and len(scaled) < count:
        # Overlap the steady middle of the take. Keep any drill attack once.
        loop = scaled[round(.12*len(scaled)):round(.85*len(scaled))]
        fade = min(round(.055*RATE),len(loop)//4)
        weight = np.linspace(0,1,fade)
        while len(scaled)<count:
            blend=scaled[-fade:]*(1-weight)+loop[:fade]*weight
            scaled=np.concatenate((scaled[:-fade],blend,loop[fade:]))
    if len(scaled)<count:
        scaled=np.pad(scaled,(0,count-len(scaled)))
    scaled=scaled[:count].copy()
    fade=min(round((.055 if repeat else .006)*RATE), count//4)
    scaled[:fade]*=np.linspace(0,1,fade)
    tail=min(round((.13 if repeat else .035)*RATE),count//3)
    scaled[-tail:]*=np.linspace(1,0,tail)
    return scaled


def main():
    spec=json.loads((ROOT/'episode.json').read_text())
    report=json.loads((AUDIO/'sfx_report.json').read_text())
    parts={}
    for p in spec['sfx_parts']:
        name=p['id']
        if not report[name]['pass']:
            raise ValueError(f'Earshot listen check failed for {name}')
        x,sr=sf.read(AUDIO/'parts'/f'{name}.wav',always_2d=True)
        if sr!=RATE:
            raise ValueError(f'Unexpected sample rate for {name}')
        x=x.mean(1)
        lo,hi={'bur':(900,11500),'root_bur':(900,11500),'saline':(1050,10500),
               'aspiration':(310,4250),'fracture':(330,8500),'knot':(450,7200),
               'liquid':(230,6700),'tissue':(270,6300)}[name]
        x=sosfilt(butter(2,(lo,hi),fs=RATE,btype='bandpass',output='sos'),x)
        parts[name]=x/(np.max(np.abs(x))+1e-12)
    bed=np.zeros((round(spec['duration']*RATE),2))
    for event in spec['sfx']:
        first=round(event['t']*RATE)
        name=event['part']
        sound=conform(parts[name],event['dur'],event.get('speed',1),event.get('in',0),event.get('loop',False))
        pan=event.get('pan',0)
        gains=np.sqrt([1-pan,1+pan])*event['gain']
        bed[first:first+len(sound)]+=sound[:,None]*gains
    sf.write(AUDIO/'sfx.wav',bed,RATE,subtype='PCM_24')
    voice,sr=sf.read(ROOT.parent/'surgery/audio/narration.wav',always_2d=True)
    if sr!=RATE or len(voice)!=len(bed):raise ValueError('Narration clock mismatch')
    sf.write(AUDIO/'mix.wav',voice+bed,RATE,subtype='FLOAT')


if __name__=='__main__':
    main()
