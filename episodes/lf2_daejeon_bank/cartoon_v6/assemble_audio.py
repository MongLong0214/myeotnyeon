import json,math
from pathlib import Path
import numpy as np,soundfile as sf
P=Path(__file__).resolve().parent
src=json.loads((P/'audio/index.json').read_text());cues=json.loads((P/'script_source.json').read_text())['cues']
voice=[];pos=0;items=src['items'];narr=[]
for i,n in enumerate(items):
 w,sr=sf.read(P/'audio'/f"{n['id']}.wav");assert sr==48000
 n.update(start_s=pos/sr,end_s=(pos+len(w))/sr);voice.append(w);pos+=len(w)
 if i+1<len(items):voice.append(np.zeros(11520));pos+=11520
frames=math.ceil(pos/1600);wav=np.concatenate(voice);wav=np.pad(wav,(0,frames*1600-len(wav)))
sf.write(P/'public/voice_full.wav',wav,48000,subtype='PCM_24')
for i,c in enumerate(cues):
 ns=[n for n in items if n['narrationId']==f'N{i+1:03}']
 narr.append(dict(c,id=f'N{i+1:03}',start_s=ns[0]['start_s'],end_s=ns[-1]['end_s']))
d=dict(fps=30,durationInFrames=frames,audioDuration=len(wav)/48000,narration=narr,sentences=items)
(P/'episode_data.json').write_text(json.dumps(d,ensure_ascii=False,separators=(',',':')))
(P/'timing.json').write_text(json.dumps(d,ensure_ascii=False,indent=2))
print(frames,frames/30,sum(n['syllables'] for n in items)/(frames/30))
