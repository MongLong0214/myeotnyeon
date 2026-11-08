from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import csv,json
HERE=Path(__file__).resolve().parent
ROOT=Path('$HOME/Downloads/Verdict_Production_Final_v5/reference_analysis/full_frames')
IDX={(r['reference'],int(r['frame_zero_based'])):r for r in csv.DictReader((ROOT/'frame_index.csv').open(encoding='utf-8-sig'))}
entries=[]
def add(ref,f,role,box=None,zoom=None):
 r=IDX[ref,f];x=(int(r['tile_column_1based'])-1)*256;step,h=(165,144) if ref=='R2' else (130,110);y=44+(int(r['tile_row_1based'])-1)*step
 im=Image.open(ROOT/r['page_path']).crop((x,y,x+256,y+h))
 source=f"{r['page_path']} r{r['tile_row_1based']} c{r['tile_column_1based']}"
 if zoom is not None:
  z=Image.open(ROOT/'zoom'/zoom[0]);zx=zoom[1]%3*640;zy=64+zoom[1]//3*387 if ref=='R1' else 70+zoom[1]//3*388
  # Zoom page dimensions are uniformly scaled by image viewer; actual geometry below.
  header=64 if ref=='R1' else 70
  # Derive row stride from 5-row source sheet.
  header=64 if z.width==1920 else 70
  stride=(z.height-header)//5
  zy=header+zoom[1]//3*stride
  im=z.crop((zx,zy,zx+640,zy+(275 if ref=='R1' else 360)));source+=f'; zoom/{zoom[0]} tile {zoom[1]+1}'
 if box: im=im.crop(tuple(round(v*s) for v,s in zip(box,[im.width,im.height,im.width,im.height])))
 id=f'C{len(entries)+1:02d}';im.save(HERE/'crops'/f'{id}.png')
 entries.append(dict(id=id,reference=ref,frame=f,tc=r['native_tc'],role=role,source=source,box=box,file=f'crops/{id}.png'))
add('R2',150,'date + subtitle')
add('R2',2688,'one-line subtitle',(.1,.76,.9,.99),zoom=('zoom_3_1.jpg',2))
add('R2',900,'measurement dotted arc')
add('R2',2900,'chapter / lime noise')
add('R2',3100,'dossier / accumulated lines')
add('R2',15200,'dossier / sentence appended')
add('R2',7200,'name + biographical line')
add('R2',3400,'date above action')
add('R2',10800,'archive news / captions')
add('R2',15400,'evidence text on paper')
add('R2',8100,'room number in scene',(.38,0,.75,.42))
add('R2',12000,'chapter / particulate entrance')
add('R1',100,'disclaimer / small serif',(.28,.3,.72,.7))
add('R1',24425,'chapter / paper texture',(.3,.3,.7,.7))
add('R1',18025,'date / lower left', (0,.73,.5,1))
add('R1',17184,'photo credit / source', (0,.86,.65,1),zoom=('zoom_1_1.jpg',0))
add('R1',17000,'evidence / names on strips')
add('R1',16350,'date over photograph')
meta=json.loads((HERE/'thumbnails/manifest.json').read_text())
for m in meta:
 if m['channel']=='extol' and m['rank']==2:continue
 im=Image.open(HERE/'thumbnails'/m['file'])
 # Keep subject context around the headline. Extol uses scene anchored role labels.
 box=(.02,.08,.99,.58) if m['channel']=='doc844' else ((.0,.45,1,1) if m['channel']=='redthread' else (.03,.04,.97,.65))
 if m['channel']=='doc844' and m['rank']==3: box=(.02,.02,.99,.99)
 im=im.crop(tuple(int(v*s) for v,s in zip(box,[im.width,im.height,im.width,im.height])))
 id=f'C{len(entries)+1:02d}';im.save(HERE/'crops'/f'{id}.png');entries.append(dict(id=id,reference=m['channel'],role='thumbnail headline / role label',source=m['url'],watch=f'https://www.youtube.com/watch?v={m["id"]}',file=f'crops/{id}.png',box=box))
(HERE/'crops.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2))
f=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',24);small=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',19)
W=2560; cellW=640;cellH=440;out=Image.new('RGB',(W,160+7*cellH),'#ede9df');d=ImageDraw.Draw(out)
d.text((30,20),'MNN / TYPE 02 — REFERENCE BOARD',font=f,fill='#151515');d.text((30,65),'R2 first / R1 second / channel thumbnails third · 26 text-bearing crops',font=small,fill='#454545')
for i,e in enumerate(entries):
 x=i%4*cellW;y=130+i//4*cellH;im=Image.open(HERE/e['file']);scale=min(608/im.width,342/im.height);im=im.resize((round(im.width*scale),round(im.height*scale)));out.paste(im,(x+16,y+(342-im.height)//2));d.text((x+16,y+350),f'{e["id"]}  {e["reference"]}  {e.get("tc","")}',font=f,fill='#171717');d.text((x+16,y+387),e['role'],font=small,fill='#444')
out.save(HERE/'ref_board.png')
print('Saved',len(entries),'crops',out.size)
