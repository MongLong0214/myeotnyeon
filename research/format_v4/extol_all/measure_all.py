import os,sys,json,csv,math,subprocess,time,hashlib,shutil,concurrent.futures,importlib.util
from pathlib import Path
import numpy as np,cv2
from PIL import Image,ImageDraw,ImageFont
from scipy.signal import find_peaks
from scenedetect import FrameTimecode
from scenedetect.detectors import ContentDetector,AdaptiveDetector
cv2.setNumThreads(1)
_original_capture=cv2.VideoCapture
def single_thread_capture(path):return _original_capture(path,cv2.CAP_FFMPEG,[cv2.CAP_PROP_N_THREADS,1])
cv2.VideoCapture=single_thread_capture
R=Path(__file__).resolve().parent;os.environ['TMPDIR']=str(R/'tmp')
FONT='/System/Library/Fonts/Supplemental/Arial.ttf'
INV=json.loads((R/'inventory.json').read_text());LONG=INV['long'];SHORT=INV['short']
def dump(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2))
def csvout(p,rows):
 if not rows:return
 with p.open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def frame(cap,n,size):
 cap.set(cv2.CAP_PROP_POS_FRAMES,max(0,int(n)));ok,x=cap.read()
 return Image.fromarray(cv2.cvtColor(cv2.resize(x,size),cv2.COLOR_BGR2RGB)) if ok else Image.new('RGB',size)
def sheet_frames(cap,times,fps,path,cols=4,size=(320,180),labels=None):
 w,h=size;canvas=Image.new('RGB',(w*cols,(h+22)*math.ceil(len(times)/cols)),(15,15,15));dr=ImageDraw.Draw(canvas)
 for i,t in enumerate(times):
  x=i%cols*w;y=i//cols*(h+22);canvas.paste(frame(cap,round(t*fps),size),(x,y+22));dr.text((x+3,y+3),labels[i] if labels else f'{t:.3f}s',font=ImageFont.truetype(FONT,12),fill='white')
 canvas.save(path,quality=87)
def measure(vid):
 d=R/vid;d.mkdir(exist_ok=True)
 while not (d/'metadata.json').exists() or not (d/'media.mp4').exists():
  if (d/'unavailable.json').exists():return
  time.sleep(2)
 if (d/'visual_ready.json').exists():return
 p=d/'media.mp4';pr=json.loads(subprocess.check_output(['ffprobe','-v','quiet','-show_streams','-show_format','-of','json',str(p)]));v=next(x for x in pr['streams'] if x['codec_type']=='video');fps=eval(v['avg_frame_rate']);dur=float(pr['format']['duration']);n=int(v.get('nb_frames',round(dur*fps)))
 dump(d/'source_media.json',{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'fps':fps,'frames':n,'duration_s':n/fps,'width':v['width'],'height':v['height'],'probe':pr})
 # Uniform native-frame proxy, no temporal subsampling.
 proxy=d/'analysis_proxy.mp4'
 targetw=480;targeth=round(targetw*v['height']/v['width']/2)*2
 if not proxy.exists():subprocess.run(['ffmpeg','-v','error','-y','-threads','2','-i',str(p),'-vf',f'scale={targetw}:{targeth}','-an','-c:v','libx264','-preset','ultrafast','-crf','18','-g','15','-threads','2',str(proxy)],check=True)
 dump(d/'media.json',{'fps':fps,'frames':n,'duration':n/fps,'width':v['width'],'height':v['height'],'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
 if (d/'candidates.json').exists() and (d/'frame_curves.npz').exists():
  arr=np.load(d/'frame_curves.npz')['data'];candidates=json.loads((d/'candidates.json').read_text());votes=json.loads((d/'detector_votes.json').read_text())
 else:
  cap=cv2.VideoCapture(str(proxy));votes={'content':[],'adaptive':[]};det={'content':ContentDetector(threshold=20,min_scene_len=4),'adaptive':AdaptiveDetector(adaptive_threshold=2.5,min_scene_len=4,min_content_val=9)}
  rows=[];prev=None;prevhist=None;idx=0
  while True:
   ok,im=cap.read()
   if not ok:break
   im=cv2.resize(im,(480,270));g=cv2.cvtColor(im,cv2.COLOR_BGR2GRAY);tc=FrameTimecode(idx,fps=fps)
   for name,x in det.items():votes[name].extend(t.get_frames() for t in x.process_frame(tc,im))
   hist=cv2.calcHist([im],[0,1,2],None,[8,8,8],[0,256]*3);cv2.normalize(hist,hist)
   rows.append([idx,idx/fps,float(np.abs(g.astype(float)-prev).mean()) if prev is not None else 0,float(cv2.compareHist(prevhist,hist,cv2.HISTCMP_BHATTACHARYYA)) if prevhist is not None else 0,float(g.mean()),float((g<10).mean()),float((g>240).mean()),float(det['content']._frame_score or 0)])
   prev=g.astype(float);prevhist=hist;idx+=1
  cap.release();arr=np.array(rows);np.savez_compressed(d/'frame_curves.npz',data=arr)
  with (d/'scdet.log').open('w') as log:subprocess.run(['ffmpeg','-hide_banner','-threads','2','-i',str(proxy),'-vf','scale=480:270,scdet=threshold=5,metadata=print:file='+str(d/'scdet_metadata.txt'),'-an','-f','null','-'],stdout=log,stderr=log,check=True)
  ff=[]
  for line in (d/'scdet_metadata.txt').read_text().splitlines():
   if 'lavfi.scd.time=' in line:ff.append(round(float(line.split('=')[1])*fps))
  votes['ffmpeg']=ff;dump(d/'detector_votes.json',votes)
  # Independent detector union; retain motion candidates for review, no statistical ground truth claimed.
  win=max(3,round(fps*.5));smooth=np.convolve(arr[:,2],np.ones(win)/win,'same');peaks,_=find_peaks(smooth,height=max(1.3,float(np.percentile(smooth,75))),prominence=1.1,distance=win)
  candidates=[]
  for fr in sorted(set(sum(votes.values(),[])+peaks.tolist())):
   if fr<3 or fr>=len(arr)-3:continue
   sources=[name for name,fs in votes.items() if any(abs(fr-x)<=2 for x in fs)]
   if any(abs(fr-x)<=win//2 for x in peaks):sources.append('diff_0.5s')
   if candidates and fr-candidates[-1]['frame']<=3:
    c=candidates[-1];c['sources']=sorted(set(c['sources']+sources))
    if arr[fr,2]>c['diff']:c.update(frame=fr,time_s=fr/fps,diff=float(arr[fr,2]),hist=float(arr[fr,3]))
    continue
   candidates.append({'candidate':len(candidates)+1,'frame':fr,'time_s':fr/fps,'sources':sources,'diff':float(arr[fr,2]),'hist':float(arr[fr,3])})
  dump(d/'candidates.json',candidates)
 reuse={'w_LJ_GQObic':R.parent/'ref_extol/ref/cuts.csv','OwQm8ZIZfiQ':R.parent/'ref_extol2/cuts.csv'}.get(vid)
 if reuse and reuse.exists():
  old=list(csv.DictReader(reuse.open()));keep=[int(float(x.get('frame',x.get('start_frame',round(float(x.get('start_s','0'))*fps))))) for x in old]
  # cuts.csv rows may describe shots from 0; read authoritative shot starts instead.
  sp=reuse.parent/'shots.csv'
  if sp.exists():keep=[int(float(x['start_frame'])) for x in list(csv.DictReader(sp.open()))[1:]]
  keep=[fr for fr in keep if fr>0];source='reused frame-accurate visual review'
 else:
  keep=[]
  for c in candidates:
   fr=c['frame'];nv=len(set(c['sources'])&{'content','adaptive','ffmpeg'});h=c['hist'];diff=c['diff']
   if (nv>=2 and (h>.12 or diff>14)) or (h>.42 and diff>9) or ('adaptive' in c['sources'] and h>.25 and diff>8):keep.append(fr)
  source='detector ensemble; sampled boundary visual review; not exhaustive manual truth'
 keep=sorted(set(keep));bound=[]
 for j,fr in enumerate(keep):
  a=max(0,fr-round(.5*fps));b=min(len(arr),fr+round(.5*fps));q=arr[a:b];center=arr[fr];near=q[:,2];bg=np.median(near);strong=np.where(near>max(4,bg*2))[0];width=int(strong[-1]-strong[0]+1) if len(strong) else 1
  dark=float(q[:,5].max());white=float(q[:,6].max());typ='hard';length=1;conf=.75
  if white>.6 and width>1:typ='flash';length=min(width,round(.5*fps));conf=.55
  elif dark>.85 and width>2:typ='fade-black';length=min(width,round(.5*fps));conf=.5
  elif width>=4 and center[3]<.4:typ='dissolve';length=min(width,round(.5*fps));conf=.45
  bound.append({'index':j+1,'frame':fr,'time_s':fr/fps,'transition_type':typ,'transition_frames_estimate':length,'transition_duration_s_estimate':length/fps,'confidence':conf,'boundary_method':source,'visual_confirmation':'pending sampled visual review'})
 csvout(d/'boundaries.csv',bound);dump(d/'reviewed.json',[{'frame':fr,'keep':True} for fr in keep])
 starts=[0]+keep;ends=keep+[n];cuts=[{'index':i+1,'start_frame':a,'end_frame':b,'start_s':a/fps,'end_s':b/fps,'duration_s':(b-a)/fps,'transition_type':('start' if i==0 else bound[i-1]['transition_type']),'confidence':(1 if i==0 else bound[i-1]['confidence'])} for i,(a,b) in enumerate(zip(starts,ends))];csvout(d/'cuts.csv',cuts)
 cap=cv2.VideoCapture(str(proxy));size=(240,135) if vid in LONG else (135,240)
 for st in range(0,len(cuts),36):
  cs=cuts[st:st+36];sheet_frames(cap,[(x['start_s']+x['end_s'])/2 for x in cs],fps,d/f'shots_{st//36+1:02}.jpg',6,size,[f"S{x['index']:03} {x['start_s']:.2f}-{x['end_s']:.2f}" for x in cs])
 # Evidence strips: all kept boundaries, plus sample rejected candidates in a separate set.
 for st in range(0,len(bound),12):
  group=bound[st:st+12];tilew,tileh=(180,102) if vid in LONG else (80,142);canvas=Image.new('RGB',(tilew*8,(tileh+22)*len(group)));dr=ImageDraw.Draw(canvas)
  for i,c in enumerate(group):
   y=i*(tileh+22);dr.text((3,y+2),f"B{c['index']:03} {c['time_s']:.3f}s {c['transition_type']}",font=ImageFont.truetype(FONT,12),fill='white')
   for j,off in enumerate([-round(.3*fps),-3,-2,-1,0,1,2,round(.3*fps)]):canvas.paste(frame(cap,c['frame']+off,(tilew,tileh)),(j*tilew,y+22))
  canvas.save(d/f'boundaries_{st//12+1:02}.jpg',quality=86)
 dur=n/fps;keytimes=np.linspace(.4,max(.4,dur-1),12).tolist();sheet_frames(cap,keytimes,fps,d/'frames_key.jpg',4,(320,180) if vid in LONG else (180,320))
 if vid in LONG:
  for a in [0,20,40]:sheet_frames(cap,np.arange(a,a+20,1).tolist(),fps,d/f'first60_{a:02}.jpg',5,(240,135))
 else:sheet_frames(cap,[0,.5,1,1.5,2,2.5,3,max(0,dur-1)],fps,d/'hook_and_ending.jpg',4,(180,320))
 # Measured palette and image texture proxies in sampled frames (not claims about effect settings).
 visual=[]
 for t in np.arange(.5,dur,2):
  im=np.array(frame(cap,t*fps,(320,180)));g=cv2.cvtColor(im,cv2.COLOR_RGB2GRAY);small=cv2.resize(im,(80,45));pixels=small.reshape(-1,3).astype(np.float32);cv2.setRNGSeed(1);_,lab,cent=cv2.kmeans(pixels,4,None,(cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER,12,.5),1,cv2.KMEANS_PP_CENTERS);counts=np.bincount(lab.ravel(),minlength=4);order=np.argsort(-counts);hsv=cv2.cvtColor(im,cv2.COLOR_RGB2HSV)
  residual=g.astype(float)-cv2.GaussianBlur(g,(3,3),0).astype(float);corners=np.r_[g[:30,:50].ravel(),g[:30,-50:].ravel(),g[-30:,:50].ravel(),g[-30:,-50:].ravel()];center=g[60:120,100:220]
  visual.append({'time_s':float(t),'dominant_hex':'#'+''.join(f'{int(x):02x}' for x in cent[order[0]]),'palette_hex':';'.join('#'+''.join(f'{int(x):02x}' for x in cent[j]) for j in order),'palette_shares':';'.join(str(round(counts[j]/len(pixels),4)) for j in order),'mean_luma':float(g.mean()),'mean_saturation_0_255':float(hsv[:,:,1].mean()),'dark_pixel_share_luma_lt40':float((g<40).mean()),'corner_minus_center_luma':float(corners.mean()-center.mean()),'high_frequency_residual_std':float(residual.std()),'laplacian_variance':float(cv2.Laplacian(g,cv2.CV_64F).var())})
 csvout(d/'visual_samples.csv',visual);cap.release();dump(d/'visual_ready.json',{'shot_count_initial':len(cuts),'duration_s':dur,'fps':fps,'source':source,'measure_pixels':'palette at320x180; black bars/subtitles included; corner darkness and residual texture not isolated vignette/grain'})
 print(vid,'VISUAL',len(cuts),len(candidates),flush=True)
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:list(ex.map(measure,LONG+SHORT))
