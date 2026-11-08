from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np,subprocess,json,math
W=Path(__file__).resolve().parents[3];R=W/'research/metrics';R.mkdir(parents=True,exist_ok=True)

def selected(path, frames, w=180, h=320):
 expr='+'.join(f'eq(n\\,{f})' for f in frames)
 r=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-vf',f'select={expr},scale={w}:{h}','-fps_mode','passthrough','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True,check=True)
 step=w*h*3;assert len(r.stdout)==step*len(frames),(len(r.stdout),len(frames))
 return {f:Image.frombytes('RGB',(w,h),r.stdout[i*step:(i+1)*step]) for i,f in enumerate(frames)}
def main():
 qs=['q015','q012','q016','q017'];cols=9;tw=180;th=344;blocks=[];meta={}
 for q in qs:
  p=W/'episodes/quiz'/q/'v5';n=json.loads((p/'render.json').read_text())['durationInFrames'];frames=[0,4,15,30,45,60]+list(range(n-45,n));meta[q]=frames
  im=Image.new('RGB',(cols*tw,36+math.ceil(len(frames)/cols)*th),'#151922');d=ImageDraw.Draw(im);d.text((10,10),f'{q} | hook 0,4,15,30,45,60 + ALL final 45 frames',fill='white')
  tiles=selected(p/('candidate_r6.mp4' if q=='q012' else 'candidate_r4.mp4'),frames)
  for i,f in enumerate(frames):
   tile=tiles[f];x=i%cols*tw;y=36+i//cols*th;im.paste(tile,(x,y));d.text((x+5,y+322),f'{q} f{f}  {f/30:.3f}s',fill='#FFDE66')
  blocks.append(im);print(q,'sheet',flush=True)
 out=Image.new('RGB',(cols*tw,sum(x.height for x in blocks)),'#151922');y=0
 for im in blocks:out.paste(im,(0,y));y+=im.height
 out.save(R/'hook_v5_sheet.jpg',quality=92)
 (R/'hook_v5_sheet_frames.json').write_text(json.dumps(meta,indent=1))
 fs=[0,4,15,30,45,60];w=2160;out=Image.new('RGB',(w,374),'#151922');d=ImageDraw.Draw(out)
 old=selected(W/'upload/v3_q016.mp4',fs);new=selected(W/'episodes/quiz/q016/v5/candidate_r4.mp4',fs)
 for i,f in enumerate(fs):
  x=i*360;d.text((x+8,8),f'q016 f{f} | v3        v5',fill='white')
  for j,tiles in enumerate([old,new]):out.paste(tiles[f],(x+j*180,36))
 out.save(R/'hook_v3_vs_v5_q016.jpg',quality=94)
if __name__=='__main__':main()
