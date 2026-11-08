"""Re-synthesise every unchanged line locally; speech and all cue anchors share one measured clock."""
from pathlib import Path
import os,sys,json,re,math,hashlib,importlib.util,subprocess,copy
import numpy as np,soundfile as sf
from scipy.signal import resample_poly
from supertonic import TTS
W=Path(__file__).resolve().parents[3];PUB=W/'production/compositor/public'
sys.path.insert(0,str(W/'episodes/quiz/out/v3'))
import qa
from align_v51 import normalizer
RATE=float(os.environ.get('V51_RATE','6.5'))

def load(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def compress_pauses(x,sr):
 # 5 ms RMS windows, shorten only established >=150ms quiet runs to 90 ms.
 win=round(sr*.005);n=len(x)//win;rms=np.sqrt(np.mean(x[:n*win].reshape(-1,win)**2,axis=1));quiet=rms<10**(-45/20)
 edges=np.diff(np.r_[False,quiet,False].astype(int));runs=list(zip(np.where(edges==1)[0],np.where(edges==-1)[0]));keep=np.ones(len(x),bool)
 for a,b in runs:
  if b-a>=30:keep[(a+9)*win:(b-9)*win]=False
 return x[keep]

def trim(x,sr):
 win=round(sr*.005);n=len(x)//win;rms=np.sqrt(np.mean(x[:n*win].reshape(-1,win)**2,axis=1));idx=np.where(rms>10**(-45/20))[0]
 if len(idx):x=x[max(0,(idx[0]-4)*win):min(len(x),(idx[-1]+5)*win)]
 return compress_pauses(x,sr)

def main():
 tts=TTS(auto_download=False,intra_op_num_threads=1,inter_op_num_threads=1);style=tts.get_voice_style(voice_name='M1')
 model=next(Path('$HOME/.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots').glob('*/weights.safetensors')).parent
 import mlx_whisper
 for q in sys.argv[1:] or ['q015','q012','q016','q017']:
  base=W/'episodes/quiz'/q;out=base/'v51';out.mkdir(exist_ok=True);na=out/'na';na.mkdir(exist_ok=True)
  spec=importlib.util.spec_from_file_location('tts_episode',base/'tts.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
  norm=normalizer(q)
  old=load(base/'v5/render.json');oldtim=load(base/'timing.json');oldaudio=load(base/'v5/audio.json')
  items=copy.deepcopy(oldtim['items']);items[0]['text']=oldaudio['text'];items[0]['start']=0;items[0]['end']=oldaudio['new_cut_frame']
  for it in items[1:]:it['start']+=oldaudio['delta_frames'];it['end']+=oldaudio['delta_frames']
  index=[]
  for i,it in enumerate(items):
   f=na/f"{it['id']}.wav";record=f.with_suffix('.json');text=it['text'];spoken=mod.tts_text(text);syll=len(re.findall('[가-힣]',spoken))
   if f.exists() and record.exists():index.append(load(record));continue
   speed=1.10;best=None
   for attempt in range(6):
    x,_=tts.synthesize(spoken,voice_style=style,lang='ko',speed=speed,total_steps=8,silence_duration=.08)
    x=trim(np.asarray(x,dtype=np.float32).reshape(-1),44100);x=resample_poly(x,160,147).astype(np.float32)
    rate=syll/(len(x)/48000);test=na/f"{it['id']}_try{attempt}.wav";sf.write(test,x,48000,subtype='PCM_24')
    stretch=RATE/rate
    if not .8<=stretch<=1.25:
     speed=float(np.clip(speed*RATE/rate,.7,2.0));print(q,it['id'],'tune',attempt,round(rate,3),round(speed,3),flush=True);continue
    if not 6.2<=rate<=6.6:
     corrected=na/f"{it['id']}_try{attempt}_rb.wav"
     subprocess.run(['ffmpeg','-v','error','-y','-i',str(test),'-af',f'atempo={stretch}','-ar','48000',str(corrected)],check=True)
     x,_=sf.read(corrected);rate=syll/(len(x)/48000);test=corrected
    hyp=mlx_whisper.transcribe(str(test),path_or_hf_repo=str(model),language='ko',temperature=0,condition_on_previous_text=False,word_timestamps=True)['text']
    acc=1-qa.cer(norm(text),norm(hyp))
    best=(x,rate,speed,hyp,acc,attempt)
    print(q,it['id'],'ASR',round(acc,4),round(rate,3),hyp,flush=True)
    if acc>=.99:break
   if best is None:
    # Engine already re-synthesised this line. Fine correction uses pitch-preserving WSOLA <=1.25.
    factor=RATE/rate
    if not .8<=factor<=1.25:raise RuntimeError(('rate cannot reach target',q,it['id'],rate))
    test=na/f"{it['id']}_corrected.wav"
    subprocess.run(['ffmpeg','-v','error','-n','-i',str(na/f"{it['id']}_try{attempt}.wav"),'-af',f'atempo={factor}','-ar','48000',str(test)],check=True)
    x,_=sf.read(test);rate=syll/(len(x)/48000);hyp=mlx_whisper.transcribe(str(test),path_or_hf_repo=str(model),language='ko',temperature=0,condition_on_previous_text=False,word_timestamps=True)['text'];acc=1-qa.cer(norm(text),norm(hyp));best=(x,rate,speed,hyp,acc,attempt)
   x,rate,speed,hyp,acc,attempt=best;sf.write(f,x,48000,subtype='PCM_24')
   rec=dict(time_stretch_factor=stretch if 'stretch' in locals() else 1, id=it['id'],cue=it['cue'],text=text,tts_text=spoken,syllables=syll,duration=len(x)/48000,sps=rate,engine_speed=speed,voice='M1',steps=8,asr_text=hyp,asr_accuracy=acc,attempts=attempt+1,file=str(f.relative_to(W)),sha256=sha(f))
   record.write_text(json.dumps(rec,ensure_ascii=False,indent=1));index.append(rec)
  # Place all newly synthesised lines with 33ms between files, no old inter-cue padding.
  cur=0;knots=[(0,0)];newitems=[]
  for it,rec in zip(items,index):
   dur=math.ceil(rec['duration']*30);new=dict(it,start=cur,end=cur+dur,file=rec['file']);newitems.append(new)
   knots.extend([(it['start'],cur),(it['end'],cur+dur)]);cur+=dur+1
  # CTA overlays the last 45 frames, with the original spoken outro retained.
  n=max(660,cur+2)
  knots.append((old['durationInFrames'],n));ks=sorted(dict(knots).items());ox=np.array([x for x,y in ks]);ny=np.array([y for x,y in ks])
  def at(f):return int(round(np.interp(f,ox,ny)))
  doc=copy.deepcopy(old);doc['durationInFrames']=n;doc['audio']=f'{q}/v51/mix_master.wav'
  for c in doc['cues']:
   oc=next(x for x in old['cues'] if x['id']==c['id']);start=at(oc['from']);end=at(oc['from']+oc['dur']);c['from']=start;c['dur']=max(1,end-start)
   c['a']={k:at(oc['from']+v)-start for k,v in oc['a'].items()}
   def props(x,key=None):
    if isinstance(x,dict):return {k:props(v,k) for k,v in x.items()}
    if isinstance(x,list):return [props(v,key) for v in x]
    if isinstance(x,(int,float)) and not isinstance(x,bool) and key in {'at','until','leverAt','handAt','moneyAt','bigAt','logoAt','punch','cardAt','liftAt'}:
     if x < -50:return x
     return at(oc['from']+oc['a'].get('s1',0)+x)-start-c['a'].get('s1',0)
    return x
   c['p']=props(oc['p'])
  doc['subtitles']=[dict(s,from_=at(s['from_']),to=max(at(s['from_'])+1,at(s['to']))) for s in old['subtitles']]
  pcm=np.zeros((n*1600,2),np.float32)
  for it,rec in zip(newitems,index):
   x,_=sf.read(W/rec['file']);a=it['start']*1600;pcm[a:a+len(x)]=x[:,None]
  raw=out/'mix_raw.wav';sf.write(raw,pcm,48000,subtype='FLOAT')
  measure=subprocess.run(['ffmpeg','-v','info','-i',str(raw),'-af','loudnorm=I=-14:TP=-1.7:LRA=11:print_format=json','-f','null','-'],capture_output=True,text=True).stderr
  m=json.loads(measure[measure.rindex('{'):measure.rindex('}')+1]);af=f"loudnorm=I=-14:TP=-1.7:LRA=11:measured_I={m['input_i']}:measured_TP={m['input_tp']}:measured_LRA={m['input_lra']}:measured_thresh={m['input_thresh']}:offset={m['target_offset']}:linear=true"
  subprocess.run(['ffmpeg','-v','error','-n','-i',str(raw),'-af',af,'-ar','48000','-c:a','pcm_s24le',str(out/'mix_master.wav')],check=True)
  pub=PUB/q/'v51';pub.mkdir(exist_ok=True)
  import shutil
  shutil.copy2(out/'mix_master.wav',pub/'mix_master.wav')
  for p in [out/'render.json',pub/'render.json']:p.write_text(json.dumps(doc,ensure_ascii=False,indent=1))
  (out/'timing.json').write_text(json.dumps(dict(items=newitems,knots=ks),ensure_ascii=False,indent=1))
  meta=dict(episode=q,voice='M1',model='Supertone/supertonic-3',reference=' '.join(i['text'] for i in items),items=index,syllables=sum(i['syllables'] for i in index),speech_seconds=sum(i['duration'] for i in index),duration_frames=n,all_lines_resynthesized=True,wording_identical_to_v5=True,inter_line_file_gap_frames=1,definition='Hangul syllables in engine input, numerals expanded by the existing episode lexicon / summed silence-trimmed utterance durations; includes internal natural pauses',network=False)
  meta['syllables_per_second']=meta['syllables']/meta['speech_seconds'];(out/'audio.json').write_text(json.dumps(meta,ensure_ascii=False,indent=1));print('DONE',q,n/30,meta['syllables_per_second'],flush=True)
if __name__=='__main__':main()
