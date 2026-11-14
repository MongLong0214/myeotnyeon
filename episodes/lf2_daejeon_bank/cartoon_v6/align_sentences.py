"""Independent word ASR of exact final sentence waveforms, anchored before assembly.
Avoids Whisper's tendency to place a new sentence's first word in the preceding one.
"""
import os,json,socket,sys
from pathlib import Path
P=Path(__file__).resolve().parent
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(P/'tmp'),MLX_CACHE_DIR=str(P/'tmp/mlx'))
def denied(*a,**k):raise RuntimeError('Network disabled')
socket.create_connection=denied;socket.socket.connect=denied
import mlx_whisper
model=next(Path('/Users/isaac/.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots').iterdir())
fix2='--fix2' in sys.argv
d=json.loads((P/('episode_data_v6fix2.json' if fix2 else 'episode_data.json')).read_text());allwords=[];rows=[]
for n in d['sentences']:
 cache=P/('fix2_evidence/asr' if fix2 and n['id'].startswith('M') else 'qa')/f"align_{n['id']}.json"
 if cache.exists():r=json.loads(cache.read_text())
 else:
  r=mlx_whisper.transcribe(str(P/n['audio_path']) if fix2 else str(P/'audio'/f"{n['id']}.wav"),path_or_hf_repo=str(model),language='ko',word_timestamps=True,condition_on_previous_text=False,verbose=False)
  cache.write_text(json.dumps(r,ensure_ascii=False,indent=2))
 ws=[w for s in r['segments'] for w in s.get('words',[])];rows.append(dict(id=n['id'],text=n['text'],recognized=r['text'],offset_s=n['start_s']))
 for w in ws:
  w=dict(w);w['start']=n['start_s']+max(0,min(n['duration'],w['start']));w['end']=n['start_s']+max(0,min(n['duration'],w['end']));w['sentenceId']=n['id'];allwords.append(w)
 print(n['id'],r['text'],flush=True)
(P/('fix2_evidence/final_word_timestamps.json' if fix2 else 'qa/final_word_timestamps.json')).write_text(json.dumps(dict(method='Independent Whisper per exact final TTS sentence waveform, offset by sample-exact concatenation timestamps; no prompt. Final WAV consists of these samples plus 240ms sentence pads.',words=allwords,sentences=rows),ensure_ascii=False,indent=2))
