"""Sequential Blender render, mux exact new narration, decode and extract evidence."""
import json,subprocess,math,hashlib,sys
from pathlib import Path
P=Path('/Users/isaac/projects/verdict-kr/work/production/astra_12min');ROOT=P.parents[1]
def run(cmd,log=None):
 if log:
  with log.open('w') as f:subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT,check=True)
 else:subprocess.run(cmd,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
manifest=[]
for name,base in json.loads((P/'representatives.json').read_text()).items():
 if len(sys.argv)>1 and name not in sys.argv[1:]:continue
 out=ROOT/'episodes'/base['episode']/'astra_12min';cp=out/f'{name}_cues.json';clip=json.loads(cp.read_text());paths=[];offset=0;actual=[]
 for i,c in enumerate(clip['cues']):
  print('RENDER',name,c['id'],flush=True)
  dest=out/f"{c['id']}_ink_v2.mp4";frames=out/'ink_frames_v2'/c['id'];n=math.ceil((c['end']-c['start'])*12)
  if not dest.exists():
   run(['/Applications/Blender.app/Contents/MacOS/Blender','-b','-t','2','--python',str(P/'draw_scene.py'),'--',str(cp),str(i)],P/f"render_{c['id']}.log")
   assert len(list(frames.glob('frame_*.png')))==n,(c['id'],n)
   run(['ffmpeg','-y','-v','error','-threads','2','-framerate','12','-i',str(frames/'frame_%04d.png'),'-i',c['audio'],'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-threads','2','-c:a','aac','-b:a','128k','-shortest',str(dest)])
  dur=float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(dest)]))
  actual.append(dict(c,delivered_start=offset,delivered_end=offset+dur,video=str(dest)));offset+=dur;paths.append(dest)
 concat=out/f'{name}_concat.txt';concat.write_text(''.join("file '"+str(x)+"'\n" for x in paths));final=out/f'{name}_NEWv2_426x240.mp4'
 run(['ffmpeg','-y','-v','error','-f','concat','-safe','0','-i',str(concat),'-c','copy','-movflags','+faststart',str(final)])
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(final)]));run(['ffmpeg','-v','error','-threads','2','-i',str(final),'-f','null','-'],P/f'{name}_decode.log')
 ev=out/'review_frames_v2';ev.mkdir(exist_ok=True);extract=[]
 for c in actual:
  for phase,ratio in [('before',.08),('during',.50),('after',.90)]:
   t=c['delivered_start']+(c['delivered_end']-c['delivered_start'])*ratio;png=ev/f"{c['id']}_{phase}.png";run(['ffmpeg','-y','-v','error','-ss',str(t),'-i',str(final),'-frames:v','1',str(png)]);extract.append(dict(cue=c['id'],phase=phase,time=t,path=str(png),text=c['text']))
 record=dict(path=str(final),sha256=hashlib.sha256(final.read_bytes()).hexdigest(),probe=probe,full_decode=True,cues=actual,extracts=extract,visual_review='pending',listening='not performed',continuous_watch='not performed',full_720_seconds=False)
 (out/f'{name}_v2_manifest.json').write_text(json.dumps(record,ensure_ascii=False,indent=2));manifest.append(record)
 print('DONE',name,probe['format']['duration'],flush=True)
(P/'representative_v2_manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2))
