"""Mux the complete final Remotion render with the sample-exact final narration."""
import json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;d=json.loads((P/'episode_data.json').read_text())
patch_file=P/'fix_evidence/label_patches.json'
if patch_file.exists():
 patches=json.loads(patch_file.read_text());cursor=0;clips=[]
 for i,patch in enumerate([*patches,dict(start=d['durationInFrames'],end=d['durationInFrames'])]):
  if patch['start']>cursor:
   gap=P/f'fix_evidence/gap_{i:02}.mp4'
   subprocess.run(['ffmpeg','-v','error','-y','-ss',str(cursor/30),'-i',str(P/'fix_evidence/picture_v6fix_1080p.mp4'),'-frames:v',str(patch['start']-cursor),'-an','-c:v','libx264','-crf','18','-preset','fast','-pix_fmt','yuv420p','-r','30','-video_track_timescale','90000',str(gap)],check=True)
   clips.append(gap)
  if 'path' in patch:clips.append(Path(patch['path']))
  cursor=patch['end']
 concat=P/'fix_evidence/picture_parts.txt'
 concat.write_text(''.join("file '"+str(p.resolve()).replace("'","'\\''")+"'\n" for p in clips))
 repaired=P/'fix_evidence/picture_label_corrected.mp4'
 subprocess.run(['ffmpeg','-v','error','-y','-f','concat','-safe','0','-i',str(concat),'-c','copy',str(repaired)],check=True)
 repaired.replace(P/'fix_evidence/picture_v6fix_1080p.mp4')
 patch_file.rename(P/'fix_evidence/label_patches_applied.json')
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=nb_frames','-of','json',str(P/'fix_evidence/picture_v6fix_1080p.mp4')]))
assert int(probe['streams'][0]['nb_frames'])==d['durationInFrames']
subprocess.run(['ffmpeg','-v','error','-y','-i',str(P/'fix_evidence/picture_v6fix_1080p.mp4'),'-i',str(P/'lf2_cartoon_v6_1080p.mp4'),'-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','copy','-movflags','+faststart',str(P/'lf2_cartoon_v6fix_1080p.mp4')],check=True)
subprocess.run(['ffmpeg','-v','error','-y','-i',str(P/'lf2_cartoon_v6fix_1080p.mp4'),'-vf','scale=640:360','-c:v','libx264','-crf','22','-preset','fast','-pix_fmt','yuv420p','-c:a','copy','-movflags','+faststart',str(P/'lf2_cartoon_v6fix_360p.mp4')],check=True)
print('MUXED',d['durationInFrames'],'frames',flush=True)
