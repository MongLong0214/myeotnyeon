#!/usr/bin/env python3
from pathlib import Path
import json, subprocess, hashlib
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).parent; rows=json.loads((ROOT/'shot_alignment.json').read_text()); W,H=1920,1080
font=lambda n: ImageFont.truetype('/System/Library/Fonts/AppleSDGothicNeo.ttc',n,index=1)
def grab(video,t,out): subprocess.run(['ffmpeg','-y','-ss',f'{t:.3f}','-i',str(video),'-frames:v','1',str(out)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
def sheet(name, indices, cols=4):
 thumbs=[]
 for i in indices:
  r=rows[i]; p=ROOT/'qa_extracts'/f'{name}_{i:03d}.jpg'; grab(ROOT/'n18_terra_remake_1080p.mp4',(r['start_s']+r['end_s'])/2,p)
  im=Image.open(p).resize((480,270)); thumbs.append((i,im,r))
 rowsn=(len(thumbs)+cols-1)//cols; out=Image.new('RGB',(cols*480,rowsn*320),(24,28,29)); d=ImageDraw.Draw(out)
 for n,(i,im,r) in enumerate(thumbs):
  x=(n%cols)*480;y=(n//cols)*320;out.paste(im,(x,y));d.text((x+10,y+276),f'{r["shot_id"]}  {r["start_s"]:.1f}–{r["end_s"]:.1f}s',font=font(20),fill='white')
 out.save(ROOT/f'{name}.jpg',quality=94)
ROOT.joinpath('qa_extracts').mkdir(exist_ok=True)
# all 67 actual final-MP4 middle frames across 2 readable sheets
sheet('shot_middles_01',list(range(0,36)),4);sheet('shot_middles_02',list(range(36,len(rows))),4)
# selected semantic/high-impact cut boundaries: prior end and next first frame actual delivery
impact=[0,1,19,25,31,38,45,51,58,63]
items=[]
for i in impact:
 r=rows[i]; t=max(0,r['start_s']-.04);p=ROOT/'qa_extracts'/f'boundary_before_{i:03d}.jpg';grab(ROOT/'n18_terra_remake_1080p.mp4',t,p)
 q=ROOT/'qa_extracts'/f'boundary_after_{i:03d}.jpg';grab(ROOT/'n18_terra_remake_1080p.mp4',r['start_s']+.04,q)
 for lab,path in [('BEFORE',p),('AFTER',q)]:items.append((i,lab,Image.open(path).resize((480,270)),r))
out=Image.new('RGB',(1920,((len(items)+3)//4)*320),(24,28,29));d=ImageDraw.Draw(out)
for n,(i,lab,im,r) in enumerate(items):
 x=n%4*480;y=n//4*320;out.paste(im,(x,y));d.text((x+10,y+276),f'{lab} {r["shot_id"]} {r["start_s"]:.1f}s',font=font(20),fill='white')
out.save(ROOT/'impact_cut_boundaries.jpg',quality=94)
# programmatic alignment and simple output facts
assert len(rows)==67 and len({r['index'] for r in rows})==67
assert all(r['end_s']>r['start_s'] for r in rows)
report={'shots':len(rows),'duplicate_indices':len(rows)!=len({r['index'] for r in rows}),'coverage_start_s':rows[0]['start_s'],'coverage_end_s':rows[-1]['end_s'],'middle_sheets':['shot_middles_01.jpg','shot_middles_02.jpg'],'impact_boundaries':'impact_cut_boundaries.jpg','status':'PASS: 67 unique source-aligned visual beats with positive durations'}
(ROOT/'qa_report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
