from pathlib import Path
import sys, subprocess
import numpy as np
from scipy.signal import find_peaks
root=Path('.sfx-work/recordings')
for item in sys.argv[1:]:
 p=root/(item+'.mp3')
 if not p.exists(): continue
 rate=16000
 b=subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-ac','1','-ar',str(rate),'-f','f32le','-'])
 a=np.frombuffer(b,dtype='f4'); w=160; y=a[:len(a)//w*w].reshape(-1,w); t=np.arange(len(y))*.01
 rms=np.sqrt(np.mean(y*y,axis=1)); db=20*np.log10(rms+1e-8)
 peaks=find_peaks(db,distance=12,prominence=8)[0]; peaks=peaks[db[peaks]>np.max(db)-24]
 print(item, 'duration',round(len(a)/rate,2),'maxdB',round(20*np.log10(np.max(abs(a))+1e-8),1),'peaks', ' '.join(f'{t[i]:.2f}/{db[i]:.0f}' for i in peaks[:110]));
 blk=min(1,.25 if len(a)<20*rate else 1); bn=int(blk/.01)
 if len(a)/rate>115: bn=100
 br=np.sqrt(np.mean(rms[:len(rms)//bn*bn].reshape(-1,bn)**2,axis=1)); print(' block RMS', blk,' '.join(f'{i*bn*.01:.2f}/{20*np.log10(x+1e-8):.0f}' for i,x in enumerate(br) if (len(br)<120 or x>np.max(br)*.3)))
