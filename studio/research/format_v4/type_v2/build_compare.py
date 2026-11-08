from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
import json,subprocess
HERE=Path(__file__).resolve().parent
WORK=HERE.parents[2]
OLD=HERE/'old';OLD.mkdir(exist_ok=True)
for name,sec in [('short_header',2),('short_choices',19),('short_reason',21.8),('short_verdict',29)]:
 out=OLD/f'{name}.png'
 if not out.exists():subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-ss',str(sec),'-i',str(WORK/'upload/v3b_q006.mp4'),'-frames:v','1','-y',str(out)],check=True)
def oldn(i):return WORK/f'episodes/v4/n18/rep2/V4N18-REP{i}.png'
def still(name):return HERE/'stills'/f'{name}.png'
def ref(id):return HERE/'crops'/f'{id}.png'
# Rows show the relevant element; crop boxes are source-pixel coordinates, never painted replacements.
rows=[
 ('01  DOCUMENTARY / CHAPTER',[ref('C04')],oldn(1),still('n18_chapter'),None,None,'C04 / R2 F2900','Nearest baseline: small chapter label in REP1'),
 ('02  DOCUMENTARY / DATE',[ref('C01')],oldn(1),still('n18_scene'),(480,20,1440,155),(480,20,1440,155),'C01 / R2 F150','Date line only; same crop in OLD / NEW'),
 ('03  DOCUMENTARY / SUBTITLE',[ref('C02')],oldn(1),still('n18_scene'),(180,900,1740,1000),(180,900,1740,1000),'C02 / R2 F2688, supplied 640px zoom','Fixed lower baseline / one line'),
 ('04  DOCUMENTARY / DOSSIER',[ref('C05')],oldn(3),still('n18_dossier'),None,None,'C05 / R2 F3100','Nearest baseline: old verdict panel; no old dossier existed'),
 ('05  DOCUMENTARY / EVIDENCE LABEL',[ref('C19'),ref('C20')],oldn(1),still('n18_scene'),(540,220,930,410),(540,220,930,410),'C19 + C20 / Extol top-video role labels','Scene-attached square label / hard pointer'),
 ('06  DOCUMENTARY / MEASUREMENT',[ref('C03')],oldn(2),still('n18_measurement'),None,None,'C03 / R2 F900','Measurement attached to the subjects; no number panel'),
 ('07  DOCUMENTARY / VERDICT',[ref('C06')],oldn(3),still('n18_verdict'),None,None,'C06 / R2 F15200','Sentence appended to the existing record'),
 ('08  DOCUMENTARY / SOURCE',[ref('C16')],oldn(3),still('n18_verdict'),(0,980,1200,1080),(0,1010,1200,1080),'C16 / R1 F17184, supplied 640px zoom','Small fixed credit; retain frame context at source edge'),
 ('09  SHORT / HEADER',[ref('C26'),ref('C24')],OLD/'short_header.png',still('q006_header'),(0,155,1080,420),(0,155,1080,420),'C26 + C24 / Redthread top thumbnails','Two dense lines / left registration / white and red'),
 ('10  SHORT / SUBTITLE',[ref('C02'),ref('C25')],OLD/'short_header.png',still('q006_header'),(40,1330,1000,1530),(40,1220,1000,1425),'C02 + C25 / R2 subtitle + outlined thumbnail type','Two-line portrait adaptation / hard edge shadow'),
 ('11  SHORT / CHOICES',[ref('C17')],OLD/'short_choices.png',still('q006_choices'),(40,460,1040,1330),(0,450,1080,1210),'C17 / R1 F17000 black strips on printed evidence','Three rows on one paper object; no highlighted answer'),
 ('12  SHORT / REASON',[ref('C05'),ref('C07')],OLD/'short_reason.png',still('q006_reason'),(40,460,1040,1330),(0,450,1080,1210),'C05 + C07 / serif dossier labels','Single reported reason / serif hierarchy / record grid'),
 ('13  SHORT / VERDICT',[ref('C06'),ref('C24')],OLD/'short_verdict.png',still('q006_verdict'),(40,460,1040,1330),(0,450,1080,1210),'C06 + C24 / appended record + red headline','Prison term and suspended sentence together'),
]
FONT='/System/Library/Fonts/Supplemental/Arial.ttf'
f=ImageFont.truetype(FONT,29);small=ImageFont.truetype(FONT,22);head=ImageFont.truetype(FONT,38)
W=2560; rowH=620; H=190+len(rows)*rowH
im=Image.new('RGB',(W,H),'#eae6dc');d=ImageDraw.Draw(im)
d.text((28,20),'MNN / TYPOGRAPHY 02 — CTO REVIEW',font=head,fill='#171713')
d.text((28,75),'13 element comparisons · reference / existing output / opt-in new still · no episode rerenders',font=small,fill='#4c4c44')
xs=[28,874,1720];cw=812
for x,t in zip(xs,['REFERENCE','OLD  /  V4 + V3B','NEW  /  TYPE 02']):d.text((x,125),t,font=f,fill='#171713')
manifest=[]
def paste_fit(path,box,x,y,w,h):
 src=Image.open(path).convert('RGB')
 if box:src=src.crop(box)
 k=min(w/src.width,h/src.height);sz=(max(1,round(src.width*k)),max(1,round(src.height*k)));src=src.resize(sz,Image.Resampling.LANCZOS)
 im.paste(src,(x+(w-sz[0])//2,y+(h-sz[1])//2))
for i,(title,refs,old,new,ob,nb,citation,note) in enumerate(rows):
 y=190+i*rowH;d.line((28,y-5,W-28,y-5),fill='#a6a397',width=2);d.text((28,y+12),title,font=f,fill='#191a15');top=y+65;pictureH=455
 for x in xs:d.rectangle((x,top,x+cw,top+pictureH),fill='#d7d3c9')
 if i==1:
  # The date is the top band of the reference frame, not its subtitle.
  r=Image.open(refs[0]);b=(int(r.width*.22),0,int(r.width*.78),int(r.height*.23));paste_fit(refs[0],b,xs[0],top,cw,pictureH)
 else:
  for j,r in enumerate(refs):paste_fit(r,None,xs[0],top+j*pictureH//len(refs),cw,pictureH//len(refs)-3)
 paste_fit(old,ob,xs[1],top,cw,pictureH);paste_fit(new,nb,xs[2],top,cw,pictureH)
 d.text((28,top+pictureH+13),citation,font=small,fill='#33362c');d.text((874,top+pictureH+13),note,font=small,fill='#33362c')
 d.text((1720,top+pictureH+43),new.name+' / frame 90',font=small,fill='#4a4b40')
 manifest.append(dict(element=title,reference=[str(r.relative_to(HERE)) for r in refs],old=str(old),new=str(new),old_crop=ob,new_crop=nb,note=note))
im.save(HERE/'compare.png');(HERE/'compare_sources.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2));print('Saved compare.png',im.size)
