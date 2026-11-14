from pathlib import Path
import json,sys,re,difflib,importlib.util
import numpy as np
W=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(W/'episodes/quiz/out/v3'));import qa

def normalizer(q):
 spec=importlib.util.spec_from_file_location('episode_lex',W/'episodes/quiz'/q/'tts.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 def norm(s):
  clean=lambda x:re.sub(r'[^가-힣0-9A-Za-z]', '', x)
  s=clean(s)
  for a,b in mod.LEX:
   if clean(a):s=s.replace(clean(a),clean(b))
  return qa.norm(s)
 return norm

def character_clock(asr,norm):
 chars=[];starts=[];ends=[]
 for seg in asr['segments']:
  for w in seg.get('words',[]):
   st=norm(w['word'])
   for i,c in enumerate(st):chars.append(c);starts.append(w['start']+(w['end']-w['start'])*i/len(st));ends.append(w['start']+(w['end']-w['start'])*(i+1)/len(st))
 return ''.join(chars),np.array(starts),np.array(ends)

def align(doc,audio,asr,norm):
 expected=norm(audio['reference']);actual,starts,ends=character_clock(asr,norm);mapping=np.full(len(expected),np.nan)
 for tag,a,b,c,d in difflib.SequenceMatcher(None,expected,actual,autojunk=False).get_opcodes():
  if tag=='equal':mapping[a:b]=np.arange(c,d)
  elif tag=='replace' and d>c:mapping[a:b]=np.linspace(c,d-1,b-a)
 good=np.where(np.isfinite(mapping))[0];mapping=np.interp(np.arange(len(mapping)),good,mapping[good]).round().astype(int);mapping=np.clip(mapping,0,max(0,len(actual)-1))
 cursor=0;rows=[]
 for sub in doc['subtitles']:
  needle=norm(sub['text']);at=expected.find(needle,cursor)
  if at<0:raise RuntimeError(('subtitle text cannot align',sub['text'],cursor))
  a=int(round(starts[mapping[at]]*30));b=max(a+1,int(round(ends[mapping[at+len(needle)-1]]*30)));b=min(b,doc['durationInFrames']);rows.append(dict(text=sub['text'],start=a,end=b,old_start=sub['from_'],old_end=sub['to'],start_seconds=starts[mapping[at]],end_seconds=ends[mapping[at+len(needle)-1]]));cursor=at+len(needle)
 return rows,1-qa.cer(expected,actual)

def main(q):
 p=W/'episodes/quiz'/q/'v51';doc=json.loads((p/'render.json').read_text());audio=json.loads((p/'audio.json').read_text());norm=normalizer(q)
 import mlx_whisper
 model=next(Path('/Users/isaac/.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots').glob('*/weights.safetensors')).parent
 asr=mlx_whisper.transcribe(str(p/'mix_master.wav'),path_or_hf_repo=str(model),language='ko',temperature=0,condition_on_previous_text=False,word_timestamps=True)
 rows,acc=align(doc,audio,asr,norm)
 for sub,row in zip(doc['subtitles'],rows):sub['from_']=row['start'];sub['to']=row['end']
 # Avoid overlapping two-caption frames at a timestamp shared by neighbouring words.
 for a,b in zip(doc['subtitles'],doc['subtitles'][1:]):a['to']=max(a['from_']+1,min(a['to'],b['from_']))
 report=dict(accuracy=acc,transcript=asr['text'],rows=rows,method='Cached offline Whisper word timestamps, normalized with the exact existing episode numeral-reading lexicon. Caption boundaries interpolated within recognized words; no change to displayed text.',pass_=acc>=.99)
 (p/'subtitle_alignment.json').write_text(json.dumps(report,ensure_ascii=False,indent=1));(p/'asr_master.json').write_text(json.dumps(asr,ensure_ascii=False,indent=1))
 if acc<.99:raise RuntimeError(('master ASR under .99',q,acc,asr['text']))
 for path in [p/'render.json',W/'production/compositor/public'/q/'v51/render.json']:path.write_text(json.dumps(doc,ensure_ascii=False,indent=1))
 print(q,'aligned',len(rows),'captions; ASR',acc,flush=True)
if __name__=='__main__':main(sys.argv[1])
