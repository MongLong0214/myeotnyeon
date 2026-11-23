"""Conform only the isolated, listen-checked Earshot recordings to the edited picture."""
import json
from pathlib import Path
import sys
import subprocess

import numpy as np
import soundfile as sf
from scipy.signal import butter, sosfilt

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent)]
from edit import DURATION,cut_time
from mix import RATE,conform

PARTS=HERE.parent/'audio/parts'
PRE=HERE/'earshot_premix.wav'
OUT=HERE/'earshot_master.m4a'
check=json.loads((PARTS.parent/'sfx_report.json').read_text())
files={}
limits={'bur':(920,12400),'root_bur':(850,12400),'saline':(830,10100),
        'aspiration':(125,4050),'fracture':(125,9890),'knot':(290,7900),
        'liquid':(105,7500),'tissue':(165,6600)}
for name,(lo,hi) in limits.items():
    if not check[name]['pass']:raise ValueError(name+' failed the Earshot listen check')
    raw,rate=sf.read(PARTS/(name+'.wav'),always_2d=True)
    if rate!=RATE:raise ValueError(rate)
    raw=sosfilt(butter(2,(lo,hi),fs=RATE,btype='bandpass',output='sos'),raw.mean(1))
    files[name]=raw/(np.max(abs(raw))+1e-8)

audio=np.zeros((round(DURATION*RATE),2))
def cue(t,name,dur,gain,speed=1,offset=0,pan=0,loop=False,pressure=0,shade=0):
    v=conform(files[name],dur,speed,offset,loop)
    x=np.arange(len(v))/RATE
    if pressure:
        if name=='aspiration':
            v*=.66+.34*np.sin(x*9.5+.9*np.sin(2.8*x))+.11*np.sin(x*22)
        else:
            v*=.86+.10*np.sin(x*11.3+.87*np.sin(x*5))+.04*np.sin(x*30)
    if shade:v=sosfilt(butter(2,shade,fs=RATE,btype='lowpass',output='sos'),v)
    start=round(t*RATE);end=min(len(audio),start+len(v))
    audio[start:end]+=v[:end-start,None]*np.sqrt([1-pan,1+pan])*gain

def hit(shot,src,*args,**kw):cue(cut_time(shot,src),*args,**kw)
def motor(a,b,name,gain,pitch,pan):
    cue(a,name,b-a,gain,pitch,.10,pan,True,1)
def drop(t,level=.38,pitch=.93,pan=0):
    cue(t,'liquid',.27,level,pitch,0,pan)

# Tiny pre-load creaks precede the fracture. A pitched-down body under the fast transient
# separates the slow-motion hook from the later real-time release.
cue(.08,'tissue',.31,.15,.67,.04,-.13,shade=3400)
cue(.67,'knot',.23,.16,.68,.06,-.07,shade=2600)
cue(1.08,'fracture',.15,.21,.72,.54,-.04)
for at,level in [(cut_time('fracture',23.88),1.08),(cut_time('section',23.88),.92)]:
    cue(at-.008,'fracture',.31,level,1.01,1.056,-.025)
    cue(at+.013,'fracture',.41,level*.63,.54,.535,.06,shade=3900)
    cue(at+.12,'fracture',.15,level*.19,1.26,.295,.19)
    drop(at+.32,.21,.69,.09)
cue(2.66,'tissue',.26,.17,.75,.085,.05)
# Puncture, withdrawal, then progressively wetter passes along the cut.
hit('anaesthesia',4.22,'tissue',.19,.26,1.16,.06,.10)
hit('anaesthesia',5.81,'tissue',.26,.22,.89,0,.07)
drop(cut_time('anaesthesia',6.17),.19,1.14,.08)
for t,dry,wet,speed in [(6.44,.34,.18,.85),(7.11,.33,.12,.70),(7.91,.40,.19,.87),(8.74,.32,.27,.74),(9.02,.16,.18,.91)]:
    cue(t,'tissue',.32,dry,speed,0,-.15)
    drop(t+.09,wet,speed*.86,-.10)
for t,k in [(10.42,.25),(10.96,.18),(11.27,.31),(11.95,.23)]:
    cue(t,'tissue',.36,k,.64,.025,-.13,shade=3600)
drop(11.65,.21,.81,.10)
# Thin high-frequency rotary whine, spray and low, wet aspiration trade prominence on contact.
motor(12.60,18.39,'bur',.49,2.45,.14)
motor(12.68,18.23,'saline',.22,1.14,-.12)
motor(13.36,16.46,'aspiration',.28,1.09,-.29)
motor(16.44,18.49,'aspiration',.67,.90,-.26)
for t,k,s in [(14.59,.15,.77),(15.98,.18,.81),(16.58,.32,.63),(16.76,.27,.80),(17.18,.35,.69),(17.39,.29,.82),(17.96,.25,.59),(18.22,.18,.70)]:
    drop(t,k,s,-.24)
motor(18.61,21.87,'bur',.50,2.66,.09)
motor(18.72,21.77,'saline',.23,1.11,-.09)
cue(22.48,'tissue',.34,.19,.63,.05,.12,shade=2900)
hit('section',23.71,'knot',.20,.25,.80,.045,-.09,shade=3450)
# Crown and separate roots release at different times.
for src,amount in [(25.36,.28),(25.64,.54),(26.13,.20),(28.59,.32),(28.81,.50),(29.38,.33),(30.68,.28),(31.00,.54),(31.41,.39),(32.08,.21)]:
    t=cut_time('delivery',src)
    cue(t,'tissue',.36,amount,.76 if src<30 else .68,.012,.09)
    drop(t+.10,amount*.72,.78,-.04)
a=cut_time('delivery',27.21);b=cut_time('delivery',27.91)
motor(a,b,'root_bur',.44,2.42,.12);motor(a+.04,b-.02,'saline',.21,1.11,-.10)
for t,vol,pitch in [(34.72,.28,.87),(35.06,.37,.70),(35.71,.30,.94),(36.42,.40,.77),(37.01,.24,.69)]:
    drop(t,vol,pitch,.06)
a=cut_time('socket',33.92);b=cut_time('socket',36.18)
motor(a,b,'saline',.42,1.08,-.13)
cue(a+.26,'aspiration',b-a-.47,.33,.96,.15,.18,True,1)
for src,vol,spd in [(34.28,.26,1),(34.86,.22,.84),(35.36,.30,.79),(35.79,.27,.69),(36.40,.33,.77),(36.86,.24,.91)]:
    drop(cut_time('socket',src),vol,spd,.16)
# Needle entry, thread travel, tightening and scissors meet the picture landmarks.
for src,vol in [(38.17,.24),(38.87,.23),(39.16,.21)]:
    hit('closure',src,'tissue',.26,vol,.91,.025,-.11)
for src,vol,spd in [(38.43,.26,.83),(39.37,.30,.82),(39.75,.48,.89),(40.17,.40,1.12)]:
    hit('closure',src,'knot',.34,vol,spd,.014,.09,shade=5900)
hit('closure',41.32,'fracture',.105,.54,1.9,1.067,.11,shade=9500)
hit('closure',41.35,'knot',.14,.23,1.3,0,.04)
hit('specimen',44.70,'knot',.24,.12,.80,.09,.12,shade=2900)
hit('specimen',45.67,'tissue',.26,.30,.72,.018,.08,shade=3200)
hit('specimen',45.71,'liquid',.18,.22,.82,.001,.03,shade=2900)
hit('specimen',46.10,'knot',.17,.19,1.16,.05,.14,shade=4300)
hit('specimen',46.82,'tissue',.28,.12,.61,.03,.21,shade=2400)
# Mild transient compression before two-pass programme normalization.
audio=np.tanh(audio*1.45)/1.45
sf.write(PRE,audio,RATE,subtype='PCM_24')

def run(cmd):
    return subprocess.run(['nice','-n','15','ffmpeg','-nostdin','-hide_banner',*cmd],capture_output=True,text=True,check=True)
target='loudnorm=I=-14:TP=-2.65:LRA=9'
r=run(['-i',str(PRE),'-af',target+':print_format=json','-f','null','-'])
values=json.loads(r.stderr[r.stderr.rindex('{'):r.stderr.rindex('}')+1])
norm=target+':linear=true'+''.join(':'+k+'='+values[v] for k,v in [('measured_I','input_i'),('measured_TP','input_tp'),('measured_LRA','input_lra'),('measured_thresh','input_thresh'),('offset','target_offset')])
run(['-y','-i',str(PRE),'-af',norm+',volume=0.36dB','-ar',str(RATE),'-t',str(DURATION),'-c:a','aac','-b:a','192k',str(OUT)])
print('Earshot-only AAC measured after encode:')
r=run(['-i',str(OUT),'-af','loudnorm=print_format=json','-f','null','-'])
print(r.stderr[r.stderr.rindex('{'):r.stderr.rindex('}')+1])
