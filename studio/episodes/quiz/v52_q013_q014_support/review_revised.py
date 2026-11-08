from pathlib import Path
import json,subprocess,math,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
W=Path(__file__).resolve().parents[3];S=Path(__file__).parent
font=ImageFont.truetype(str(W/'production/compositor/public/fonts/Pretendard-Bold.otf'),20)
def save(p,x):
 with p.open('x') as f:json.dump(x,f,ensure_ascii=False,indent=1)
def decode(v,fs,w):
 sel='+'.join('eq(n\\,%d)'%f for f in sorted(fs));h=w*16//9
 r=subprocess.run(['ffmpeg','-v','error','-i',str(v),'-vf',f'select={sel},scale={w}:{h}','-vsync','0','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True,check=True)
 a=np.frombuffer(r.stdout,np.uint8).reshape(-1,h,w,3);assert len(a)==len(fs)
 return dict(zip(sorted(fs),a))
def one(q):
 p=W/'episodes/quiz'/q/'v52';v=p/'candidate_revised.mp4';d=json.loads((p/('render_final_aligned.json' if q=='q014' else 'render_final.json')).read_text());n=d['durationInFrames'];outro=next(c for c in d['cues'] if c['scene']=='outro');card=n-45
 labels={0:'HOOK 0s',30:'HOOK 1s',60:'HOOK 2s',61:'BODY cut',card:'END CARD',n-1:'END last'}
 for c in d['cues']:
  labels.setdefault(c['from'],c['id']+' '+c['scene']+' start')
  if c['scene']!='outro':labels.setdefault(min(c['from']+18,c['from']+c['dur']-1),c['id']+' settled')
  if c['scene']=='weigh':
   for k in [2,3,4]:labels.setdefault(c['from']+c['a'][f's{k}']+20,'evidence '+str(k-1))
  if c['scene']=='reveal':
   labels[c['from']+c['a']['s1']+18]='ANSWER'
   labels[c['from']+c['a']['s2']+18]='ANSWER second line'
 window=list(range(outro['from']-5,card+7));fs=set(labels)|set(window);a=decode(v,fs,360)
 dr=p/'review_frames_revised';dr.mkdir()
 for f,x in a.items():
  out=dr/f'f{f:05}.jpg';assert not out.exists();Image.fromarray(x).save(out,quality=94,subsampling=0)
 # The ending must keep the verdict panel alive all the way to the full-screen card.
 before=a[outro['from']-1][175:485,35:325].astype(float)
 rows=[]
 for f in range(outro['from'],card):
  z=a[f][175:485,35:325].astype(float);rows.append(dict(frame=f,seconds=f/30,verdict_roi_mae=float(np.abs(z-before).mean())))
 cut=float(np.abs(a[card].astype(float)-a[card-1].astype(float)).mean())
 ok=all(r['verdict_roi_mae']<8 for r in rows) and cut>10
 strip=Image.new('RGB',(360*len(window),680),(16,20,25));draw=ImageDraw.Draw(strip)
 for i,f in enumerate(window):draw.text((i*360+8,8),f'{q} f{f} {f/30:.3f}s',font=font,fill='white');strip.paste(Image.fromarray(a[f]),(i*360,36))
 dest=S/f'end_transition_{q}_revised.jpg';assert not dest.exists();strip.save(dest,quality=95,subsampling=0)
 save(p/'end_transition_checked_revised.json',dict(pass_=ok,range_inclusive=[window[0],window[-1]],outro_cue_from=outro['from'],full_card_from=card,held_verdict_frames=rows,cut_mae=cut,method='Every decoded frame from 5 frames before old outro through 6 frames after full card. Compare verdict ROI against last verdict frame; inspect consecutive-frame strip. Current getEndTransition keeps reveal until N-45; no intermediate Outro mounted.',strip=str(dest.relative_to(W)),manual_review_pending=True))
 save(p/'review_frame_manifest_revised.json',dict(episode=q,frames=[dict(frame=f,seconds=f/30,label=label,file=str((dr/f'f{f:05}.jpg').relative_to(W))) for f,label in sorted(labels.items())]))
 print(q,'end_transition',ok,rows,'cut',cut,flush=True)
def sheet():
 manifests=[json.loads((W/'episodes/quiz'/q/'v52/review_frame_manifest_revised.json').read_text()) for q in ['q013','q014']];cols=6;rowh=696;rows=sum(math.ceil(len(m['frames'])/cols) for m in manifests)
 im=Image.new('RGB',(cols*360,rows*rowh),(16,20,25));draw=ImageDraw.Draw(im);offset=0
 for m in manifests:
  for i,r in enumerate(m['frames']):
   x=i%cols*360;y=(offset+i//cols)*rowh;draw.text((x+7,y+6),f"{m['episode']} f{r['frame']} / {r['seconds']:.2f}s",font=font,fill='white');draw.text((x+7,y+30),r['label'],font=font,fill='#e8c052');im.paste(Image.open(W/r['file']),(x,y+56))
  offset+=math.ceil(len(m['frames'])/cols)
 out=W/'research/metrics/v52_q013_q014_sheet.jpg';assert not out.exists();im.save(out,quality=95,subsampling=0)
 save(W/'research/metrics/v52_q013_q014_sheet_frames.json',manifests);print('sheet',im.size,flush=True)
if __name__=='__main__':sheet() if sys.argv[1]=='sheet' else one(sys.argv[1])
