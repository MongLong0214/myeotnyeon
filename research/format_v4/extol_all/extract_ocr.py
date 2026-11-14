import json,subprocess,csv,math,concurrent.futures,re
from pathlib import Path
import cv2
from PIL import Image,ImageDraw,ImageFont
cv2.setNumThreads(1)
R=Path(__file__).resolve().parent;inv=json.loads((R/'inventory.json').read_text())
CH={'H_GaGKQp17k':[42,93,352.5,434.3,577.5],'w_LJ_GQObic':[95.2,148.5,218.8,401],'C1eXfwC7uAw':[44,369.8],'OwQm8ZIZfiQ':[130,231,417,474]}
def run(vid):
 d=R/vid
 if not (d/'media.mp4').exists():return
 if (d/'typography_summary.json').exists():return
 m=json.loads((d/'metadata.json').read_text());dur=m['duration'];short=vid in inv['short'];times=[0,1,2,3,max(0,dur-1)] if short else sorted(set([0,1,2,3,7,10,14,15,30,45,59]+[round(x,2) for x in __import__('numpy').linspace(1,dur-1,12)]+CH.get(vid,[])))
 tmp=d/'ocr_frames.internal';tmp.mkdir(exist_ok=True);cap=cv2.VideoCapture(str(d/'media.mp4'));fps=cap.get(cv2.CAP_PROP_FPS);paths=[]
 for t in times:
  cap.set(cv2.CAP_PROP_POS_FRAMES,int(t*fps));ok,im=cap.read()
  if not ok:continue
  h,w=im.shape[:2];im=cv2.resize(im,(min(w,1280),round(h*min(w,1280)/w)));p=tmp/f'{t:08.2f}.jpg';cv2.imwrite(str(p),im);paths.append(p)
 cap.release()
 r=subprocess.run([str(R/'ocr')]+[str(p) for p in paths],stdout=subprocess.PIPE,check=True,text=True);data=json.loads(r.stdout);(d/'ocr.internal.json').write_text(json.dumps(data,ensure_ascii=False,indent=2));rows=[]
 for item in data:
  t=float(Path(item['path']).stem)
  for x in item.get('regions',[]):
   role='subtitle' if x['y_top']>(.55 if short else .8) else 'headline' if short and x['y_top']<.3 else 'date_or_number' if re.search(r'\d+\s*(년|월|일|시|초|m|명|척)|\d+:\d+',x['text']) else 'chapter' if re.search(r'^[0-9]+[. ]',x['text']) else 'label_or_graphic'
   rows.append({'time_s':t,'role_estimate':role,'x_norm':x['x'],'y_norm':x['y_top'],'width_norm':x['width'],'height_norm':x['height'],'box_area_share':x['width']*x['height'],'ocr_confidence':x['confidence'],'character_count':len(x['text']),'note':'Apple Vision ko-KR; boxes not font point sizes; OCR includes misrecognitions. Text not reproduced in this coordinate table.'})
 if rows:
  with (d/'text_regions.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 import statistics
 subs=[x['height_norm'] for x in rows if x['role_estimate']=='subtitle'];heads=[x['height_norm'] for x in rows if x['role_estimate']=='headline']
 summ={'sampled_frame_count':len(paths),'region_count':len(rows),'subtitle_box_height_median_frame_share':statistics.median(subs) if subs else None,'headline_box_height_median_frame_share':statistics.median(heads) if heads else None,'subtitle_present_sample_share':len(set(x['time_s'] for x in rows if x['role_estimate']=='subtitle'))/len(paths) if paths else None,'method':'Apple Vision OCR at <=1280px width; role by location/number patterns; no font family identity inferred','sample_times_s':times};(d/'typography_summary.json').write_text(json.dumps(summ,ensure_ascii=False,indent=2))
 # Six small type crops from source frames, cropped around text region clusters.
 strips=[]
 for item in data[:min(12,len(data))]:
  im=Image.open(item['path']).convert('RGB');w,h=im.size;regs=item.get('regions',[])
  for x in regs:
   if x['confidence']<.5:continue
   a=max(0,int((x['x']-.01)*w));b=max(0,int((x['y_top']-.01)*h));c=min(w,int((x['x']+x['width']+.01)*w));e=min(h,int((x['y_top']+x['height']+.01)*h));crop=im.crop((a,b,c,e));crop.thumbnail((450,75));strips.append(crop)
  if len(strips)>=12:break
 canvas=Image.new('RGB',(500,90*min(12,len(strips))),(20,20,20))
 for i,im in enumerate(strips[:12]):canvas.paste(im,(20,i*90+5))
 if strips:canvas.save(d/'type_crops.jpg',quality=88)
 print(vid,'OCR',len(paths),len(rows),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:list(ex.map(run,inv['long']+inv['short']))
