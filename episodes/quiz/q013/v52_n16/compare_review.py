from pathlib import Path
import json,subprocess,hashlib,math,csv
import numpy as np
from PIL import Image,ImageDraw,ImageFont
W=Path(__file__).resolve().parents[4];S=Path(__file__).parent;A=W/'upload/v52_q013.mp4';B=W/'upload/v52_q013_n16.mp4'
def save(p,x):
 with p.open('x') as f:json.dump(x,f,ensure_ascii=False,indent=1)
def probe(p):return json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(p)]))
def md5(p,copy=False):return subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-map','0:a:0','-c:a','copy' if copy else 'pcm_s32le','-f','md5','-']).decode().strip()
a,b=probe(A),probe(B);va=next(s for s in a['streams'] if s['codec_type']=='video');vb=next(s for s in b['streams'] if s['codec_type']=='video')
checks={k:[va.get(k),vb.get(k)] for k in ['nb_read_frames','duration','r_frame_rate','width','height']};assert all(x==y for x,y in checks.values()),checks
ma,mb=md5(A,True),md5(B,True);pa,pb=md5(A),md5(B);assert ma==mb and pa==pb
N=int(va['nb_read_frames']);d=json.loads((S/'render_n16.json').read_text());labels={0:'HOOK start',30:'HOOK 1s',60:'HOOK 2s',61:'C1 dormitory',N-45:'END #16',N-1:'END last #16',200:'C2 court / original blank',260:'C3 key / original blank'}
for c in d['cues']:
 if c['scene']=='outro':continue # getEndTransition holds verdict until full card
 start=max(61,c['from']);labels.setdefault(start,c['id']+' scene cut');labels.setdefault(min(start+18,N-46),c['id']+' settled')
 p=c['p'];s1=c['a']['s1']
 for st in p.get('stamps',[]):
  for k in ['at','until']:
   if k in st:
    f=c['from']+s1+st[k];labels.setdefault(f,c['id']+' stamp '+k);labels.setdefault(min(f+10,c['from']+c['dur']-1),c['id']+' stamp settled')
 if c['scene']=='weigh':
  for k in [2,3,4]:labels[c['from']+c['a'][f's{k}']+20]='C4 evidence '+str(k-1)
 if c['scene']=='reveal':
  labels[c['from']+c['a']['s1']+18]='C5 answer';labels[c['from']+c['a']['s2']+18]='C5 prosecution request'
labels[754]='Last held verdict';labels={f:label for f,label in labels.items() if 0<=f<N}
ps=[subprocess.Popen(['ffmpeg','-v','error','-i',str(v),'-an','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE) for v in [A,B]]
rows=[];art=[];stills={};boxes={'badge':[304,184,784,256],'end_card_text':[128,1280,800,1376],'C2_C3_panel':[60,468,1020,1332]};out=S/'review_frames';out.mkdir()
# The changed set is clipped to the same rounded panel. Mask only the active scene time and badge/end text.
for f in range(N):
 xs=[np.frombuffer(p.stdout.read(1080*1920*3),np.uint8).reshape(1920,1080,3) for p in ps]
 delta=xs[0].astype(np.float32)-xs[1].astype(np.float32);mask=np.ones((1920,1080),bool)
 if 61<=f<N-45:
  x0,y0,x1,y1=boxes['badge'];mask[y0:y1,x0:x1]=False
 if f>=N-45:
  x0,y0,x1,y1=boxes['end_card_text'];mask[y0:y1,x0:x1]=False
 if 139<=f<329:
  x0,y0,x1,y1=boxes['C2_C3_panel'];mask[y0:y1,x0:x1]=False
  # Left/lower artwork ROI excludes all original stamps/tags and source text.
  roi=xs[1][940:1200,160:750];oldroi=xs[0][940:1200,160:750]
  pixels=int(np.count_nonzero(np.max(np.abs(roi.astype(np.int16)-oldroi.astype(np.int16)),axis=2)>20));art.append(dict(frame=f,changed_art_pixels=pixels))
 mse=float(np.square(delta[mask]).mean());score=10*math.log10(255**2/mse) if mse else float('inf');rows.append((f,score,mse))
 if f in labels:
  im=Image.fromarray(xs[1]);im.resize((360,640)).save(out/f'f{f:04}.jpg',quality=95,subsampling=0)
 if f in [200,260,300,770]:stills[f]=[Image.fromarray(x.copy()) for x in xs]
for p in ps:assert p.wait()==0
with (S/'per_frame_psnr.csv').open('x') as o:
 c=csv.writer(o);c.writerow(['frame_zero_based','rgb_psnr_db_outside_active_change_regions','mse']);c.writerows(rows)
m=min(rows,key=lambda x:x[1]);assert m[1]>=45,m
assert all(r['changed_art_pixels']>10000 for r in art),min(art,key=lambda r:r['changed_art_pixels'])
font=ImageFont.truetype(str(W/'production/compositor/public/fonts/Pretendard-Bold.otf'),20)
cols=6;rowh=696;sheet=Image.new('RGB',(cols*360,math.ceil(len(labels)/cols)*rowh),(16,20,25));draw=ImageDraw.Draw(sheet);manifest=[]
for i,(f,label) in enumerate(sorted(labels.items())):
 x=i%cols*360;y=i//cols*rowh;draw.text((x+7,y+6),f'q013 #16 | f{f} / {f/30:.3f}s',font=font,fill='white');draw.text((x+7,y+30),label,font=font,fill='#e8c052');sheet.paste(Image.open(out/f'f{f:04}.jpg'),(x,y+56));manifest.append(dict(frame=f,seconds=f/30,label=label,file=str((out/f'f{f:04}.jpg').relative_to(W))))
with (W/'research/metrics/v52_q013_n16_sheet.jpg').open('xb') as o:sheet.save(o,format='JPEG',quality=95,subsampling=0)
save(W/'research/metrics/v52_q013_n16_sheet_frames.json',manifest)
grid=Image.new('RGB',(1080,2*1010),(16,20,25));draw=ImageDraw.Draw(grid)
for i,f in enumerate([200,260]):
 for j,lab in enumerate(['BEFORE #13','AFTER #16']):
  draw.text((j*540+12,i*1010+8),f'f{f} | {lab}',font=font,fill='white');grid.paste(stills[f][j].resize((540,960)),(j*540,i*1010+45))
with (S/'before_after.jpg').open('xb') as o:grid.save(o,format='JPEG',quality=95,subsampling=0)
covera=np.asarray(Image.open(W/'upload/cover_v52_q013.jpg')).astype(float);coverb=np.asarray(Image.open(W/'upload/cover_v52_q013_n16.jpg')).astype(float);mask=np.ones(covera.shape[:2],bool);mask[184:256,304:784]=False;mse=np.square(covera[mask]-coverb[mask]).mean();cpsnr=float(10*np.log10(255**2/mse)) if mse else None;assert cpsnr is None or cpsnr>=45
r=dict(frame_count=N,checks=checks,container_duration=[a['format']['duration'],b['format']['duration']],audio=dict(stream_md5_before=ma,stream_md5_after=mb,stream_identical=ma==mb,decoded_pcm_md5_before=pa,decoded_pcm_md5_after=pb,pcm_identical=pa==pb),psnr=dict(method='Decoded RGB24 per-frame MSE over every pixel outside active changed rectangles; zero-based frame index.',regions_xyxy=boxes,badge_frames=[61,N-46],end_text_frames=[N-45,N-1],changed_panels_frames=[139,328],minimum_db=m[1],minimum_frame=m[0],all_frames_ge_45_db=all(x[1]>=45 for x in rows)),art_coverage=dict(pass_=True,frames_checked=len(art),minimum_changed_art_pixels=min(r['changed_art_pixels'] for r in art),per_frame=art),cover_psnr_outside_badge=cpsnr,sheet='research/metrics/v52_q013_n16_sheet.jpg')
save(S/'comparison.json',r);print(json.dumps({k:v for k,v in r.items() if k!='art_coverage'},indent=2),flush=True)
