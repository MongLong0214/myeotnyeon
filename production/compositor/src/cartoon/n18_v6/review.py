"""Extract actual MP4 edit pairs and make the requested human-readable cut sheet."""
import json,math,subprocess,sys
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
from audio import E
fontpath='/System/Library/Fonts/AppleSDGothicNeo.ttc'
font=ImageFont.truetype(fontpath,18);small=ImageFont.truetype(fontpath,15)
data=json.loads((E/'episode_data.json').read_text());shots=data['shots'];caps=data['captions']
def caption(f):return next((c['text'] for c in caps if c['start']<=f<c['end']),'(문장 사이 쉼)')
def wrap(txt,maxlen=52):
 out=[];line=''
 for w in txt.split():
  if line and len(line+' '+w)>maxlen:out.append(line);line=w
  else:line+=(' ' if line else '')+w
 return out+[line] if line else out
def extract():
 folder=E/'delivered_frames';folder.mkdir(exist_ok=True)
 frames=sorted(set([f for s in shots[1:] for f in [s['start']-1,s['start']]]+[int((s['start']+s['end'])/2) for s in shots]))
 def balanced(items):
  if len(items)==1:return f'eq(n\\,{items[0]})'
  k=len(items)//2;return '('+balanced(items[:k])+'+'+balanced(items[k:])+')'
 select=balanced(frames)
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(E/'n18_cartoon_v6_1080p.mp4'),'-vf',f'select={select},scale=640:360','-fps_mode','vfr','-q:v','2',str(folder/'%05d.jpg')],check=True)
 mapping={str(f):str((folder/f'{i+1:05}.jpg').relative_to(E)) for i,f in enumerate(frames)}
 (E/'delivered_frames.json').write_text(json.dumps(mapping,indent=2));return mapping
def sheets(mapping):
 w,h=960,340;rows=[]
 for i,s in enumerate(shots[1:],1):
  row=Image.new('RGB',(w,h),'#181724');d=ImageDraw.Draw(row)
  for side,(f,sh) in enumerate([(s['start']-1,shots[i-1]),(s['start'],s)]):
   im=Image.open(E/mapping[str(f)]).resize((480,270));row.paste(im,(480*side,0))
   d.text((side*480+8,274),f'{sh["id"]}  {f/30:.3f}s  {sh["size"]}  {sh["angle_deg"]}°',font=small,fill='#bcd4c7')
   for j,t in enumerate(wrap(caption(f),29)[:2]):d.text((side*480+8,294+j*20),t,font=font,fill='white')
  rows.append(row)
 full=Image.new('RGB',(w,h*len(rows)),'#181724')
 for i,row in enumerate(rows):full.paste(row,(0,i*h))
 full.save(E/'cut_sheet.jpg',quality=91,subsampling=0)
 for p in range(math.ceil(len(rows)/10)):
  chunk=rows[p*10:(p+1)*10];page=Image.new('RGB',(w,h*len(chunk)),'#181724')
  for j,row in enumerate(chunk):page.paste(row,(0,j*h))
  page.save(E/f'cut_page_{p+1:02}.jpg',quality=91,subsampling=0)
 # Mid-shot frames are also useful for checking what every sentence depicts.
 for p in range(math.ceil(len(shots)/25)):
  chunk=shots[p*25:(p+1)*25];page=Image.new('RGB',(1920,5*280),'#181724');d=ImageDraw.Draw(page)
  for j,s in enumerate(chunk):
   f=int((s['start']+s['end'])/2);x=(j%5)*384;y=(j//5)*280
   page.paste(Image.open(E/mapping[str(f)]).resize((384,216)),(x,y));d.text((x+5,y+218),s['id']+' '+s['size'],font=small,fill='#bcd4c7')
   for k,t in enumerate(wrap(s['text'],25)[:2]):d.text((x+5,y+237+k*19),t,font=small,fill='white')
  page.save(E/f'shot_page_{p+1:02}.jpg',quality=92,subsampling=0)
 print('SHEETS',len(rows),'cuts',len(shots),'shots',flush=True)
if __name__=='__main__':
 mapping=json.loads((E/'delivered_frames.json').read_text()) if len(sys.argv)>1 and sys.argv[1]=='sheets' else extract()
 sheets(mapping)
