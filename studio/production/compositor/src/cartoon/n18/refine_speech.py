from pathlib import Path
import json,numpy as np,soundfile as sf
W=Path(__file__).resolve().parents[5];O=W/'episodes/v4/n18/cartoon_v4';S=Path(__file__).parent
d=json.loads((O/'shots.json').read_text());a,sr=sf.read(O/'public/narration.wav',always_2d=True);a=a.mean(1);rms=np.sqrt(np.mean(a.reshape(-1,1600)**2,axis=1));amp=np.clip((rms-.004)/.075,0,1)**.7
speech=[{'amplitude':0,'viseme':'rest'} for v in amp]
for c in d['subtitles']:
 chars=[ch for ch in c['text'] if '\uac00'<=ch<='\ud7a3'];st=c['from'];en=c['to'];ener=np.maximum(rms[st:en]-.003,.001)**.35;cum=np.cumsum(ener);cum/=cum[-1]
 if not chars:continue
 for j in range(st,en):
  z=min(len(chars)-1,int(cum[j-st]*len(chars)));code=ord(chars[z])-0xac00;initial=code//588;vowel=(code%588)//28;final=code%28;phase=(cum[j-st]*len(chars))%1
  if final in (1,2,7,16,17,18,19,20,22,23,24,25,26,27) and phase>.72:shape='M'
  elif initial in (6,7,8,17) and phase<.22:shape='M' if initial==6 else 'F'
  elif vowel in (8,9,10,11,12,13,14,15,16,17):shape='O'
  elif vowel in (1,3,5,7,19,20):shape='E'
  else:shape='A'
  speech[j]={'amplitude':round(float(amp[j]),4),'viseme':shape if amp[j]>.045 else 'rest'}
d['speech']=speech;d['viseme_method']='Same as engine-v4 LF2: energy-weighted Korean grapheme progression inside existing captions, per-frame RMS gate. Approximate visemes, not forced phoneme alignment.'
(O/'shots.json').write_text(json.dumps(d,ensure_ascii=False,indent=2));(S/'data.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')))
print('speech frames',len(speech))
