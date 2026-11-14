"""CPU fallback for the existing cached Whisper model; final-mix sentence checks.
No prompts or expected text are fed to the recognizer. Uses the same edit distance
as S001/asr_check.py, with explicit number-reading normalization from lex.json.
"""
from pathlib import Path
import sys,json,re,struct,time,math,os
sys.path.append('/opt/homebrew/Cellar/openai-whisper/20250625_4/libexec/lib/python3.14/site-packages')
import whisper,torch,numpy as np,soundfile as sf
from scipy.signal import resample_poly
E=Path(__file__).resolve().parent
lex=json.loads((E/'lex.json').read_text())
def norm(s):
 # Canonical date/number formatting, before stripping punctuation. A two-digit
 # year is expanded only when the complete date matches an adopted source date.
 s=re.sub(r'\s+','',s)
 for digits,reading in lex:
  compact=re.sub(r'\s+','',digits)
  if re.match(r'20\d{2}년\d+월\d+일$',compact):
   s=re.sub(r'(?<!\d)'+re.escape(compact[2:]),compact,s)
 for a,b in lex:s=s.replace(re.sub(r'\s+','',a),re.sub(r'\s+','',b))
 for a,b in [('6월','유월'),('육월','유월'),('이틀후','이틀뒤')]:s=s.replace(a,b)
 return re.sub('[^가-힣0-9]','',s)
def distance(a,b):
 a,b=norm(a),norm(b);d=list(range(len(b)+1))
 for i,ca in enumerate(a,1):
  p=d[:];d[0]=i
  for j,cb in enumerate(b,1):d[j]=min(p[j]+1,d[j-1]+1,p[j-1]+(ca!=cb))
 return d[-1],len(a)
def load():
 torch.set_num_threads(4)
 p=next(Path.home().glob('.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots/*/weights.safetensors'))
 cfg=json.loads(p.with_name('config.json').read_text());cfg.pop('model_type',None)
 m=whisper.Whisper(whisper.ModelDimensions(**cfg))
 with p.open('rb') as f:
  n=struct.unpack('<Q',f.read(8))[0];h=json.loads(f.read(n));off=8+n
 weights={}
 for key,v in h.items():
  if key in ('__metadata__','alignment_heads'):continue
  a=np.memmap(p,mode='r',dtype={'F16':'<f2','F32':'<f4'}[v['dtype']],offset=off+v['data_offsets'][0],shape=tuple(v['shape']))
  k=key.replace('.mlp1.','.mlp.0.').replace('.mlp2.','.mlp.2.')
  x=torch.from_numpy(np.array(a,copy=True)).float()
  if '.conv' in k and k.endswith('.weight'):x=x.transpose(1,2).contiguous()
  weights[k]=x
 print('loading weights',flush=True);print(m.load_state_dict(weights,strict=False),flush=True);m.eval();return m

def recognize(m,w):
 # Use the model's trained 30-second context; short-context cropping caused
 # repetition and is deliberately not used for acceptance measurements.
 mel=whisper.log_mel_spectrogram(whisper.pad_or_trim(w.astype(np.float32)),n_mels=128)
 with torch.inference_mode():
  r=whisper.decode(m,mel,whisper.DecodingOptions(language='ko',fp16=False,without_timestamps=True,temperature=0,sample_len=180))
 return r.text.strip()

if __name__=='__main__':
 m=load();start=time.time();items=json.loads((E/'audio/na/index.json').read_text())['items'];mode=sys.argv[1] if len(sys.argv)>1 else 'takes';results=[]
 if mode=='final':
  subprocess=__import__('subprocess');subprocess.run(['ffmpeg','-v','error','-y','-i',str(E/'out/n18_v4.mp4'),'-vn','-ar','16000','-ac','1',str(E/'audio/final_aac.wav')],check=True)
  audio,sr=sf.read(E/'audio/final_aac.wav')
 for it in items:
  if mode=='final':
   a=int((it['t_start']+1.5)*16000);b=int((it['t_end']+1.5+.12)*16000);w=audio[max(0,a-640):b]
  else:
   w,sr=sf.read(E/it['file']);w=resample_poly(w,1,3)
  asr=recognize(m,w);d,n=distance(it['text'],asr);results.append(dict(id=it['id'],text=it['text'],asr=asr,errors=d,characters=n,match=1-d/n))
  print(it['id'],round(1-d/n,4),asr,flush=True)
  (E/f'out/asr_{mode}.json').write_text(json.dumps(dict(model='existing cached whisper-large-v3-turbo',backend='PyTorch CPU; converted in memory from cached MLX tensors',normalization='lex.json digit readings, whitespace/punctuation, 유월 orthography',prompt=None,match=1-sum(x['errors'] for x in results)/sum(x['characters'] for x in results),items=results,seconds=time.time()-start),ensure_ascii=False,indent=1))
