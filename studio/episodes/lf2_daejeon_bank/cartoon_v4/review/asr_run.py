import os,json,subprocess
from pathlib import Path
R=Path(__file__).parent
os.environ['HF_HUB_OFFLINE']='1';os.environ['PYTHONDONTWRITEBYTECODE']='1'
subprocess.run(['ffmpeg','-v','error','-i',str(R.parent/'lf2_cartoon_v4_1080p.mp4'),'-ar','16000','-ac','1',str(R/'final_mix_16k.wav'),'-y'],check=True)
import mlx_whisper
r=mlx_whisper.transcribe(str(R/'final_mix_16k.wav'),path_or_hf_repo='mlx-community/whisper-large-v3-turbo',language='ko',word_timestamps=True,verbose=False,condition_on_previous_text=False)
(R/'asr.json').write_text(json.dumps(r,ensure_ascii=False,indent=2))
print('ASR complete',len(r['segments']))
