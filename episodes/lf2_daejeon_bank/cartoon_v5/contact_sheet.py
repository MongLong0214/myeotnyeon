"""Every final cut midpoint plus review pages, decoded from the encoded video."""
import json,subprocess,math
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent;d=json.loads((P/'episode_data.json').read_text());q=P/'qa';(q/'cuts').mkdir(exist_ok=True)
frames=[s['start']+(s['end']-s['start'])//2 for s in d['shots']]
def balanced(seq):
 if len(seq)==1:return seq[0]
 mid=len(seq)//2;return '('+balanced(seq[:mid])+')+('+balanced(seq[mid:])+')'
select=balanced([f'eq(n,{f})' for f in frames])
subprocess.run(['ffmpeg','-v','error','-y','-i',str(P/'lf2_cartoon_v5_1080p.mp4'),'-vf',f"select='{select}',scale=384:216",'-fps_mode','vfr',str(q/'cuts/%04d.jpg')],check=True)
font=ImageFont.truetype('/System/Library/Fonts/Menlo.ttc',13)
def sheet(subset,out,cols,width):
 cellh=width*9//16+34;im=Image.new('RGB',(cols*width,math.ceil(len(subset)/cols)*cellh),'#17142a');dr=ImageDraw.Draw(im)
 for j,(idx,s) in enumerate(subset):
  tile=Image.open(q/'cuts'/f'{idx+1:04}.jpg').resize((width,width*9//16));x=(j%cols)*width;y=(j//cols)*cellh;im.paste(tile,(x,y));dr.text((x+5,y+tile.height+4),f"{s['id']} {s['start']/30:.2f}s {s['action']}",font=font,fill='white')
 im.save(out,quality=90)
indexed=list(enumerate(d['shots']));sheet(indexed,P/'sheet.jpg',8,256)
for k in range(0,len(indexed),40):sheet(indexed[k:k+40],q/f'sheet_{k//40+1:02}.jpg',5,384)
print('SHEET',len(indexed),'cuts')
