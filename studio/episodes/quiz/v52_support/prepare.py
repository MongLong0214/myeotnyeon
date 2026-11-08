"""v52: original v3 master speech segments, only hook synthesised, no existing file mutated."""
from pathlib import Path
import sys,json,re,math,hashlib,copy,importlib.util
import numpy as np,soundfile as sf
from scipy.signal import resample_poly
from supertonic import TTS
W=Path(__file__).resolve().parents[3];P=W/'production/compositor/public';S=Path(__file__).parent
sys.path.insert(0,str(W/'episodes/quiz/v51_support'));from align_v51 import normalizer,align
sys.path.insert(0,str(W/'episodes/quiz/out/v3'));import qa

def load(p):return json.loads(p.read_text())
def save(p,x):
 with p.open('x') as f:json.dump(x,f,ensure_ascii=False,indent=1)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def syll(s):return len(re.findall('[가-힣]',s))
def hook_trim(x,sr):
 win=round(sr*.005);n=len(x)//win;rms=np.sqrt(np.mean(x[:n*win].reshape(-1,win)**2,axis=1));idx=np.where(rms>10**(-45/20))[0]
 if len(idx):x=x[max(0,(idx[0]-5)*win):min(len(x),(idx[-1]+6)*win)]
 n=len(x)//win;rms=np.sqrt(np.mean(x[:n*win].reshape(-1,win)**2,axis=1));z=rms<10**(-45/20);edges=np.diff(np.r_[False,z,False].astype(int));keep=np.ones(len(x),bool)
 for a,b in zip(np.where(edges==1)[0],np.where(edges==-1)[0]):
  if b-a>24:keep[(a+8)*win:(b-8)*win]=False
 return x[keep]
def main():
 tts=TTS(auto_download=False,intra_op_num_threads=1,inter_op_num_threads=1);style=tts.get_voice_style('M1')
 import mlx_whisper
 model=next(Path('$HOME/.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots').glob('*/weights.safetensors')).parent
 for q in sys.argv[1:] or ['q015','q012','q016','q017']:
  base=W/'episodes/quiz'/q;out=base/'v52';out.mkdir(exist_ok=False);pub=P/q/'v52';pub.mkdir(exist_ok=False)
  idx=load(base/'audio/na/index.json');index={i['id']:i for i in idx['items']};tim=load(base/'timing.json');prior=load(base/'v5/audio.json');old=load(base/'v5/render.json');norm=normalizer(q)
  spec=importlib.util.spec_from_file_location('lex',base/'tts.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
  body=[index[i['id']] for i in tim['items'][1:]];bd=sum(sf.info(base/i['file']).duration for i in body);bc=sum(syll(i['tts_text']) for i in body)
  all_old_seconds=sum(sf.info(base/i['file']).duration for i in idx['items']);baseline=sum(syll(i['tts_text']) for i in idx['items'])/all_old_seconds
  text=prior['text'];spoken=mod.tts_text(text);hc=syll(spoken);required=hc/((bc+hc)/baseline-bd)
  minimum=max(7.5,bc/bd,baseline,required);target=minimum*1.045;speed=1.38;selected=None
  for take in range(8):
   h,_=tts.synthesize(spoken,voice_style=style,lang='ko',speed=speed,total_steps=16,silence_duration=.08)
   h=hook_trim(np.asarray(h,np.float32).reshape(-1),44100);h=resample_poly(h,160,147).astype(np.float32);rate=hc/(len(h)/48000);f=out/f'hook_take{take}.wav';sf.write(f,h,48000,subtype='PCM_24')
   if not minimum<=rate<=target+.85:
    print(q,'hook tune',take,'sps',rate,'minimum',minimum,flush=True);speed=float(np.clip(speed*target/rate,.7,2));continue
   a=mlx_whisper.transcribe(str(f),path_or_hf_repo=str(model),language='ko',temperature=0,condition_on_previous_text=False,word_timestamps=True);acc=1-qa.cer(norm(text),norm(a['text']));print(q,'hook',take,'sps',round(rate,3),'ASR',acc,a['text'],flush=True)
   if acc>=.99:selected=(h,rate,speed,take,a);break
  if selected is None:raise RuntimeError(('no passing new hook',q))
  h,hrate,hspeed,take,ha=selected;save(out/'hook_asr.json',ha)
  original,sr=sf.read(P/q/'mix_master.wav',dtype='int32',always_2d=True);assert sr==48000
  first=tim['items'][0];voice,_=sf.read(base/first['file']);start=round(first['start']*sr/30);aligned=original[start:start+len(voice)].astype(np.float64).mean(1)/(2**31)
  gain=float(np.dot(aligned,voice)/np.dot(voice,voice));gain=min(gain,.76/max(1e-9,float(np.abs(h).max())))
  sf.write(out/'hook_master.wav',np.repeat((h*gain)[:,None],2,axis=1),sr,subtype='PCM_24');hook,_=sf.read(out/'hook_master.wav',dtype='int32',always_2d=True)
  chunks=[hook];items=[];records=[];cur=0
  olditems=copy.deepcopy(tim['items']);olditems[0].update(start=0,end=prior['new_cut_frame'],text=text)
  for it in olditems[1:]:it['start']+=prior['delta_frames'];it['end']+=prior['delta_frames']
  for k,it in enumerate(olditems):
   if k==0:x=hook;dur=len(h)/sr;count=hc;path=out/'hook_master.wav';ts=spoken
   else:
    source=tim['items'][k];rec=index[it['id']];path=base/rec['file'];length=sf.info(path).frames;oldstart=round(source['start']*sr/30);x=original[oldstart:oldstart+length].copy();assert len(x)==length;dur=length/sr;count=syll(rec['tts_text']);ts=rec['tts_text'];chunks.append(x)
   ni=dict(it,start=cur/1600,end=(cur+len(x))/1600,start_sample=cur,end_sample=cur+len(x),file=str(path.relative_to(W)));items.append(ni)
   records.append(dict(id=it['id'],cue=it['cue'],text=it['text'],tts_text=ts,syllables=count,duration=dur,sps=count/dur,engine_speed=hspeed if k==0 else idx['speed'],steps=16,voice='M1',resynthesized=k==0,file=str(path.relative_to(W)),source_sha256=sha(path),original_master_start_sample=None if k==0 else oldstart,new_start_sample=cur,samples=len(x)))
   cur+=len(x)
  # The 1.5s CTA begins with the original spoken outro; the trailing tail is not a between-line pause.
  n=max(660,math.ceil(items[-1]['start'])+45,math.ceil(cur/1600))
  master=np.zeros((n*1600,2),np.int32);pos=0
  for x in chunks:master[pos:pos+len(x)]=x;pos+=len(x)
  sf.write(out/'mix_master.wav',master,sr,subtype='PCM_24');actual,_=sf.read(out/'mix_master.wav',dtype='int32',always_2d=True)
  evidence=[]
  for rec in records[1:]:
   a=rec['original_master_start_sample'];b=rec['new_start_sample'];ln=rec['samples'];ident=np.array_equal(actual[b:b+ln],original[a:a+ln]);assert ident
   evidence.append(dict(id=rec['id'],source_start_sample=a,delivery_start_sample=b,samples=ln,pcm_identical=ident,source_pcm_sha256=hashlib.sha256(original[a:a+ln].tobytes()).hexdigest(),delivery_pcm_sha256=hashlib.sha256(actual[b:b+ln].tobytes()).hexdigest()))
  # Map every old measured speech boundary to its new exact position; preserve original fact text.
  knots={0:0,old['durationInFrames']:n}
  for a,b in zip(olditems,items):knots[a['start']]=b['start'];knots[a['end']]=b['end']
  ks=sorted(knots.items());ox=np.array([a for a,b in ks]);ny=np.array([b for a,b in ks]);at=lambda x:int(round(np.interp(x,ox,ny)))
  doc=copy.deepcopy(old);doc['durationInFrames']=n;doc['audio']=f'{q}/v52/mix_master.wav'
  for c,oc in zip(doc['cues'],old['cues']):
   start=at(oc['from']);c['from']=start;c['dur']=max(1,at(oc['from']+oc['dur'])-start);c['a']={k:at(oc['from']+v)-start for k,v in oc['a'].items()}
   def props(x,key=None):
    if isinstance(x,dict):return {k:props(v,k) for k,v in x.items()}
    if isinstance(x,list):return [props(v,key) for v in x]
    if isinstance(x,(int,float)) and not isinstance(x,bool) and key in {'at','until','leverAt','handAt','moneyAt','bigAt','logoAt','punch','cardAt','liftAt'}:
     return x if x < -50 else at(oc['from']+oc['a'].get('s1',0)+x)-start-c['a'].get('s1',0)
    return x
   c['p']=props(oc['p'])
  for c in doc['cues'][1:]:
   lead=min(i['start'] for i in items if i['cue']==c['id']);newstart=int(round(lead))-4;delta=c['from']-newstart;c['from']=newstart;c['a']={k:v+delta for k,v in c['a'].items()}
  for a,b in zip(doc['cues'],doc['cues'][1:]):a['dur']=b['from']-a['from']
  doc['cues'][-1]['dur']=n-doc['cues'][-1]['from'];doc['subtitles']=[dict(s,from_=at(s['from_']),to=max(at(s['from_'])+1,at(s['to']))) for s in old['subtitles']]
  ref=' '.join(i['text'] for i in items);assert ref==prior['reference']
  meta=dict(episode=q,voice='M1',reference=ref,items=records,syllables=bc+hc,speech_seconds=bd+len(h)/sr,syllables_per_second=(bc+hc)/(bd+len(h)/sr),original_v3_syllables_per_second=baseline,original_body_syllables_per_second=bc/bd,hook_syllables_per_second=hrate,hook_engine_speed=hspeed,hook_gain=gain,hook_take=take,body_pcm_identical=True,body_pcm_evidence=evidence,body_narration_source='Original v3 normalized master segments, original sentence WAV lengths, no stretch/trim/gain changes. Only spaces between sentence files removed.',original_master_sha256=sha(P/q/'mix_master.wav'),wording_identical_to_v5=True,all_lines_resynthesized=False,definition='Hangul syllables in existing episode TTS numeral readings / sum of complete utterance WAV durations, identical to original v3 comparison; excludes between-line gaps.',duration_frames=n,network=False)
  assert meta['syllables_per_second']>=baseline and hrate>=7.5
  save(out/'audio.json',meta);save(out/'timing.json',dict(items=items,knots=ks))
  # Align new caption times to actual speech; the original display strings remain untouched.
  ar=mlx_whisper.transcribe(str(out/'mix_master.wav'),path_or_hf_repo=str(model),language='ko',temperature=0,condition_on_previous_text=False,word_timestamps=True);save(out/'asr_master.json',ar)
  rows,clockacc=align(doc,meta,ar,norm);fullacc=1-qa.cer(norm(ref),norm(ar['text']))
  if fullacc<.99:raise RuntimeError(('new master ASR below .99',q,fullacc,ar['text']))
  for sub,row in zip(doc['subtitles'],rows):sub['from_']=row['start'];sub['to']=row['end']
  for a,b in zip(doc['subtitles'],doc['subtitles'][1:]):a['to']=max(a['from_']+1,min(a['to'],b['from_']))
  save(out/'subtitle_alignment.json',dict(accuracy=fullacc,character_clock_accuracy=clockacc,rows=rows,pass_=fullacc>=.99))
  save(out/'render.json',doc);save(pub/'render.json',doc)
  with (out/'mix_master.wav').open('rb') as a,(pub/'mix_master.wav').open('xb') as b:
   import shutil;shutil.copyfileobj(a,b)
  print('DONE',q,'seconds',n/30,'sps',meta['syllables_per_second'],'original',baseline,'hook',hrate,'ASR',fullacc,flush=True)
if __name__=='__main__':main()
