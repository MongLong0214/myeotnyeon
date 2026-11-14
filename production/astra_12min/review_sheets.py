from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
P=Path('/Users/isaac/projects/verdict-kr/work/production/astra_12min')
records=json.loads((P/'representative_v2_manifest.json').read_text())
for r in records:
 fs=r['extracts'];sheet=Image.new('RGB',(426*3,264*(len(fs)//3)),(20,25,30));d=ImageDraw.Draw(sheet)
 for i,x in enumerate(fs):
  im=Image.open(x['path']);xx=i%3*426;yy=i//3*264;sheet.paste(im,(xx,yy));d.text((xx+8,yy+242),f"{x['cue']} {x['phase']} {x['time']:.3f}s",fill='white')
 target=P/(Path(r['path']).stem+'_sheet.png');sheet.save(target);print(target)
