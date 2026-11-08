from pathlib import Path
import json,subprocess
from PIL import Image,ImageDraw,ImageFont
import numpy as np
W=Path(__file__).resolve().parents[3];OUT=W/'research/metrics';S=Path(__file__).parent
font=ImageFont.truetype(str(W/'production/compositor/public/fonts/Pretendard-Bold.otf'),26)
def shot(p,f,w=432):
 raw=subprocess.run(['ffmpeg','-v','error','-ss',f'{f/30:.8f}','-i',str(p),'-frames:v','1','-vf',f'scale={w}:{w*16//9}','-f','rawvideo','-pix_fmt','rgb24','-'],capture_output=True,check=True).stdout
 return Image.fromarray(np.frombuffer(raw,np.uint8).reshape(w*16//9,w,3))
def main():
 sheet=Image.new('RGB',(5*432,4*824),(16,20,25));draw=ImageDraw.Draw(sheet);manifest={}
 for row,q in enumerate(['q015','q012','q016','q017']):
  p=W/'episodes/quiz'/q/'v51/candidate.mp4';n=json.loads((W/'episodes/quiz'/q/'v51/qa.json').read_text())['duration']['seconds']*30
  fs=[0,15,30,60,round(n)-20];manifest[q]=fs
  for col,f in enumerate(fs):
   x=col*432;y=row*824;draw.text((x+10,y+12),f'{q}   {"CTA" if col==4 else "HOOK"}   f{f} / {f/30:.2f}s',font=font,fill=(240,244,246));sheet.paste(shot(p,f),(x,y+56))
 sheet.save(OUT/'hook_v51_sheet.jpg',quality=95,subsampling=0)
 comp=Image.new('RGB',(6*360,696),(16,20,25));d=ImageDraw.Draw(comp)
 for i,(ver,f) in enumerate([(v,f) for v in ['v3','v5','v51'] for f in [0,30]]):
  d.text((i*360+10,10),f'{ver} q016 | f{f}',font=font,fill=(240,244,246));comp.paste(shot(W/'episodes/quiz/q016/v51/candidate.mp4' if ver == 'v51' else W/'upload'/f'{ver}_q016.mp4',f,360),(i*360,56))
 comp.save(OUT/'hook_v3_v5_v51_q016.jpg',quality=95,subsampling=0);(OUT/'hook_v51_sheet_frames.json').write_text(json.dumps(manifest,indent=2));print('sheets saved')
if __name__=='__main__':main()
