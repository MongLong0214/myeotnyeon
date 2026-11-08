from pathlib import Path
import json,subprocess
from PIL import Image,ImageDraw,ImageFont
import numpy as np
W=Path(__file__).resolve().parents[3];OUT=W/'research/metrics';font=ImageFont.truetype(str(W/'production/compositor/public/fonts/Pretendard-Bold.otf'),26)
def shot(p,f,w=432):
 raw=subprocess.run(['ffmpeg','-v','error','-ss',f'{f/30:.8f}','-i',str(p),'-frames:v','1','-vf',f'scale={w}:{w*16//9}','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True,check=True).stdout
 return Image.fromarray(np.frombuffer(raw,np.uint8).reshape(w*16//9,w,3))
sheet=Image.new('RGB',(5*432,4*824),(16,20,25));draw=ImageDraw.Draw(sheet);manifest={}
for row,q in enumerate(['q015','q012','q016','q017']):
 p=W/'episodes/quiz'/q/'v52';d=json.loads((p/'render_final.json').read_text());fs=[0,15,30,60,d['durationInFrames']-20];manifest[q]=fs
 for col,f in enumerate(fs):
  x=col*432;y=row*824;draw.text((x+10,y+12),f'v52 {q}   {"CTA" if col==4 else "HOOK"}   f{f}',font=font,fill=(240,244,246));sheet.paste(shot(p/'candidate.mp4',f),(x,y+56))
path=OUT/'hook_v52_sheet.jpg';assert not path.exists();sheet.save(path,quality=95,subsampling=0)
with (OUT/'hook_v52_sheet_frames.json').open('x') as f:json.dump(manifest,f,indent=1)
print('sheet saved',path)
