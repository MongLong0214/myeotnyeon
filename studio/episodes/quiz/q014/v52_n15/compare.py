from pathlib import Path
import subprocess,json,hashlib,math,csv
import numpy as np
from PIL import Image,ImageDraw,ImageFont
W=Path.cwd();S=W/'episodes/quiz/q014/v52_n15';A=W/'upload/v52_q014.mp4';B=W/'upload/v52_q014_n15.mp4'
def probe(p):return json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(p)]))
def md5(p,copy=False):return subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-map','0:a:0','-c:a','copy' if copy else 'pcm_s32le','-f','md5','-']).decode().strip()
a,b=probe(A),probe(B);va=next(s for s in a['streams'] if s['codec_type']=='video');vb=next(s for s in b['streams'] if s['codec_type']=='video')
checks={k:[va.get(k),vb.get(k)] for k in ['nb_read_frames','duration','r_frame_rate','width','height']};assert all(x==y for x,y in checks.values()),checks
ma,mb=md5(A,True),md5(B,True);pa,pb=md5(A),md5(B);assert ma==mb or pa==pb
ps=[subprocess.Popen(['ffmpeg','-v','error','-i',str(v),'-an','-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE) for v in [A,B]]
N=int(va['nb_read_frames']);rows=[];stills={};boxes={'badge':[304,184,784,256],'end_card_text':[128,1280,800,1376]}
for f in range(N):
 xs=[np.frombuffer(p.stdout.read(1080*1920*3),np.uint8).reshape(1920,1080,3) for p in ps]
 d=xs[0].astype(np.float32)-xs[1].astype(np.float32);mask=np.ones((1920,1080),bool)
 if 61<=f<N-45:x0,y0,x1,y1=boxes['badge'];mask[y0:y1,x0:x1]=False
 if f>=N-45:x0,y0,x1,y1=boxes['end_card_text'];mask[y0:y1,x0:x1]=False
 mse=float(np.square(d[mask]).mean());score=10*math.log10(255**2/mse) if mse else float('inf');rows.append((f,score,mse))
 if f in [30,300,883,884,900,928]:
  for label,x in zip(['before','after'],xs):Image.fromarray(x).save(S/f'{label}_f{f:04}.png')
  stills[f]=[Image.fromarray(x.copy()) for x in xs]
for p in ps:assert p.wait()==0
with (S/'per_frame_psnr.csv').open('x') as o:
 c=csv.writer(o);c.writerow(['frame_zero_based','rgb_psnr_db_outside_text_regions','mse']);c.writerows(rows)
m=min(rows,key=lambda x:x[1]);assert m[1]>=45,m
font=ImageFont.truetype(str(W/'production/compositor/public/fonts/Pretendard-Bold.otf'),24)
sheet=Image.new('RGB',(1080,3*1010),(18,22,28));draw=ImageDraw.Draw(sheet)
for i,f in enumerate([30,300,900]):
 for j,label in enumerate(['BEFORE #14','AFTER #15']):
  draw.text((j*540+12,i*1010+8),f'f{f} | {label}',font=font,fill='white');sheet.paste(stills[f][j].resize((540,960)),(j*540,i*1010+45))
sheet.save(S/'before_after.jpg',quality=96)
# Larger text-region comparisons, including the requested hook frame where no badge exists.
crop=Image.new('RGB',(1000,740),(18,22,28));dr=ImageDraw.Draw(crop)
for i,(f,box) in enumerate([(30,boxes['badge']),(300,boxes['badge']),(900,boxes['end_card_text'])]):
 dr.text((10,i*240+8),f'frame {f}: BEFORE (left) / AFTER (right)',font=font,fill='white')
 for j in range(2):
  im=stills[f][j].crop(box);im.thumbnail((480,180));crop.paste(im,(j*500+10,i*240+50))
crop.save(S/'number_crops.jpg',quality=98)
r=dict(frame_count=N,checks=checks,container_duration=[a['format']['duration'],b['format']['duration']],audio=dict(stream_md5_before=ma,stream_md5_after=mb,stream_identical=ma==mb,decoded_pcm_md5_before=pa,decoded_pcm_md5_after=pb,pcm_identical=pa==pb),psnr=dict(method='Decoded RGB24, per-frame MSE over every pixel outside declared text rectangles; zero-based frames; only active text region masked',regions_xyxy=boxes,badge_frames=[61,N-46],end_text_frames=[N-45,N-1],minimum_db=m[1],minimum_frame=m[0],all_frames_ge_45_db=all(x[1]>=45 for x in rows)),stills='episodes/quiz/q014/v52_n15/before_after.jpg')
with (S/'comparison.json').open('x') as o:json.dump(r,o,indent=2)
print(json.dumps(r,indent=2))
