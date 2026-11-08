"""Recognize the complete delivered AAC, with no script prompt."""
import os
os.environ.update(HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',HF_HUB_DISABLE_TELEMETRY='1')
import json,time,subprocess
import mlx_whisper
import audio as V
E=V.E;start=time.time();video=E/'n18_cartoon_v5_1080p.mp4'
wav=E/'audio/final_aac_16k.wav'
subprocess.run(['ffmpeg','-v','error','-y','-i',str(video),'-vn','-ar','16000','-ac','1',str(wav)],check=True)
r=mlx_whisper.transcribe(str(wav),path_or_hf_repo='mlx-community/whisper-large-v3-turbo',language='ko',condition_on_previous_text=False,temperature=0,verbose=False,word_timestamps=True)
expected=' '.join(x['tts'] for x in V.read_script());errors,n=V.distance(expected,r['text'])
result=dict(model='local cached whisper-large-v3-turbo',source=video.name+' delivered AAC',initial_prompt=None,condition_on_previous_text=False,normalization='Numeric cardinal/native counter readings, punctuation/whitespace, 육월→유월, 이틀후→이틀뒤. No semantic corrections.',match=1-errors/n,errors=errors,characters=n,text=r['text'],segments=r['segments'],seconds=time.time()-start)
(E/'asr_final.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(result['match'],errors,n,flush=True)
