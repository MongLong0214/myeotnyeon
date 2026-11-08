from pathlib import Path
import json,subprocess
from PIL import Image,ImageDraw
W=Path.cwd();Q=W/'episodes/quiz/q006';P=Q/'v3d_work';D=json.loads((W/'production/compositor/public/q006/render.json').read_text());V=W/'upload/v3d_q006.mp4'
frames=[552,570,590,610,650,675,705,735,768,805,855,925]
phone=sorted({s['from_'] for s in D['subtitles']}|{c['from']+c['dur']-4 for c in D['cues']})
folder=P/'sheet_frames';folder.mkdir(exist_ok=True)
for f in sorted(set(frames+phone)):
 path=folder/f'{f}.png'
 if not path.exists():subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-n','-ss',str(f/30),'-i',str(V),'-frames:v','1',str(path)],check=True)
def make(fs,cols,width,mask,out):
 h=width*16//9; label=28
 sheet=Image.new('RGB',(cols*width,((len(fs)+cols-1)//cols)*(h+label)),(22,22,22));draw=ImageDraw.Draw(sheet)
 for i,f in enumerate(fs):
  im=Image.open(folder/f'{f}.png').convert('RGBA')
  if mask:
   ov=Image.new('RGBA',im.size,(0,0,0,0));d=ImageDraw.Draw(ov)
   for b in [(0,0,110,1920),(970,0,1080,1920),(0,0,1080,190),(0,1540,1080,1920),(880,900,1080,1920)]:d.rectangle(b,fill=(255,0,80,85))
   im=Image.alpha_composite(im,ov)
  x,y=(i%cols)*width,(i//cols)*(h+label);im=im.convert('RGB').resize((width,h),Image.Resampling.LANCZOS);sheet.paste(im,(x,y+label))
  cue=next(c for c in D['cues'] if c['from']<=f<c['from']+c['dur'])
  draw.text((x+6,y+7),f'{f:03d}f | {f/30:.3f}s | {cue["scene"]}',fill=(238,232,220))
 sheet.save(out,quality=95)
make(frames,4,270,False,W/'research/format_v4/type_v2/q006_v3d_sheet.jpg')
make(phone,6,270,True,Q/'phone_sheet_v3d.png')
(P/'sheet_frames.json').write_text(json.dumps(dict(contact=frames,phone=phone),indent=2));print('Contact',len(frames),'phone',len(phone))
