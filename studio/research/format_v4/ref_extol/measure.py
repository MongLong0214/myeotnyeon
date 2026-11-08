from analyze import *
from scipy import signal
import soundfile as sf

def sino(n):
 n=int(n)
 if n==0:return '영'
 if n>=10000:return sino(n//10000)+'만'+(sino(n%10000) if n%10000 else '')
 out=''
 for base,unit in [(1000,'천'),(100,'백'),(10,'십'),(1,'')]:
  a,n=divmod(n,base)
  if a:out+=('' if a==1 and base>1 else '일이삼사오육칠팔구'[a-1])+unit
 return out
def syll(text):
 text=re.sub(r'(\d+)\.(\d+)',lambda m:sino(m[1])+'점'+''.join(sino(n) for n in m[2]),text)
 text=re.sub(r'(?i)cm', '센티미터', text);text=re.sub(r'(?i)km', '킬로미터', text);text=re.sub(r'(?i)kg', '킬로그램', text);text=re.sub(r'(?i)IMF', '아이엠에프', text);text=re.sub(r'(?i)(?<=\d)m', '미터', text)
 text=re.sub(r'(\d+)(명|개|살)',lambda m:({'1':'한','2':'두','3':'세','4':'네','5':'다섯','6':'여섯','7':'일곱','8':'여덟','9':'아홉','10':'열'}.get(m[1],sino(m[1]))+m[2]),text)
 text=re.sub(r'\d+',lambda m:sino(m[0]),text)
 return len(re.findall('[가-힣]',text))
def audio(k):
 d=R/k;m=meta(k);wav=d/'analysis_audio_stereo.wav'
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(VIDEOS[k]),'-vn','-ar','16000','-ac','2',str(wav)],check=True)
 y,sr=sf.read(wav);mono=y.mean(axis=1);side=(y[:,0]-y[:,1])/2
 # 10ms energy and spectral flux; onset means transient, not proof of SFX.
 f,t,z=signal.stft(mono,sr,nperseg=400,noverlap=240);mag=np.abs(z)
 flux=np.maximum(0,np.diff(mag,axis=1)).sum(axis=0);flux=np.r_[0,flux]
 logenergy=20*np.log10(np.maximum(np.sqrt(np.mean(np.lib.stride_tricks.sliding_window_view(mono,400)[::160]**2,axis=1)),1e-9))
 med=signal.medfilt(flux,51);dev=signal.medfilt(np.abs(flux-med),51)+1e-7
 score=(flux-med)/dev
 onset,_=find_peaks(score,height=6,distance=10,prominence=3)
 onset=onset[flux[onset]>np.percentile(flux,60)]
 words=list(csv.DictReader((d/'words.csv').open()));words=[{**w,'start':float(w['start']),'end':float(w['end'])} for w in words if float(w['end'])>float(w['start'])]
 starts=np.array([w['start'] for w in words]);ends=np.array([w['end'] for w in words]);dur=m['duration']
 gaps=[{'start_s':a['end'],'end_s':b['start'],'duration_s':b['start']-a['end'],'method':'ASR non-word gap; not acoustic silence proof'} for a,b in zip(words,words[1:]) if b['start']-a['end']>.2]
 csvwrite(d/'pauses.csv',gaps)
 # WebRTC VAD on the mixed audio for acoustic speech/no-speech intervals, music can contaminate.
 import webrtcvad
 vad=webrtcvad.Vad(2);step=320;pcm=(np.clip(mono,-1,1)*32767).astype('<i2');flags=[]
 for i in range(0,len(pcm)-step,step):flags.append(vad.is_speech(pcm[i:i+step].tobytes(),sr))
 vf=np.array(flags);runs=[];st=None
 for i,v in enumerate(np.r_[vf,True]):
  if not v and st is None:st=i
  elif v and st is not None:
   if (i-st)*.02>.2:runs.append({'start_s':st*.02,'end_s':i*.02,'duration_s':(i-st)*.02})
   st=None
 csvwrite(d/'acoustic_pauses.csv',runs)
 windows=[]
 for a in np.arange(0,dur,30):
  b=min(a+30,dur);ws=[w for w in words if w['end']>a and w['start']<b];count=sum(syll(w['word'])*max(0,min(b,w['end'])-max(a,w['start']))/(w['end']-w['start']) for w in ws)
  pause=sum(max(0,min(b,g['end_s'])-max(a,g['start_s'])) for g in gaps)
  windows.append({'start_s':a,'end_s':b,'syllables':count,'syllables_per_timeline_s':count/(b-a),'syllables_per_phrase_s':count/max(.01,b-a-pause),'asr_pause_s':pause})
 csvwrite(d/'narration_30s.csv',windows)
 # RMS measurements in speech and non-speech windows. No stem separation asserted.
 def rms(a):return float(20*np.log10(max(1e-9,np.sqrt(np.mean(a*a))))) if len(a) else None
 speech=np.zeros(len(mono),bool)
 for w in words:speech[round(w['start']*sr):round(w['end']*sr)]=True
 ns=~speech
 total=sum(syll(w['word']) for w in words);span=words[-1]['end']-words[0]['start'];paused=sum(g['duration_s'] for g in gaps)
 aud={'syllables_normalized_estimate':total,'syllable_method':'Hangul blocks; Arabic numerals expanded to Korean readings; ASR/counting uncertainty retained','syllables_per_timeline_s':total/dur,'syllables_per_phrase_s':total/(span-paused),'asr_pause_count_gt_0_2':len(gaps),'asr_pause_median_s':float(np.median([g['duration_s'] for g in gaps])) if gaps else None,'asr_pause_total_s':paused,'vad_pause_count_gt_0_2':len(runs),'vad_pause_median_s':float(np.median([g['duration_s'] for g in runs])) if runs else None,'mixed_speech_rms_dbfs':rms(mono[speech]),'mixed_nonword_rms_dbfs':rms(mono[ns]),'side_rms_dbfs':rms(side),'side_speech_rms_dbfs':rms(side[speech]),'side_nonword_rms_dbfs':rms(side[ns]),'bed_to_speech_proxy_db':rms(mono[ns])-rms(mono[speech]),'bed_to_speech_proxy_warning':'nonword mixture vs word mixture; includes ambience/SFX, not isolated music vs narration loudness','audio_onset_count':len(onset)}
 dump(d/'audio_summary.json',aud)
 csvwrite(d/'audio_onsets.csv',[{'time_s':float(t[i]),'robust_flux_score':float(score[i]),'flux':float(flux[i]),'speech_overlap':bool(any(w['start']<=t[i]<=w['end'] for w in words))} for i in onset])
 csvwrite(d/'audio_curve.csv',[{'time_s':float(tt),'spectral_flux':float(flux[i]),'robust_score':float(score[i])} for i,tt in enumerate(t)])
 print(k,aud,flush=True)

def thumbnails(k):
 d=R/k;m=meta(k);cap=cv2.VideoCapture(str(R/'tmp'/f'{k}_proxy.mp4'));fps=m['fps'];rows=json.loads((d/'reviewed.json').read_text());starts=[0]+[r['frame'] for r in rows if r['keep']];ends=starts[1:]+[m['frames']]
 for st in range(0,len(starts),30):
  sheet=Image.new('RGB',(1200,((min(30,len(starts)-st)+4)//5)*159));dr=ImageDraw.Draw(sheet)
  for j,(a,b) in enumerate(zip(starts[st:st+30],ends[st:st+30])):
   x=j%5*240;y=j//5*159;sheet.paste(imageframe(cap,round((a+b)/2),(240,135)),(x,y+24));dr.text((x+2,y+4),f'S{st+j+1:03} {a/fps:.2f}-{b/fps:.2f}',font=ImageFont.truetype(FONT,13),fill='white')
  sheet.save(d/f'shots_{st//30+1:02}.jpg',quality=88)
 cap.release()

def flow(k):
 d=R/k;m=meta(k);fps=m['fps'];review=json.loads((d/'reviewed.json').read_text());rows=[r for r in review if r['keep']];starts=[0]+[r['frame'] for r in rows];ends=starts[1:]+[m['frames']]
 cap=cv2.VideoCapture(str(R/'tmp'/f'{k}_proxy.mp4'));out=[]
 for si,(a,b) in enumerate(zip(starts,ends)):
  vals=[];scales=[];dxs=[];dys=[];inliers=[]
  for pos in np.linspace(a+max(2,round(.15*fps)),b-1-max(2,round(.15*fps)),min(12,max(1,int((b-a)/fps*3)))):
   f0=int(pos);f1=min(b-2,f0+max(1,round(.2*fps)))
   if f1<=f0:continue
   cap.set(cv2.CAP_PROP_POS_FRAMES,f0);ok,im0=cap.read();cap.set(cv2.CAP_PROP_POS_FRAMES,f1);ok1,im1=cap.read()
   if not ok or not ok1:continue
   g0=cv2.cvtColor(cv2.resize(im0,(320,180)),cv2.COLOR_BGR2GRAY)[:150];g1=cv2.cvtColor(cv2.resize(im1,(320,180)),cv2.COLOR_BGR2GRAY)[:150]
   dt=(f1-f0)/fps;fl=cv2.calcOpticalFlowFarneback(g0,g1,None,.5,3,15,3,5,1.2,0);mag=np.linalg.norm(fl,axis=2);vals.append(float(mag.mean()/dt));dxs.append(float(np.median(fl[:,:,0])/dt));dys.append(float(np.median(fl[:,:,1])/dt))
   pts=cv2.goodFeaturesToTrack(g0,500,.01,6)
   if pts is not None and len(pts)>8:
    p1,st,err=cv2.calcOpticalFlowPyrLK(g0,g1,pts,None);q=st.ravel()==1
    if q.sum()>8:
     mat,ins=cv2.estimateAffinePartial2D(pts[q],p1[q],method=cv2.RANSAC,ransacReprojThreshold=1.5)
     if mat is not None:scales.append((math.hypot(mat[0,0],mat[1,0])-1)/dt*100);inliers.append(float(ins.mean()))
  mean=float(np.mean(vals)) if vals else 0;dx=float(np.median(dxs)) if dxs else 0;dy=float(np.median(dys)) if dys else 0;scale=float(np.median(scales)) if scales else 0
  if abs(scale)>.25:move='push-in' if scale>0 else 'pull-out'
  elif math.hypot(dx,dy)>.7:move='pan' if abs(dx)>abs(dy) else 'tilt'
  elif mean>3:move='parallax'
  else:move='static'
  out.append({'index':si+1,'start_frame':a,'end_frame':b,'start_s':a/fps,'end_s':b/fps,'duration_s':(b-a)/fps,'camera_move':move,'flow_mean_px_per_s_at_320w':mean,'flow_median_dx_px_per_s':dx,'flow_median_dy_px_per_s':dy,'flow_direction_degrees':math.degrees(math.atan2(dy,dx)),'scale_change_pct_per_s':scale,'scale_change_pct_shot_estimate':((1+scale/100)**((b-a)/fps)-1)*100,'affine_inlier_fraction':float(np.mean(inliers)) if inliers else None,'flow_pair_count':len(vals)})
  if si%20==0:print(k,'FLOW',si,flush=True)
 csvwrite(d/'flow.csv',out);cap.release()
if __name__=='__main__':
 for k in (sys.argv[2:] or list(VIDEOS)):globals()[sys.argv[1]](k)
