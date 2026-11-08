"""Independent local Whisper ASR. No expected-text prompt or network."""
import os,json,re,sys,subprocess,difflib,hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',PYTHONDONTWRITEBYTECODE='1',TMPDIR=str(P/'tmp'),MLX_CACHE_DIR=str(P/'tmp/mlx'))
import socket
def denied(*a,**k):raise RuntimeError('Network disabled')
socket.create_connection=denied;socket.socket.connect=denied
from voice import spoken,korean
def norm(s):
 s=s.replace(',','');s=re.sub(r'(?i)cctv','씨씨티비',s);s=re.sub(r'(?i)dna','디엔에이',s)
 s=re.sub(r'(?i)A','에이',s);s=re.sub(r'(?i)B','비',s)
 for a,b in [('1만5천','일만오천'),('1만5000','일만오천'),('15만','십오만'),('9천만','구천만'),('2억1천만','이억천만'),('2억1000만','이억천만'),('10월','시월'),('2인조','이인조'),('2개','두개'),('3명이','세명이'),('3명도','세명도'),('10시','열시')]:s=s.replace(a,b)
 s=spoken(s)
 return re.sub('[^가-힣]','',s)
def distance(a,b):
 row=list(range(len(b)+1))
 for i,ca in enumerate(a,1):
  prev=row;row=[i]+[0]*len(b)
  for j,cb in enumerate(b,1):row[j]=min(row[j-1]+1,prev[j]+1,prev[j-1]+(ca!=cb))
 return row[-1]
def main():
 import mlx_whisper
 model=next(Path('$HOME/.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots').iterdir())
 d=json.loads((P/'episode_data.json').read_text());mode=sys.argv[1] if len(sys.argv)>1 else 'voice'
 file=P/'public/voice_full.wav' if mode=='voice' else P/'lf2_cartoon_v5_1080p.mp4'
 wav=P/'qa'/f'asr_{mode}_16k.wav';subprocess.run(['ffmpeg','-v','error','-y','-i',str(file),'-ac','1','-ar','16000',str(wav)],check=True)
 r=mlx_whisper.transcribe(str(wav),path_or_hf_repo=str(model),language='ko',word_timestamps=True,condition_on_previous_text=False,verbose=False)
 (P/'qa'/f'asr_{mode}.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
 expected=norm(' '.join(n['text'] for n in d['narration']));actual=norm(r['text']);dist=distance(expected,actual)
 diffs=[dict(op=tag,expected=expected[i:j],recognized=actual[k:l],expected_index=i,asr_index=k) for tag,i,j,k,l in difflib.SequenceMatcher(None,expected,actual,autojunk=False).get_opcodes() if tag!='equal']
 report=dict(input_audio_sha256=hashlib.sha256(wav.read_bytes()).hexdigest(),model=str(model),mode=mode,method='1 - Levenshtein character error rate after punctuation/spacing and conventional numeric/Latin readings; no prompt, no text substitutions based on output',expected_characters=len(expected),recognized_characters=len(actual),edit_distance=dist,accuracy=1-dist/len(expected),gate=1-dist/len(expected)>=.98,differences=diffs)
 (P/'qa'/f'asr_{mode}_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2),flush=True)
if __name__=='__main__':main()
