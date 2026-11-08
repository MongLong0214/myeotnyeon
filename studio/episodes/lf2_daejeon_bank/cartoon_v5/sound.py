"""Original locally synthesized score/SFX, no third-party samples."""
import json,subprocess
from pathlib import Path
import numpy as np,soundfile as sf
from scipy.ndimage import uniform_filter1d,maximum_filter1d
P=Path(__file__).resolve().parent;SR=24000
d=json.loads((P/'episode_data.json').read_text());duration=d['durationInFrames']/30;size=round(duration*SR)
rng=np.random.default_rng(611001);music=np.zeros(size,dtype=np.float32);sfx=np.zeros(size,dtype=np.float32)
def add(bus,w,t,gain=1):
 i=round(t*SR)
 if i>=len(bus):return
 w=w[:len(bus)-max(0,i)]
 if i<0:w=w[-i:];i=0
 bus[i:i+len(w)]+=w*gain
def kick():
 t=np.arange(int(.22*SR))/SR;return np.sin(2*np.pi*(44*t+12*(1-np.exp(-t*40))))*np.exp(-t*23)*.16
def hat():
 t=np.arange(int(.055*SR))/SR;n=rng.standard_normal(len(t));n=n-np.convolve(n,np.ones(8)/8,mode='same');return n*np.exp(-t*95)*.018
def snare():
 t=np.arange(int(.12*SR))/SR;return (rng.standard_normal(len(t))*.04+np.sin(2*np.pi*180*t)*.03)*np.exp(-t*40)
beat=60/138;roots=[73.416,58.27,87.307,65.406]
for j,t0 in enumerate(np.arange(0,duration,beat/2)):
 if j%2==0:add(music,kick(),t0)
 if j%4==2:add(music,snare(),t0)
 add(music,hat(),t0,.55 if j%2 else 1)
 root=roots[(j//32)%4];tt=np.arange(round(beat/2*SR))/SR
 freq=root*(2 if j%8 in [5,7] else 1)
 bass=(np.sin(2*np.pi*freq*tt)+.23*np.sin(2*np.pi*freq*2*tt))*np.exp(-tt*8)*.05
 add(music,bass,t0)
 if j%2==1:
  note=root*4*[1,1.5,1.2,2][(j//2)%4]
  wave=(np.sin(2*np.pi*note*tt)+.22*np.sin(2*np.pi*note*2.001*tt))*np.sin(np.pi*np.clip(tt/(beat/2),0,1))**2*.016
  add(music,wave,t0)
events=[]
for s in d['shots']:
 if s.get('serious'):continue
 t0=s['start']/30;tt=np.arange(int(.13*SR))/SR
 if s['index']%3==0:
  wave=rng.standard_normal(len(tt))*np.sin(np.pi*tt/.13)**3*.018
  add(sfx,wave,t0);events.append(dict(t=t0,kind='self-made whoosh'))
 if s.get('illustrative') and s['index']%2==0:
  tt=np.arange(int(.2*SR))/SR;freq=900-tt*3200
  wave=np.sin(2*np.pi*np.cumsum(freq)/SR)*np.sin(np.pi*tt/.2)*.037
  add(sfx,wave,t0);events.append(dict(t=t0,kind='self-made record scratch'))
for n in d['narration']:
 a=round(n['start_s']*SR);b=round(n['end_s']*SR)
 if n.get('serious'):music[a:b]*=.16
 if n.get('loop'):
  tt=np.arange(int(.65*SR))/SR;wave=np.sin(2*np.pi*(180*tt+280*tt**2))*np.sin(np.pi*tt/.65)**2*.025
  add(sfx,wave,max(n['start_s'],n['end_s']-.65));music[max(a,b-int(.9*SR)):b]*=1.65;events.append(dict(t=max(n['start_s'],n['end_s']-.65),kind='self-made cliffhanger rise'))
# One abbreviated non-counting gunfire composite; there are no repeated shot sounds.
tt=np.arange(round(.2*SR))/SR
burst=(rng.standard_normal(len(tt))*.17*np.exp(-tt*52)+np.sin(2*np.pi*72*tt)*np.exp(-tt*29)*.22)
add(sfx,burst,12/30);events.append(dict(t=.4,kind='self-made abbreviated gunfire composite; no asserted shot count'))
for s in d['shots']:
 if s.get('serious'):music[round(s['start']/30*SR):round(s['end']/30*SR)]*=.4
voice,sr=sf.read(P/'public/voice_full.wav');v=voice[::2][:size]
env=np.sqrt(uniform_filter1d(v*v,size=round(SR*.025)));duck=1-.78*np.clip(maximum_filter1d(env,size=round(SR*.08))/.075,0,1)
music*=duck
voice_gain=min(1.5,.13/max(.0001,float(np.sqrt(np.mean(v*v)))));mix=v*voice_gain+music+sfx
peak=float(np.max(np.abs(mix)));mix*=min(1,.94/peak)
sf.write(P/'audio/music.wav',music,SR,subtype='PCM_24');sf.write(P/'audio/sfx.wav',sfx,SR,subtype='PCM_24');sf.write(P/'audio/mix_raw.wav',mix,SR,subtype='PCM_24')
subprocess.run(['ffmpeg','-v','error','-y','-i',str(P/'audio/mix_raw.wav'),'-af','loudnorm=I=-16:TP=-1.5:LRA=9','-ar','48000','-c:a','pcm_s24le',str(P/'public/soundtrack.wav')],check=True)
(P/'audio/sound_events.json').write_text(json.dumps(dict(tempo=138,source='Original deterministic oscillator/noise synthesis in sound.py, no third-party samples',ducking='RMS envelope, up to 78% reduction under voice',events=events),ensure_ascii=False,indent=2))
(P/'audio/credits.txt').write_text('Music and all SFX: original local oscillator/noise synthesis in sound.py. No licensed sample dependency, paid service, network or uploaded material. Voice: local Supertonic 3 M1, same voice as Shorts; model license remains at $HOME/.cache/supertonic3/LICENSE. Local Pretendard font uses its bundled OFL license.\n')
print('SOUND',duration,'s,',len(events),'events, peak raw',peak)
