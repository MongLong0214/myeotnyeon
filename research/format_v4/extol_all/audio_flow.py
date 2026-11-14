import sys,os,json,csv,time,subprocess,concurrent.futures,importlib.util
from pathlib import Path
import numpy as np
import soundfile as sf
from scipy import signal
R=Path(__file__).resolve().parent;os.environ['TMPDIR']=str(R/'tmp');sys.path.insert(0,str(R.parent/'ref_extol'))
import analyze,measure
import cv2
cv2.setNumThreads(1)
_original_capture=cv2.VideoCapture
def single_thread_capture(path):return _original_capture(path,cv2.CAP_FFMPEG,[cv2.CAP_PROP_N_THREADS,1])
cv2.VideoCapture=single_thread_capture
inv=json.loads((R/'inventory.json').read_text());videos={v:R/v/'media.mp4' for v in inv['long']+inv['short']}
analyze.R=R;analyze.VIDEOS=videos;measure.R=R;measure.VIDEOS=videos

def csvout(p,rows):
 if not rows:return
 with p.open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def db(x):return float(20*np.log10(max(1e-10,np.sqrt(np.mean(x*x))))) if len(x) else None
def audio(vid):
 d=R/vid
 if (d/'audio_complete.json').exists() or (d/'unavailable.json').exists():return
 while not (d/'transcript.internal.json').exists():
  if (d/'unavailable.json').exists():return
  time.sleep(2)
 if not (d/'media.json').exists():
  while not (d/'media.json').exists():time.sleep(2)
 data=json.loads((d/'transcript.internal.json').read_text()); ws=[{'start':w['start'],'end':w['end'],'word':w['word'],'probability':w.get('probability'),'segment':s['id']} for s in data['segments'] for w in s.get('words',[])];csvout(d/'words.csv',ws)
 measure.audio(vid)
 # EBU R128 via ffmpeg loudnorm measurement. Values are of the published mix.
 r=subprocess.run(['ffmpeg','-hide_banner','-threads','2','-i',str(d/'media.mp4'),'-vn','-af','loudnorm=I=-16:TP=-1.5:LRA=11:print_format=json','-f','null','-'],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,text=True)
 text=r.stderr;(d/'lufs.log').write_text(text)
 try:loud=json.loads(text[text.rfind('{'):text.rfind('}')+1])
 except:loud={}
 y,sr=sf.read(d/'analysis_audio_stereo.wav');mono=y.mean(1);side=(y[:,0]-y[:,1])/2;dur=len(mono)/sr
 data=json.loads((d/'transcript.internal.json').read_text());words=[w for s in data['segments'] for w in s.get('words',[]) if w['end']>w['start']]
 mask=np.zeros(len(mono),bool)
 for w in words:mask[max(0,round((w['start']-.06)*sr)):min(len(mask),round((w['end']+.06)*sr))]=True
 rows=[]
 for t in range(int(np.ceil(dur))):
  a=t*sr;b=min(len(mono),(t+1)*sr);m=mask[a:b];chunk=mono[a:b];sc=side[a:b]
  rows.append({'start_s':t,'end_s':min(dur,t+1),'mix_rms_dbfs':db(chunk),'side_rms_dbfs':db(sc),'asr_speech_fraction':float(m.mean()),'nonword_mix_rms_dbfs':db(chunk[~m]),'speech_mix_rms_dbfs':db(chunk[m]),'nonword_energy_present_proxy':bool(m.mean()<.5 and db(chunk)>-50),'note':'side/nonword energy includes music, ambience, SFX and speech leakage; not separated stems'})
 csvout(d/'audio_1s.csv',rows)
 # Cue change candidates based on 3s-window spectral distribution and RMS jump.
 features=[]
 for t in np.arange(0,dur-3,3):
  x=side[int(t*sr):int((t+3)*sr)];f,p=signal.welch(x,sr,nperseg=1024);bands=np.array([p[(f>=a)&(f<b)].sum() for a,b in [(40,200),(200,800),(800,3000),(3000,7500)]]);bands=bands/(bands.sum()+1e-12);features.append((t,db(x),bands))
 cues=[]
 for prev,cur in zip(features,features[1:]):
  dist=float(np.linalg.norm(cur[2]-prev[2]));jump=abs(cur[1]-prev[1])
  if dist>.45 or jump>8:cues.append({'time_s':float(cur[0]),'spectral_distribution_distance':dist,'side_rms_jump_db':jump,'status':'cue-change candidate; neither music identity nor musical edit confirmed'})
 csvout(d/'cue_candidates.csv',cues)
 e=mono[:len(mono)//320*320].reshape(-1,320);energy=20*np.log10(np.maximum(1e-10,np.sqrt((e*e).mean(1))));changes=np.diff(np.r_[False,energy<-60,False].astype(int));starts=np.where(changes==1)[0];ends=np.where(changes==-1)[0];sil=[{'start_s':a*.02,'end_s':b*.02,'duration_s':(b-a)*.02} for a,b in zip(starts,ends) if (b-a)*.02>=.18];csvout(d/'mix_silences.csv',sil)
 s=json.loads((d/'audio_summary.json').read_text());s.update({'integrated_lufs':float(loud['input_i']) if 'input_i' in loud else None,'loudness_range_lu':float(loud['input_lra']) if 'input_lra' in loud else None,'true_peak_dbtp':float(loud['input_tp']) if 'input_tp' in loud else None,'side_energy_present_share_1s_gt_minus50':float(np.mean([r['side_rms_dbfs']>-50 for r in rows])),'music_presence_confirmed':None,'cue_change_candidate_count':len(cues),'mix_silence_count_gt_0_18s_below_minus60':len(sil),'mix_silence_total_s':sum(x['duration_s'] for x in sil)})
 (d/'audio_summary.json').write_text(json.dumps(s,ensure_ascii=False,indent=2));(d/'audio_complete.json').write_text('{}');print(vid,'AUDIO',s['integrated_lufs'],flush=True)
def flow(vid):
 d=R/vid
 if (d/'flow.csv').exists() or (d/'unavailable.json').exists():return
 while not (d/'visual_ready.json').exists():
  if (d/'unavailable.json').exists():return
  time.sleep(2)
 link=R/'tmp'/f'{vid}_proxy.mp4'
 if not link.exists():link.symlink_to(d/'analysis_proxy.mp4')
 measure.flow(vid);print(vid,'FLOW DONE',flush=True)
if __name__=='__main__':
 targets=inv['long'] if sys.argv[1]=='flow' else inv['long']+inv['short']
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:list(ex.map(globals()[sys.argv[1]],targets))
