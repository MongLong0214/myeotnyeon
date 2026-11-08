"""Assemble corrected source shots, master AAC, then measure delivered media."""
from pathlib import Path
import json,subprocess,time,sys,re,hashlib,datetime
E=Path(__file__).resolve().parent;W=E.parents[2];O=E/'out';film=json.loads((W/'production/compositor/src/v4/n18-film.json').read_text());duration=film['durationInFrames']/30

def run(args,log):
 with (O/log).open('w') as f:subprocess.run(args,stdout=f,stderr=subprocess.STDOUT,check=True)

def measure():
 p=subprocess.run(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(O/'n18_v4.mp4')],capture_output=True,text=True,check=True);probe=json.loads(p.stdout);(O/'ffprobe.json').write_text(json.dumps(probe,indent=1))
 run(['ffmpeg','-hide_banner','-i',str(O/'n18_v4.mp4'),'-vn','-af','ebur128=peak=true','-f','null','-'],'ebur128.log')
 run(['ffmpeg','-hide_banner','-i',str(O/'n18_v4.mp4'),'-an','-vf','freezedetect=n=-50dB:d=0.2,blackdetect=d=0.05:pix_th=0.04:pic_th=0.98','-f','null','-'],'freeze-black.log')
 # 0,10,...,380 seconds; PTS-based labels are only on this QA contact sheet.
 font=str(W/'production/compositor/public/fonts/Pretendard-Regular.otf')
 vf=f"select='not(mod(n,300))',scale=384:216,drawtext=fontfile={font}:text='%{{pts\\:hms}}':fontsize=15:fontcolor=white:box=1:boxcolor=black@0.7:x=9:y=9,tile=5x8:padding=8:margin=8"
 run(['ffmpeg','-v','error','-y','-i',str(O/'n18_v4.mp4'),'-vf',vf,'-frames:v','1',str(O/'sheet.png')],'sheet.log')
 print('MEDIA MEASURED',flush=True)

def assemble():
 t=time.monotonic();start=datetime.datetime.now().astimezone().isoformat()
 filt=f'[0:v]split=2[a][b];[a]trim=start_frame=0:end_frame=195,setpts=N/(30*TB)[pre];[1:v]setpts=N/(30*TB)[mid];[b]trim=start_frame=393:end_frame=9720,setpts=N/(30*TB)[post];[2:v]setpts=N/(30*TB)[tail];[pre][mid][post][tail]concat=n=4:v=1:a=0,format=yuv420p[v]'
 run(['ffmpeg','-hide_banner','-y','-r','30','-i',str(E/'build/recovered.h264'),'-i',str(O/'_spatial.mp4'),'-i',str(E/'build/tail.mp4'),'-i',str(E/'audio/mix_master.wav'),'-filter_complex',filt,'-map','[v]','-map','3:a','-c:v','libx264','-profile:v','high','-level:v','4.0','-crf','16','-preset','veryfast','-r','30','-fps_mode','cfr','-frames:v',str(film['durationInFrames']),'-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-c:a','aac','-b:a','320k','-aac_ms','0','-ar','48000','-ac','2','-t',f'{duration:.9f}','-movflags','+faststart',str(O/'n18_v4.mp4')],'final-encode.log')
 (O/'assembly-time.json').write_text(json.dumps(dict(start=start,end=datetime.datetime.now().astimezone().isoformat(),wall_seconds=time.monotonic()-t,patch_frames=[195,392],video_encoder='libx264 High / CRF 16 / veryfast',audio_encoder='AAC 320 kbps'),indent=1));print('ASSEMBLED',flush=True)

if __name__=='__main__':
 while not (O/'render-time.json').exists():time.sleep(5)
 if not (O/'spatial-render-time.json').exists():raise RuntimeError('corrected spatial shots not ready')
 assemble();measure()
 run([str(W/'.venv/bin/python'),'-u',str(E/'asr_continuous.py'),str(O/'n18_v4.mp4'),'--output=out/asr_final.json'],'asr-final.log')
 print('FINAL CHECKS COMPLETE',flush=True)
