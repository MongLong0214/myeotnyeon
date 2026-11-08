"""Derive the 360p share copy and every-cut QA images from the delivered MP4."""
from pathlib import Path
import json,subprocess,sys
import audio as V
E=V.E;video=E/'n18_cartoon_v5_1080p.mp4'
if '--cuts-only' not in sys.argv:
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(video),'-vf','scale=640:360:flags=lanczos','-c:v','libx264','-preset','fast','-crf','24','-c:a','aac','-b:a','112k','-movflags','+faststart',str(E/'n18_cartoon_v5_360p.mp4')],check=True)
shots=json.loads((E/'episode_data.json').read_text())['shots']
frames=[int(s['start']+(s['end']-s['start'])*.54) for s in shots]
directory=E/'delivered_cut_frames';directory.mkdir(exist_ok=True)
def balanced(parts):
 if len(parts)==1:return parts[0]
 k=len(parts)//2;return '('+balanced(parts[:k])+'+'+balanced(parts[k:])+')'
selection=balanced([f'eq(n,{f})' for f in frames])
subprocess.run(['ffmpeg','-v','error','-y','-i',str(video),'-vf',f"select='{selection}',scale=640:360",'-fps_mode','vfr','-q:v','3',str(directory/'%03d.jpg')],check=True)
for i,s in enumerate(shots,1):
 source=directory/f'{i:03}.jpg';assert source.exists(),source
 (E/'qa_frames'/f'{s["id"]}.jpg').write_bytes(source.read_bytes())
subprocess.run(['ffmpeg','-v','error','-y','-i',str(video),'-t','60','-c','copy','-movflags','+faststart',str(E/'first60_final.mp4')],check=True)
print('360P + DELIVERED CUTS',len(shots),flush=True)
