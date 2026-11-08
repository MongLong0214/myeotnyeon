from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import json, subprocess
ROOT=Path(__file__).resolve().parent
FONT='/System/Library/Fonts/AppleSDGothicNeo.ttc'
def f(n): return ImageFont.truetype(FONT,n)
data=json.loads((ROOT/'shot_alignment.json').read_text())
out=ROOT/'delivery_frames'; out.mkdir(exist_ok=True)
for s in data:
 t=(s['start_s']+s['end_s'])/2
 subprocess.run(['ffmpeg','-y','-v','error','-ss',str(t),'-i',str(ROOT/'lf2_terra_remake_1080p.mp4'),'-frames:v','1',str(out/(s['id']+'.png'))],check=True)
thumb=(480,270); sheet=Image.new('RGB',(960,300*8),(17,25,30)); d=ImageDraw.Draw(sheet)
for i,s in enumerate(data):
 im=Image.open(out/(s['id']+'.png')).resize(thumb); x=i%2*480; y=i//2*300; sheet.paste(im,(x,y)); d=ImageDraw.Draw(sheet)
 d.text((x+12,y+272),f"{s['id']} {s['start_s']:.0f}–{s['end_s']:.0f}s",font=f(21),fill='#f5ddb1')
sheet.save(ROOT/'lf2_terra_delivery_midframes.png')
print('EXTRACTED',len(data),'direct MP4 midframes')
