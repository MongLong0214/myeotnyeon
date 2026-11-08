from pathlib import Path
import subprocess,json,hashlib,re,sys,os
import numpy as np,soundfile as sf
W=Path(__file__).resolve().parents[5];O=W/'episodes/v4/n18/cartoon_v4';S=Path(__file__).parent
D=json.loads((O/'shots.json').read_text());main=O/'n18_cartoon_v4_1080p.mp4';share=O/'n18_cartoon_v4_360p.mp4'
# Every contact-sheet image is extracted from the final encoded native render.
frames=[]
for sh in D['shots']:
 for phase in [.28,.72]:frames.append(int(sh['start']+(sh['end']-sh['start'])*phase))
def balanced(v):
 if len(v)==1:return f'eq(n,{v[0]})'
 m=len(v)//2;return '('+balanced(v[:m])+'+'+balanced(v[m:])+')'
selection=balanced(frames);extract=O/'qa/encoded';extract.mkdir(exist_ok=True)
commands=[
 (['ffmpeg','-hide_banner','-y','-i',str(main),'-vf','scale=640:360:flags=lanczos','-c:v','libx264','-preset','fast','-crf','23','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',str(share)],O/'share_render.log'),
 (['ffmpeg','-hide_banner','-i',str(main),'-vf','blackdetect=d=0.10:pix_th=0.10,freezedetect=n=-60dB:d=3','-an','-f','null','-'],O/'video_scan.log'),
 (['ffmpeg','-hide_banner','-y','-threads','2','-filter_threads','1','-i',str(main),'-vf',f"select='{selection}',scale=960:540",'-fps_mode','vfr','-threads','2','-q:v','3',str(extract/'%04d.jpg')],O/'extract.log')]
processes=[];force=os.environ.get("N18_FORCE_FINAL_CHECK")=="1"
for cmd,log in commands:
 if not force and log.name=='share_render.log' and share.exists():
  z=subprocess.run(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(share)],capture_output=True,text=True)
  if z.returncode==0 and float(z.stdout)>455:continue
 if not force and log.name=='video_scan.log' and log.exists() and 'frame=13663' in log.read_text().replace(' ','') and 'video:' in log.read_text():continue
 if not force and log.name=='extract.log' and len(list(extract.glob('*.jpg')))==len(frames):continue
 handle=open(log,'w');processes.append((subprocess.Popen(cmd,stdout=handle,stderr=handle),handle,log))
for p,h,l in processes:
 rc=p.wait();h.close()
 if rc:raise RuntimeError(f'{l}: ffmpeg failed {rc}')
for i,frame in enumerate(frames):
 sh=D['shots'][i//2];dst=O/'qa'/f"{sh['id']}_{'a' if i%2==0 else 'b'}.jpg";dst.write_bytes((extract/f'{i+1:04d}.jpg').read_bytes())
subprocess.run([sys.executable,str(S/'qa.py')],check=True)
q=json.loads((O/'qa.json').read_text());scan=(O/'video_scan.log').read_text();q['picture_scan']={'black_intervals':re.findall(r'black_start:[^\n]+',scan),'freeze_intervals':re.findall(r'lavfi.freezedetect.[^\n]+',scan),'full_stream_decoded':True,'static_detection_min_s':3,'threshold_db':-60}
q['exports']={}
for file in [main,share]:
 p=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(file)]));v=next(z for z in p['streams'] if z['codec_type']=='video');q['exports'][file.name]={'width':v['width'],'height':v['height'],'frames':int(v['nb_frames']),'fps':v['r_frame_rate'],'video_duration_s':float(v['duration']),'container_duration_s':float(p['format']['duration']),'sha256':hashlib.sha256(file.read_bytes()).hexdigest()}
final_pcm=O/'qa/final_audio.wav';subprocess.run(['ffmpeg','-v','error','-y','-i',str(main),'-vn','-c:a','pcm_s16le',str(final_pcm)],check=True)
x,sr=sf.read(final_pcm,always_2d=True);source,osr=sf.read(O/'public/mix.wav',always_2d=True);L=min(len(x),len(source));q['audio']['final_aac_peak_linear']=float(np.max(np.abs(x)));q['audio']['final_aac_clipped_samples']=int(np.sum(np.abs(x)>=1));q['audio']['final_aac_mix_correlation']=float(np.corrcoef(x[:L].reshape(-1)[::32],source[:L].reshape(-1)[::32])[0,1]);q['audio']['final_aac_duration_s']=len(x)/sr
assert all(z['frames']==D['durationInFrames'] for z in q['exports'].values());assert not q['picture_scan']['black_intervals'];assert not q['picture_scan']['freeze_intervals'];assert q['audio']['final_aac_clipped_samples']==0
q['status']='RENDERED_AWAITING_FINAL_VISUAL_REVIEW';q['unfinished']=['Final encoded contact-sheet visual review.'];(O/'qa.json').write_text(json.dumps(q,ensure_ascii=False,indent=2));print('Final exports decoded; sheet.jpg regenerated from every encoded cut.')
