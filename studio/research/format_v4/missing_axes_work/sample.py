from PIL import Image,ImageDraw,ImageFont
from pathlib import Path
import csv,json,numpy as np
R=Path('research/format_v4/extol_all');O=Path('research/format_v4/missing_axes_work');font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',13)
for vid in ['H_GaGKQp17k','w_LJ_GQObic','C1eXfwC7uAw','_qQK1LZpyJI']:
 rows=list(csv.DictReader((R/vid/'cuts.csv').open()));idx=np.linspace(0,len(rows)-2,40).round().astype(int);out=[]
 canvas=Image.new('RGB',(1200,8*159),(16,16,19));dr=ImageDraw.Draw(canvas)
 pairs=Image.new('RGB',(1080,20*124),(16,16,19));pd=ImageDraw.Draw(pairs)
 for j,i in enumerate(idx):
  i=int(i)
  sh=Image.open(R/vid/f'shots_{i//36+1:02}.jpg');mid=sh.crop(((i%36)%6*240,(i%36)//6*157+22,(i%36)%6*240+240,(i%36)//6*157+157))
  canvas.paste(mid,((j%5)*240,(j//5)*159+22));dr.text(((j%5)*240+3,(j//5)*159+3),f'{j+1:02} S{i+1} {float(rows[i]["start_s"]):.1f}s',font=font,fill='white')
  # boundary i+1 ends shot i+1. first and fourth columns are same-shot -0.3s/-1f
  strip=Image.open(R/vid/f'boundaries_{i//12+1:02}.jpg');y=(i%12)*124+22
  x=(j%2)*540;yy=(j//2)*124
  pairs.paste(strip.crop((0,y,180,y+102)),(x,yy+22));pairs.paste(strip.crop((540,y,720,y+102)),(x+180,yy+22));pairs.paste(mid.resize((180,102)),(x+360,yy+22));pd.text((x+3,yy+3),f'{j+1:02} S{i+1}: end-.3 / end-1f / midpoint',font=font,fill='white')
  out.append(dict(sample=j+1,shot=i+1,**rows[i]))
 canvas.save(O/f'{vid}_40.jpg',quality=92);pairs.save(O/f'{vid}_pairs.jpg',quality=90)
 (O/f'{vid}_sample.json').write_text(json.dumps(out,indent=2))
 print(vid,len(rows))
