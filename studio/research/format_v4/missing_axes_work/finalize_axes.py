import csv,json,re
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
O=Path('research/format_v4/missing_axes_work');R=Path('research/format_v4/extol_all')
labels={
'H_GaGKQp17k':{'human3d':[1,3,5,6,9,12,13,14,16,17,18,19,21,23,27,28,31,35,37,38,39],'human_other':[7,25,40],'text':[1,7,8,9,10,19,25,26,30,31,32,33]},
'w_LJ_GQObic':{'human3d':list(range(2,14))+[19,20,21,22,23,32,34,37],'human_other':[16,17,18,24,25,26,27,29,31,33,35,38,39],'text':[1,10,15,16,17,18,24,25,26,27,28,29,30,33,35,36,40]},
'C1eXfwC7uAw':{'human3d':[3,5,7,8,11,13,14,16,17,18,19,20,22,26,33,34,35,36],'human_other':[4,9,10,25,27,28,29,31,37,38,39,40],'text':[1,6,8,9,10,18,25,28,29,30,31,33,34,37,38,39,40]},
'_qQK1LZpyJI':{'human3d':[4,5,6,7,12,13,14,15,22,23,26,27,28,29,30,38,39,40],'human_other':[1,2,3,18,19,20,21,24,32,33,34,35,36],'text':[5,8,9,10,11,12,37,38,40]},
'N18':{'human3d':[],'human_other':[],'text':list(range(1,41))}}
allrows=[];summary=[]
for v,L in labels.items():
 samples=json.load(open(O/f'{v}_sample.json'));ocr=json.load(open(O/f'{v}_ocr.json'));pairs=json.load(open(O/f'{v}_motion.json'))
 logs=list(csv.DictReader(open(R/v/'flow.csv'))) if v!='N18' else None
 rows=[]
 for j,r in enumerate(samples):
  i=j+1;regions=[]
  for b in ocr[j].get('regions',[]):
   y=b['y_top'];x=b['text']
   is_sub=(.72<=y<.87) if v=='N18' else y>=.785
   if not is_sub and b['confidence']>=.3 and re.search('[가-힣A-Za-z0-9]',x):regions.append(x)
  # Manual presence annotation suppresses OCR detections that are only grain/geometry.
  if i not in L['text']:regions=[]
  words=sum(len(re.findall(r'\S*[가-힣A-Za-z0-9]\S*',x)) for x in regions)
  f0=float(logs[r['shot']-1]['flow_mean_px_per_s_at_320w']) if logs else r['flow'];f1=pairs[j]['end_pair_flow_px_per_s_320w']
  motion=max(f0,f1)>=2
  row=dict(video=v,sample=i,shot=r['shot'],start_s=r['start_s'],duration_s=r['duration_s'],human_visible=i in L['human3d'] or i in L['human_other'],human_3d=i in L['human3d'],motion_estimate=motion,non_subtitle_text=i in L['text'],non_subtitle_ocr_words=words,flow_fullshot=f0,flow_end_pair=f1,ocr_text=' | '.join(regions));rows.append(row);allrows.append(row)
 sec=sum(float(x['duration_s']) for x in rows);summary.append(dict(video=v,n=40,human=sum(x['human_visible'] for x in rows),human3d=sum(x['human_3d'] for x in rows),motion=sum(x['motion_estimate'] for x in rows),text=sum(x['non_subtitle_text'] for x in rows),ocr_words=sum(x['non_subtitle_ocr_words'] for x in rows),sample_seconds=sec,wpm=sum(x['non_subtitle_ocr_words'] for x in rows)*60/sec))
with (O/'annotations.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(allrows[0]));w.writeheader();w.writerows(allrows)
(O/'summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2));print(json.dumps(summary,indent=2))
# One requested character shot grid, solely from the saved Extol representative frames.
choices=[('H_GaGKQp17k',31),('H_GaGKQp17k',35),('H_GaGKQp17k',37),('w_LJ_GQObic',9),('w_LJ_GQObic',20),('w_LJ_GQObic',34),('C1eXfwC7uAw',8),('C1eXfwC7uAw',13),('C1eXfwC7uAw',14),('_qQK1LZpyJI',12),('_qQK1LZpyJI',22),('_qQK1LZpyJI',27)]
canvas=Image.new('RGB',(1200,4*249),(14,16,20));dr=ImageDraw.Draw(canvas);font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',15)
for j,(v,i) in enumerate(choices):
 row=next(x for x in allrows if x['video']==v and x['sample']==i);x=j%3*400;y=j//3*249;canvas.paste(Image.open(O/v/f'{i:02}.jpg').resize((400,225)),(x,y+24));dr.text((x+5,y+3),f'{v} / S{row["shot"]} / {float(row["start_s"]):.1f}s',font=font,fill=(225,227,230))
canvas.save('research/format_v4/extol_character_grid.jpg',quality=93)
