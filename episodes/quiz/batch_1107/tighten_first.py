from pathlib import Path
import json,math,shutil
import soundfile as sf
import numpy as np
W=Path(__file__).resolve().parents[3];p=W/'upload/pkg/q020_batch1107'
q=json.load(open(p/'qa.json'));c=json.load(open(p/'case.json'))
if (p/'tightened.json').exists():raise SystemExit('already tightened')
original=p/'mix_master_before_tighten.wav';shutil.copyfile(p/'mix_master.wav',original)
x,sr=sf.read(original,dtype='float32');cuts=[]
for r in q['gates']['C1']['evidence']['pauses']:
 if not r['pass_']:
  n=math.ceil((r['seconds']-.1)*30-1e-7);length=n*sr//30;center=(r['at']+r['seconds']/2)*sr;a=round(center-length/2);cuts.append((a,a+length,n))
keep=np.ones(len(x),bool)
for a,b,n in cuts:keep[a:b]=False
sf.write(p/'mix_master.wav',x[keep],sr,subtype='PCM_24')
def shift(t):return t-sum(n/30 for a,b,n in cuts if b/sr<=t+.00001)
for u in c['utterances']:
 u['start_s']=shift(u['start_s']);u['end_s']=shift(u['end_s']);u['from_frame']=round(u['start_s']*30);u['dur']=round((u['end_s']-u['start_s'])*30)
c['n']-=sum(n for _,_,n in cuts);c['duration']=c['n']/30
(p/'case.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
a=json.load(open(p/'audio.json'));a['items']=c['utterances'];(p/'audio.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
(p/'script.md').write_text('[COLD_OPEN @ 0.000]\n[CENTRAL_QUESTION @ 0.000]\n'+'\n'.join(f'## {u["id"]} · {u["start_s"]:.3f}–{u["end_s"]:.3f}s · {u["mode"]}\n{u["text"]}\n화면: {c["label"][j]}' for j,u in enumerate(c['utterances']))+'\n')
(p/'tightened.json').write_text(json.dumps(dict(cuts=cuts,removed_frames=sum(n for _,_,n in cuts),method='Measured final ASR sentence gaps shortened; original master preserved.'),indent=2))
print(c['n'],c['duration'])
