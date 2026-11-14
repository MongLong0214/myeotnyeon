import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
p=Path('/Users/isaac/projects/verdict-kr/work/production/astra_12min/render_verification.json');font=ImageFont.truetype('/System/Library/Fonts/AppleSDGothicNeo.ttc',16)
for r in json.loads(p.read_text()):
 sheet=Image.new('RGB',(1440,295*(len(r['frames'])//3)));d=ImageDraw.Draw(sheet)
 for k,f in enumerate(r['frames']):
  im=Image.open(f['frame']);im.thumbnail((480,270));sheet.paste(im,(480*(k%3),295*(k//3)))
  d.text((480*(k%3)+5,295*(k//3)+272),f['cue']+' '+str(round(f['time'],3))+'s',font=font,fill='white')
 out=Path(r['video']).with_suffix('.review.jpg');sheet.save(out);print(out)
