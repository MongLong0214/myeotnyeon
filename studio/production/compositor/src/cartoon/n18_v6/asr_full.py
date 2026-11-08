"""Independent unprompted ASR of continuous narration or delivered AAC."""
import os
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1')
import json,sys,time,subprocess
import mlx_whisper
from audio import E,distance,script
mode=sys.argv[1] if len(sys.argv)>1 else 'voice'
source=E/('n18_cartoon_v6_1080p.mp4' if mode=='aac' else 'audio/narration.wav')
wav=E/f'audio/asr_{mode}_16k.wav'
subprocess.run(['ffmpeg','-v','error','-y','-i',str(source),'-vn','-ar','16000','-ac','1',str(wav)],check=True)
start=time.time()
r=mlx_whisper.transcribe(str(wav),path_or_hf_repo='mlx-community/whisper-large-v3-turbo',language='ko',condition_on_previous_text=False,temperature=0,verbose=False,word_timestamps=True)
err,n=distance(' '.join(x['tts'] for x in script()),r['text'])
result=dict(model='local cached whisper-large-v3-turbo',source=str(source.relative_to(E)),initial_prompt=None,condition_on_previous_text=False,normalization='Numeric cardinal/native counters, whitespace and punctuation only; 육월→유월. No semantic substitutions.',match=1-err/n,errors=err,characters=n,text=r['text'],segments=r['segments'],elapsed_s=time.time()-start)
(E/f'asr_{mode}.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print('ASR',mode,result['match'],err,n,flush=True)
