"""Opt-in v5 documents/audio; original render data and PCM are never modified."""
from pathlib import Path
import sys, json, copy, math, hashlib, importlib.util
import numpy as np, soundfile as sf
from scipy.signal import resample_poly
from supertonic import TTS
W=Path(__file__).resolve().parents[3]; sys.path.insert(0,str(W/'episodes/quiz'))
from episodes import EPISODES
P=W/'production/compositor/public'; SUPPORT=Path(__file__).parent

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 tts=TTS(auto_download=False,intra_op_num_threads=4,inter_op_num_threads=1)
 for q in ['q015','q012','q016','q017']:
  e=EPISODES[q]; base=W/'episodes/quiz'/q; out=base/'v5';out.mkdir(exist_ok=True)
  spec=importlib.util.spec_from_file_location('episode_tts',base/'tts.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
  settings=json.loads((base/'audio/na/index.json').read_text()); hook=e['hook']['narration']; ask=e['hook'].get('ask') or json.loads((P/q/'render.json').read_text())['ep']['ask']
  text=hook+' '+ask; spoken=mod.tts_text(text)
  target=out/'hook.wav'
  if target.exists():raise RuntimeError('refusing overwrite '+str(target))
  wav,_=tts.synthesize(spoken,voice_style=tts.get_voice_style(voice_name=settings['voice']),lang='ko',speed=settings['speed'],total_steps=settings['steps'])
  x=resample_poly(mod.trim(np.asarray(wav,dtype=np.float32).reshape(-1),44100),160,147).astype(np.float32)
  sf.write(target,x,48000,subtype='PCM_24')
  doc=json.loads((P/q/'render.json').read_text()); old=copy.deepcopy(doc);tim=json.loads((base/'timing.json').read_text());first=tim['items'][0]
  orig,sr=sf.read(P/q/'mix_master.wav',always_2d=True); voice,_=sf.read(base/first['file']); aligned=orig[round(first['start']*sr/30):round(first['start']*sr/30)+len(voice)].mean(1)
  gain=float(np.dot(aligned,voice)/np.dot(voice,voice))
  cut=first['end']; newcut=math.ceil(len(x)/sr*30);delta=newcut-cut
  intro=np.zeros((round(newcut*sr/30),2));intro[:len(x)]=x[:,None]*gain
  mixed=np.concatenate([intro,orig[round(cut*sr/30):]])
  sf.write(out/'mix_master.wav',mixed,sr,subtype='PCM_24')
  saved,_=sf.read(out/'mix_master.wav',always_2d=True)
  assert np.array_equal(saved[len(intro):],orig[round(cut*sr/30):])
  for c in doc['cues']:
   if c['from']==0:
    c['dur']+=delta;c['a']['s1']=0;c['a']['e1']=newcut
    for k in c['a']:
     if k not in ['s1','e1']:c['a'][k]+=delta
   else:c['from']+=delta
  if 's2' in old['cues'][0]['a'] and 'punch' in old['cues'][0]['p']:
   old_s1=old['cues'][0]['a']['s1']
   doc['cues'][0]['p']['punch']=[round(t/(cut-old_s1)*newcut) if t+old_s1<cut else t+old_s1+delta for t in old['cues'][0]['p']['punch']]
  doc['durationInFrames']+=delta
  # Existing first-sentence captions are replaced with weighted splits, all later captions move together.
  subs=[dict(s,from_=s['from_']+delta,to=s['to']+delta) for s in old['subtitles'] if s['from_']>=cut]
  lines=e['hook'].get('split') or [hook];pieces=[*lines,ask];weights=[len(s.replace('\n','')) for s in pieces];acc=0;intro_sub=[]
  for i,(s,w) in enumerate(zip(pieces,weights)):
   start=round(newcut*acc/sum(weights));acc+=w;end=round(newcut*acc/sum(weights));intro_sub.append(dict(from_=start,to=end,text=s))
  doc['subtitles']=intro_sub+subs;doc['audio']=f'{q}/v5/mix_master.wav'
  pub=P/q/'v5';pub.mkdir(exist_ok=True);sf.write(pub/'mix_master.wav',saved,sr,subtype='PCM_24')
  (pub/'render.json').write_text(json.dumps(doc,ensure_ascii=False,indent=1))
  (out/'render.json').write_text(json.dumps(doc,ensure_ascii=False,indent=1))
  ref=text+' '+' '.join(it['text'] for it in tim['items'][1:])
  meta=dict(episode=q,voice=settings['voice'],speed=settings['speed'],steps=settings['steps'],text=text,tts_text=spoken,reference=ref,old_cut_frame=cut,new_cut_frame=newcut,delta_frames=delta,gain=gain,body_pcm_identical=True,original_master_sha256=sha(P/q/'mix_master.wav'),new_master_sha256=sha(out/'mix_master.wav'),duration_frames=doc['durationInFrames'])
  (out/'audio.json').write_text(json.dumps(meta,ensure_ascii=False,indent=1));print(q,meta,flush=True)
if __name__=='__main__':main()
