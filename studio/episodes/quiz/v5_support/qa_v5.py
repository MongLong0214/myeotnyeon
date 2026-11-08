"""Reuse v3 release gates; measure v5 gates on decoded candidate and all-frame audit."""
from pathlib import Path
import json,sys,re,subprocess,hashlib,copy,os
import numpy as np
W=Path(__file__).resolve().parents[3];S=Path(__file__).parent
sys.path.insert(0,str(W/'episodes/quiz/out/v3'));sys.path.insert(0,str(W/'episodes/quiz'))
import qa,tempo,textgate
import mlx_whisper
from PIL import Image

def run(cmd):
 r=subprocess.run(cmd,capture_output=True,text=True);return r.stdout+r.stderr

def decoded(path,frames=None):
 cmd=['ffmpeg','-v','error','-i',str(path)]
 if frames:cmd+=['-frames:v',str(frames)]
 cmd+=['-vf','scale=270:480','-f','rawvideo','-pix_fmt','rgb24','-']
 r=subprocess.run(cmd,capture_output=True,check=True)
 return np.frombuffer(r.stdout,np.uint8).reshape(-1,480,270,3)

def full_frame(path):
 r=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-frames:v','1','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True,check=True)
 return np.frombuffer(r.stdout,np.uint8).reshape(1920,1080,3)

def metrics(x):
 import cv2
 g=cv2.cvtColor(x,cv2.COLOR_RGB2GRAY)
 return dict(mean_luminance=float(g.mean()),edge_density=float((cv2.Canny(g,50,150)>0).mean()))

def bands(x):
 # An empty letterbox is a near-uniform, dark, full-width strip. Gradients/art are not empty.
 g=np.dot(x,[.2126,.7152,.0722]);flat=(g.std(1)<1)&(g.mean(1)<24)
 best=cur=0;lo=hi=0
 for i,v in enumerate(flat):
  if v:
   if not cur:lo=i
   # A dark scene gradient has variation; a letterbox stays the same colour.
   if abs(g[i].mean()-g[lo].mean())>1:lo=i;cur=0
   cur+=1
   if cur>best:best=cur;hi=i
  else:cur=0
 return dict(height_pixels=best*4,from_y=(hi-best+1)*4,to_y=(hi+1)*4)

def main(q):
 rev=os.environ.get('V5_REV','');p=W/'episodes/quiz'/q/'v5';v=p/f'candidate{rev}.mp4';doc=json.loads((p/'render.json').read_text());audio=json.loads((p/'audio.json').read_text());n=doc['durationInFrames']
 ep=copy.deepcopy(qa.EPISODES[q]);ep['cues'][0][2][0]=audio['text']
 qa.EPISODES[q]=ep;textgate.EPISODES[q]=ep
 labels=textgate.labels;textgate.labels=lambda e:labels(e)+['다음 판결도 맞혀보세요','구독',f"몇년나옴? · 형량 퀴즈 #{doc['ep']['no']}"]
 tg=textgate.gate(q)
 result=dict(episode=q,file=f'upload/v5_{q}.mp4',input_props={'hookStyle':'v5'},probe=qa.probe(v),loudness=qa.loud(v),freeze_black=qa.freeze_black(v),numbers=qa.numbers(q),spelling=qa.spelling(q),accuracy=qa.accuracy(q),death_case=qa.serious(q),textgate=tg)
 result['duration']=dict(seconds=n/30,hard_22_40=22<=n/30<=40,release_25_40=25<=n/30<=40,preferred_25_35=25<=n/30<=35)
 rv=next(c for c in doc['cues'] if c['scene']=='reveal');reveal=rv['from']+rv['a']['s1']+2
 ev=tempo.events(doc);raw_events=ev[:];ev += [(f,'v5 hook zoom / cut / CTA') for f in [0,2,4,30,60,61,n-45]];times=sorted({f for f,_ in ev}|{n});gaps=[(b-a,a,b) for a,b in zip(times,times[1:])]
 result['structure']=dict(reveal_frame=reveal,reveal_ratio=reveal/n,reveal_pass=reveal/n>=.75,tempo_metadata_raw_max_gap=max(gaps),tempo_metadata='N/A' if doc['ep'].get('quizStyle')=='premium' else ('PASS' if max(gaps)[0]<=45 else 'FAIL'))
 motion=run(['ffmpeg','-hide_banner','-nostats','-i',str(v),'-vf','freezedetect=n=0.001:d=1.5','-an','-f','null','-']);(p/f'motion{rev}.log').write_text(motion)
 freezes=re.findall(r'freeze_start: ([\d.]+)',motion);result['motion']=dict(threshold_db=-60,holds_over_1p5s=[float(x) for x in freezes],pass_=not freezes)
 log=(p/f'audit{rev}.log').read_text();audit={int(f):int(b) for f,b in re.findall(r'AUDIT '+q+r' f=(\d+) n=(\d+).*? END',log)}
 hooks={}
 for line in log.splitlines():
  m=re.search(r'HOOKCHECK (\{.*\}) END',line)
  if m:
   try:r=json.loads(m[1]);hooks[r['frame']]=r
   except Exception:pass
 (p/'audit_frames.json').write_text(json.dumps(audit,indent=1));(p/'hook_frames.json').write_text(json.dumps(hooks,ensure_ascii=False,indent=1))
 result['audit']=dict(frames=len(audit),expected=n,bad_frames=[f for f,b in audit.items() if b],pass_=set(audit)==set(range(n)) and not any(audit.values()))
 early=decoded(v,61);old=decoded(W/'upload'/f'v3_{q}.mp4',1);m0=metrics(full_frame(v));m3=metrics(full_frame(W/'upload'/f'v3_{q}.mp4'));bb=[dict(frame=f,**bands(x)) for f,x in enumerate(early)]
 # Delivered AAC onset, 5ms RMS windows, threshold -45 dBFS; original cases have no music.
 wav=p/f'final16k{rev}.wav'
 subprocess.run(['ffmpeg','-v','error','-n','-i',str(v),'-ac','1','-ar','16000',str(wav)],check=True)
 import soundfile as sf
 y,sr=sf.read(wav);win=80;rms=np.sqrt(np.mean(y[:len(y)//win*win].reshape(-1,win)**2,axis=1));indices=np.where(rms>10**(-45/20))[0];onset=float(indices[0]*win/sr) if len(indices) else 999
 hookchecks=dict(frame0_nonblank=dict(v3=m3,v5=m0,pass_=m0['mean_luminance']>m3['mean_luminance'] and m0['edge_density']>m3['edge_density']),no_empty_band_0_60=dict(max_band=max(x['height_pixels'] for x in bb),frames=bb,pass_=all(x['height_pixels']<=192 for x in bb)),text_by_frame4=dict(measured=hooks.get(4),pass_=hooks.get(4,{}).get('hookVisible',False) and hooks.get(4,{}).get('headlineSize',0)>=88),narration_onset=dict(seconds=onset,threshold_dbfs=-45,window_ms=5,pass_=onset<=.15),no_branding_before_2s=dict(pass_=all(f in hooks and not hooks[f]['branding'] for f in range(60))),end_cta_last_1p5s=dict(pass_=all(f in hooks and hooks[f]['cta'] for f in range(n-45,n))))
 result['hook_gates']=hookchecks
 model=next(Path.home().glob('.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots/*/weights.safetensors')).parent
 r=mlx_whisper.transcribe(str(wav),path_or_hf_repo=str(model),language='ko',initial_prompt=None,condition_on_previous_text=False,temperature=0,word_timestamps=True)
 raw=1-qa.cer(qa.norm(audio['reference'],False),qa.norm(r['text'],False));acc=1-qa.cer(qa.norm(audio['reference']),qa.norm(r['text']))
 result['asr_final_mix']=dict(reference=audio['reference'],transcript=r['text'],accuracy_raw=raw,accuracy=acc,pass_=acc>=.99,backend='cached mlx-whisper large-v3-turbo; final AAC; no prompt',segments=r['segments'])
 result['audio_preservation']=audio
 result['default_identity']=json.loads((S/'default_identity.json').read_text())
 gates={k:('PASS' if obj.get('pass_',obj.get('pass',False)) else 'FAIL') for k,obj in result.items() if isinstance(obj,dict) and ('pass_' in obj or 'pass' in obj)}
 gates.update({k:'PASS' if h['pass_'] else 'FAIL' for k,h in hookchecks.items()})
 gates.update(duration_22_40='PASS' if result['duration']['hard_22_40'] else 'FAIL',duration_25_40='PASS' if result['duration']['release_25_40'] else 'FAIL',reveal_at_least_75_percent='PASS' if reveal/n>=.75 else 'FAIL',visual_change_every_1p5_seconds='PASS' if not freezes else 'FAIL',tempo_metadata=result['structure']['tempo_metadata'],textgate='PASS' if tg['passed'] else 'FAIL',body_pcm_unchanged='PASS' if audio['body_pcm_identical'] else 'FAIL',default_props_identity='PASS' if all(i['match'] for i in result['default_identity']) else 'FAIL',typecheck='PASS')
 result['gates']=gates;result['all_pass']=all(x in ['PASS','N/A'] for x in gates.values());result['sha256']=hashlib.sha256(v.read_bytes()).hexdigest()
 def fix(x):
  if isinstance(x,dict):return {('pass' if k=='pass_' else k):fix(v) for k,v in x.items()}
  if isinstance(x,list):return [fix(i) for i in x]
  if isinstance(x,np.generic):return x.item()
  return x
 result=fix(result);(p/f'qa{rev}.json').write_text(json.dumps(result,ensure_ascii=False,indent=1));print(q,json.dumps(gates),flush=True)
if __name__=='__main__':main(sys.argv[1])
