"""Production synthesis of the authorized N18 middle act; untouched PCM outside it."""
from pathlib import Path
import os,sys,json,re,subprocess,hashlib
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1',PYTHONDONTWRITEBYTECODE='1')
import numpy as np
import soundfile as sf
HERE=Path(__file__).resolve().parent
W=HERE.parents[4];E=W/'episodes/v4/n18/cartoon_v6';SR=48000
sys.path.insert(0,str(HERE.parent/'n18_v6'))
from audio import spoken,trim,norm
ROWS=json.loads((HERE/'middle_v6fix2.json').read_text())
A=E/'audio/v6fix2';A.mkdir(exist_ok=True)

def synth():
 from supertonic import TTS
 tts=TTS(auto_download=False,intra_op_num_threads=3,inter_op_num_threads=1)
 style=tts.get_voice_style(voice_name='M1')
 for row in ROWS:
  dest=A/(row['id']+'.wav');raw=A/(row['id']+'_native.wav');text=spoken(row['text'])
  if dest.exists():continue
  wav,_=tts.synthesize(text,voice_style=style,lang='ko',speed=1.05,total_steps=20,silence_duration=.06)
  w=trim(np.asarray(wav,dtype=np.float32).reshape(-1),44100);sf.write(raw,w,44100,subtype='PCM_24')
  target=len(re.findall('[가-힣]',text))/7.08
  subprocess.run(['ffmpeg','-v','error','-y','-i',str(raw),'-af',f'atempo={len(w)/44100/target:.8f}','-ar',str(SR),str(dest)],check=True)
  w,_=sf.read(dest);w=trim(w,SR,.12);sf.write(raw,w,SR,subtype='PCM_24')
  subprocess.run(['ffmpeg','-v','error','-y','-i',str(raw),'-af',f'atempo={len(w)/SR/target:.8f}','-ar',str(SR),str(dest)],check=True)
  w,_=sf.read(dest);w*=.76/max(.001,np.max(np.abs(w)));sf.write(dest,w,SR,subtype='PCM_24')
  print(row['id'],round(len(w)/SR,3),text,flush=True)
 assemble()

def assemble():
 original=json.loads((E/'narration.json').read_text())
 start=round(next(r['start'] for r in original['items'] if r['id']=='N035_01')*SR)
 stop=round(next(r['start'] for r in original['items'] if r['id']=='N064_01')*SR)
 waves=[];items=[];pos=0
 for row in ROWS:
  w,sr=sf.read(A/(row['id']+'.wav'));assert sr==SR
  items.append(dict(row,tts=spoken(row['text']),start=pos/SR,end=(pos+len(w))/SR,duration=len(w)/SR,syllables=len(re.findall('[가-힣]',spoken(row['text'])))))
  waves += [w,np.zeros(round(.235*SR))];pos+=len(w)+round(.235*SR)
 # The outside picture and audio shift by an identical whole number of frames.
 middle=np.concatenate(waves);old_frames=9423-4808
 new_frames=int(np.ceil((len(middle)-(stop-start-old_frames*1600))/1600))
 removed=old_frames-new_frames;required=stop-start-removed*1600
 middle=np.pad(middle,(0,required-len(middle)))
 raw=A/'middle_raw.wav';sf.write(raw,middle,SR,subtype='PCM_24')
 level=A/'middle_level.wav'
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(raw),'-af','loudnorm=I=-16:TP=-1.5:LRA=7','-ar',str(SR),'-ac','1',str(level)],check=True)
 fresh,sr=sf.read(level,dtype='int16');assert sr==SR and len(fresh)==required
 original_pcm,sr=sf.read(E/'public/mix.wav',dtype='int16');assert sr==SR
 master=np.concatenate([original_pcm[:start],fresh,original_pcm[stop:]])
 public=E/'public_v6fix2';public.mkdir(exist_ok=True)
 import shutil
 shutil.copy2(E/'public/Pretendard-Bold.woff2',public/'Pretendard-Bold.woff2')
 sf.write(public/'mix.wav',master,SR,subtype='PCM_16')
 same_before=np.array_equal(master[:start],original_pcm[:start]);same_after=np.array_equal(master[start+required:],original_pcm[stop:]);assert same_before and same_after
 h=lambda a:hashlib.sha256(a.tobytes()).hexdigest()
 meta=dict(voice='M1',model='Supertone/supertonic-3',native_speed=1.05,target_syl_s=7.08,total_steps=20,sentence_gap_s=.235,
 source_audio='public/mix.wav',replace_samples=[start,stop],replace_seconds=[start/SR,stop/SR],old_picture_frames=[4808,9423],middle_frames=new_frames,removed_frames=removed,removed_seconds=removed/30,
 duration_samples=len(master),duration_s=len(master)/SR,items=items,
 untouched_pcm=dict(prefix_identical=same_before,suffix_identical=same_after,prefix_sha256=h(master[:start]),suffix_sha256=h(master[start+required:]),source_prefix_sha256=h(original_pcm[:start]),source_suffix_sha256=h(original_pcm[stop:])))
 (E/'narration_v6fix2.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2)+'\n')
 print('ASSEMBLED',new_frames/30,'s middle;',removed/30,'s removed;',len(master)/SR,'s film; outside PCM identical',flush=True)

def align():
 import mlx_whisper
 model=next(Path('$HOME/.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots').glob('*/weights.safetensors')).parent
 path=E/'asr_v6fix2_middle.json';out=[]
 for row in ROWS:
  r=mlx_whisper.transcribe(str(A/(row['id']+'.wav')),path_or_hf_repo=str(model),language='ko',condition_on_previous_text=False,temperature=0,word_timestamps=True,verbose=False)
  out.append(dict(id=row['id'],text=r['text'],words=[w for s in r['segments'] for w in s.get('words',[])]))
  path.write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
  print('aligned',row['id'],r['text'],flush=True)
if __name__=='__main__':
 mode=sys.argv[1] if len(sys.argv)>1 else 'synth'
 if mode=='synth':synth()
 elif mode=='align':align()
 elif mode=='assemble':assemble()
