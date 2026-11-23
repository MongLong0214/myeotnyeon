"""Mix the episode's recorded cues and a continuous, circular Earshot score at 48 kHz."""
from functools import lru_cache
from pathlib import Path
import hashlib
import json
import re
import subprocess
import numpy as np
import soundfile as sf
from scipy.ndimage import maximum_filter1d, uniform_filter1d
from scipy.signal import butter, correlate, sosfilt

EP = Path(__file__).resolve().parent.parent
CACHE = EP/'production/.cache'
SPEC = json.loads((EP/'episode.json').read_text())
RATE = 48000
N = round(SPEC['duration'] * RATE)
LIBRARY = EP/SPEC['audio']['recordings_dir']
LEDGER = (EP/SPEC['audio']['recording_ledger']).read_text()
SCORE = CACHE/'score'
SCORE.mkdir(exist_ok=True)
def linear(db):
    return 10**(db/20)
def rms(x):
    return float(np.sqrt(np.mean(x*x)))
def filtered(x, limits):
    return sosfilt(butter(2, limits, fs=RATE, btype='bandpass', output='sos'),x,axis=0)

@lru_cache(None)
def take(name):
    path=LIBRARY/name
    sha=hashlib.sha256(path.read_bytes()).hexdigest()
    row=next(row for row in LEDGER.splitlines() if f'/s/{path.stem}/' in row)
    if sha not in row or 'CC0' not in row or 'creativecommons.org/publicdomain/zero/1.0/' not in path.with_suffix('.html').read_text():
        raise ValueError(f'Source rights or file digest mismatch for {name}')
    data=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-ar',str(RATE),'-ac','2','-f','f32le','-'])
    return np.frombuffer(data,np.float32).reshape(-1,2)
def envelope(samples, attack, release):
    for count,reverse in ((round(attack*RATE),False),(round(release*RATE),True)):
        n=min(len(samples),count)
        if n:
            ramp=(.5-.5*np.cos(np.linspace(0,np.pi,n)))[:,None]
            if reverse:samples[-n:] *= ramp[::-1]
            else:samples[:n] *= ramp

def sound(name, pitch=None):
    path=SCORE/(name+'.wav')
    if not path.exists():
        args=['--sound','note/pizzicato','--pitch',pitch,'--bright','-.32'] if pitch else ['--sound','drone/dark','--pitch','D2','--dur','48','--bright','-.45','--width','.55']
        subprocess.run([str(EP.parents[1]/'.venv/bin/earshot'),'make',*args,'--seed','36','-o',str(path)],check=True)
    x,sr=sf.read(path,always_2d=True,dtype='float32')
    if sr!=RATE:raise ValueError((path,sr))
    return x

def score():
    x=filtered(sound('drone'),(62,4100))
    start=2*RATE; overlap=RATE; margin=round(.016*RATE)
    head=x[start:start+overlap].mean(axis=1)
    tail=x[start+N-margin:start+N+overlap+margin].mean(axis=1)
    offset=np.argmax(correlate(tail,head,mode='valid',method='fft'))-margin
    ix=start+np.arange(N+overlap)*(1+offset/N)
    base=np.floor(ix).astype(int);frac=(ix-base)[:,None]
    raw=x[base]*(1-frac)+x[base+1]*frac
    bed=raw[:N].copy()
    w=(.5-.5*np.cos(np.linspace(0,np.pi,overlap)))[:,None]
    bed[:overlap]=raw[N:]*(1-w)+raw[:overlap]*w
    avg=uniform_filter1d(np.mean(bed*bed,axis=1),RATE,mode='wrap')
    bed*= (linear(-24)/np.sqrt(avg))[:,None]
    notes={k:sound('pluck-'+k,p) for k,p in zip('dfac',['D4','F4','A4','C5'])}
    # Eight bars resolve to D. The final pluck rings across the edit point.
    for i,(beat,note) in enumerate([(0,'d'),(2.5,'a'),(4.75,'f'),(7,'d'),(9.5,'a'),(11.5,'c'),(13.75,'a'),(16,'f'),(18.5,'d'),(20,'a'),(22.5,'f'),(25,'a'),(27.75,'c'),(29.5,'a'),(31.25,'d')]):
        part=notes[note].copy()
        part*=linear((-18.8,-22,-21.4,-23)[i%4])/np.max(abs(part))
        envelope(part,.009,.075)
        pos=round(beat*N/32)
        first=min(N-pos,len(part));bed[pos:pos+first]+=part[:first]
        bed[:len(part)-first]+=part[first:]
    return bed

def room_tone():
    bed=np.zeros((N,2))
    clip=take(SPEC['audio']['bed']['recording'])
    width=round(.85*RATE)
    for i,offset in enumerate((75.8,76.2,76.5)):
        t=round(i*N/3); end=round((i+1)*N/3)
        n=end-t+width;s=round(offset*RATE)
        part=filtered(clip[s:s+n],(68,3550))
        part*=linear(-41)/rms(part)
        envelope(part,width/RATE,width/RATE)
        first=min(n,N-t);bed[t:t+first]+=part[:first]
        bed[:n-first]+=part[first:]
    return bed

def effects():
    bus=np.zeros((N,2))
    # Target rms, passband, attack and release for the recorded material.
    treatment={
        '155913':(-27, (280,8500),.004,.034),
        '728347':(-17.8,(400,10100),.088,.18),
        '816678':(-30,(530,4300),.06,.10),
        '211605':(-25,(135,5100),.019,.075),
        '816680':(-26,(240,5200),.024,.06),
        '707344':(-20,(200,9900),.078,.105),
        '680616':(-22,(440,7200),.069,.088),
        '707321':(-21.5,(125,6100),.12,.13),
    }
    for beat in SPEC['beats']:
        for cue in beat['sfx']:
            name=cue['recording'];key=Path(name).stem
            level,band,attack,release=treatment[key]
            dur=cue['dur']; t=np.arange(round(dur*RATE))/RATE
            rate=np.ones(len(t))
            if key in ('707344','728347'):
                rate=np.interp(t/dur,[0,.09,.35,.68,.85,1],[1.05,.97,.985,.95,.97,1.06])
            idx=np.rint(cue['source_in_s']*RATE+np.cumsum(rate)-rate[0]).astype(int)
            source=take(name)[idx]
            mono=source[:,0] if key=='680616' else source.mean(axis=1)
            x=filtered(mono,band)
            if key=='680616' and dur<1:level-=4
            bound=rms(x)*3.1
            x=bound*np.tanh(x/max(bound,1e-9))
            x*=linear(level)/rms(x)
            p=-.18 if key=='707321' else .08
            stereo=x[:,None]*np.sqrt([1-p,1+p])
            envelope(stereo,attack,release)
            start=round(RATE*cue['t'])
            bus[start:start+len(stereo)]+=stereo
    return bus

def loudness(path):
    p=subprocess.run(['ffmpeg','-hide_banner','-nostats','-i',str(path),'-af','loudnorm=I=-14:TP=-1.5:print_format=json','-f','null','-'],capture_output=True,text=True,check=True)
    return json.loads(re.search(r'\{[^{}]+"input_i"[^{}]+\}',p.stderr,re.S)[0])

def main():
    sfx=effects(); ambient=room_tone()
    power=uniform_filter1d(np.mean(sfx*sfx,axis=1),round(.055*RATE),mode='wrap')
    held=maximum_filter1d(power,round(.15*RATE),mode='wrap')
    depth=np.clip((10*np.log10(np.maximum(held,1e-12))+30)/3.8,0,3.2)
    depth=uniform_filter1d(depth,round(.18*RATE),mode='wrap')
    dry=score()
    # AAC's first overlap window is most transparent near a shared stereo zero crossing.
    # Rotate only the two continuous beds; all fourteen picture-locked effects keep their sample times.
    positions=np.arange(-RATE//20,RATE//20)
    bed_start=dry[positions]+ambient[positions]
    bed_previous=dry[positions-1]+ambient[positions-1]
    cost=np.maximum(abs(bed_start),abs(bed_previous)).max(axis=1)+abs(bed_start-bed_previous).max(axis=1)
    phase=int(positions[np.argmin(cost)])
    ambient=np.roll(ambient,-phase,axis=0)
    music=np.roll(dry,-phase,axis=0)*linear(-depth)[:,None]
    program=music+sfx+ambient
    wav=CACHE/'rootcanal-mix.wav'; dest=CACHE/'rootcanal-audio.m4a'
    sf.write(wav,program,RATE,subtype='FLOAT')
    gain=-14-float(loudness(wav)['input_i'])
    for attempt in range(5):
        sf.write(wav,program*linear(gain),RATE,subtype='PCM_24')
        subprocess.run(['ffmpeg','-v','error','-nostdin','-y','-i',str(wav),'-c:a','aac','-b:a','320k',str(dest)],check=True)
        measured=loudness(dest)
        error=-14-float(measured['input_i'])
        if abs(error)<.04 and float(measured['input_tp'])<=-1.5:break
        if float(measured['input_tp'])>-1.5:
            # Compress foreground peaks only, leaving music automation intact.
            ceiling=linear(-2.8-gain)
            allowance=np.maximum(ceiling-np.max(abs(ambient+music),axis=1),.004)
            sfx=allowance[:,None]*np.tanh(sfx/allowance[:,None])
            program=ambient+music+sfx
        gain+=error
    else:raise ValueError(measured)
    sf.write(CACHE/'music.wav',music*linear(gain),RATE,subtype='PCM_24')
    metrics=dict(sample_rate=RATE,samples=N,integrated_lufs=float(measured['input_i']),true_peak_dbtp=float(measured['input_tp']),maximum_duck_db=float(depth.max()),music_min_100ms_rms_db=20*np.log10(np.sqrt(np.mean((music*linear(gain)).reshape(-1,RATE//10,2)**2,axis=(1,2))).min()),mix_seam_step=float(np.max(abs(program[-1]-program[0]))*linear(gain)),events=sum(len(b['sfx']) for b in SPEC['beats']))
    decoded=np.frombuffer(subprocess.check_output(['ffmpeg','-v','error','-i',str(dest),'-t',str(SPEC['duration']),'-f','f32le','-']),np.float32).reshape(-1,2)
    assert len(decoded)==N
    nearby=np.abs(np.diff(np.vstack((decoded[-2048:],decoded[:2048])),axis=0)).max(axis=1)
    metrics.update(bed_phase_samples=phase,aac_seam_step=float(abs(decoded[-1]-decoded[0]).max()),aac_edge_p99_step=float(np.quantile(nearby,.99)))
    print(json.dumps(metrics,indent=2))
    (CACHE/'audio-metrics.json').write_text(json.dumps(metrics,indent=2))
if __name__=='__main__': main()
