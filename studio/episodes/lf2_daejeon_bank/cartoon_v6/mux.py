"""Encode the edited PCM once, retaining all earlier video and WAV files."""
import json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;d=json.loads((P/'episode_data_v6fix2.json').read_text());picture=P/'fix2_evidence/picture_v6fix2_1080p.mp4'
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=nb_frames','-of','json',str(picture)]))
assert int(probe['streams'][0]['nb_frames'])==d['durationInFrames']
subprocess.run(['ffmpeg','-v','error','-y','-i',str(picture),'-i',str(P/'public/voice_v6fix2.wav'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-ar','48000','-movflags','+faststart',str(P/'lf2_cartoon_v6fix2_1080p.mp4')],check=True)
subprocess.run(['ffmpeg','-v','error','-y','-i',str(P/'lf2_cartoon_v6fix2_1080p.mp4'),'-vf','scale=640:360','-c:v','libx264','-crf','22','-preset','fast','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',str(P/'lf2_cartoon_v6fix2_360p.mp4')],check=True)
print('MUXED',d['durationInFrames'],'frames /',d['audioDuration'],'s',flush=True)
