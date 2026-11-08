from analyze import *
from collections import Counter,defaultdict
chapters=json.loads((R/'chapters.json').read_text());groups=defaultdict(list);rows=[]
cap=cv2.VideoCapture(str(R/'tmp/ref_proxy.mp4'));dur=meta('ref')['duration'];fps=30
for sec in range(math.ceil(dur)):
 cap.set(cv2.CAP_PROP_POS_FRAMES,min(round((sec+.5)*fps),meta('ref')['frames']-1));ok,im=cap.read()
 if not ok:raise ValueError(sec)
 a=cv2.resize(im,(160,90));hsv=cv2.cvtColor(a,cv2.COLOR_BGR2HSV);g=cv2.cvtColor(a,cv2.COLOR_BGR2GRAY);h,s,v=cv2.split(hsv);rgb=cv2.cvtColor(a,cv2.COLOR_BGR2RGB);name=next(c['name'] for c in chapters if c['start_s']<=sec+.5<c['end_s']);groups[name].append(rgb.reshape(-1,3)[::6])
 center=g[22:68,40:120];corners=np.r_[g[:15,:25].ravel(),g[:15,-25:].ravel(),g[-15:,:25].ravel(),g[-15:,-25:].ravel()]
 rows.append({'time_s':min(sec+.5,dur-.01),'chapter':name,'mean_luma':float(g.mean()),'dark_luma_below32_share':float((g<32).mean()),'low_sat_share':float((s<50).mean()),'red_share':float((((h<10)|(h>170))&(s>128)&(v>90)).mean()),'yellow_share':float(((h>=20)&(h<=40)&(s>128)&(v>90)).mean()),'blue_share':float(((h>=100)&(h<=135)&(s>128)&(v>90)).mean()),'laplacian_variance_at160w':float(cv2.Laplacian(g,cv2.CV_64F).var()),'highpass_std_at160w':float((g.astype(float)-cv2.GaussianBlur(g,(0,0),1)).std()),'corner_minus_center_luma':float(corners.mean()-center.mean()),'top_bottom_veryblack_share':float(np.r_[g[:3].ravel(),g[-3:].ravel()].__lt__(4).mean())})
cap.release();csvwrite(R/'visual_metrics_1s.csv',rows);palette=[]
for c in chapters:
 pixels=np.concatenate(groups[c['name']]).astype(np.float32);cv2.setRNGSeed(7);_,labels,centers=cv2.kmeans(pixels,5,None,(cv2.TERM_CRITERIA_EPS+cv2.TERM_CRITERIA_MAX_ITER,30,.2),3,cv2.KMEANS_PP_CENTERS);counts=Counter(labels.ravel());colors=[{'hex':'#'+''.join(f'{max(0,min(255,int(round(v)))):02x}' for v in centers[k]),'pixel_share':n/len(labels)} for k,n in counts.most_common()];rs=[r for r in rows if r['chapter']==c['name']]
 palette.append({'chapter':c['name'],'samples':len(rs),'palette':colors,**{k:float(np.mean([r[k] for r in rs])) for k in list(rows[0])[2:]}})
dump(R/'palette_by_section.json',palette)
# Representative contact sheet and precise measured pixel masks for native subtitle/chapter text.
sys.path.insert(0,str(R));from supplement import sheet
keytimes=[2.8,8,11.25,20,42,57.5,90,126,131.5,139,151,188,194,235,241,326,388,417.5,434,500]
sheet(keytimes,'frames_key.jpg',4,(480,270));dump(R/'frames_key_times.json',keytimes)
im8=np.array(Image.open(R/'tmp/native08.png').convert('RGB'));im131=np.array(Image.open(R/'tmp/native131.png').convert('RGB'))
def maskmeasure(im,box):
 x0,y0,x1,y1=box;a=im[y0:y1,x0:x1];h=cv2.cvtColor(a,cv2.COLOR_RGB2HSV);mask=(h[:,:,1]<25)&(h[:,:,2]>230);yy,xx=np.where(mask);return {'roi_xyxy':box,'threshold':'HSV S<25,V>230','white_ink_bbox_xyxy':[int(xx.min()+x0),int(yy.min()+y0),int(xx.max()+x0+1),int(yy.max()+y0+1)],'white_ink_pixels':int(mask.sum()),'glyph_height_px':int(yy.max()-yy.min()+1),'glyph_width_px':int(xx.max()-xx.min()+1)}
type_metrics={'subtitle_t8':maskmeasure(im8,[320,900,1600,990]),'chapter_t131_5':maskmeasure(im131,[1100,110,1650,260]),'font_warning':'Glyph pixel bounds are measured, CSS font sizes/family cannot be recovered. Subtitle white bold sans with heavy black stroke/shadow; chapter handwritten brush/rounded serif hybrid guess.'}
thumb=np.array(Image.open(R/'reference.jpg').convert('RGB'));h,w=thumb.shape[:2];box=[145,425,1140,554];tm=maskmeasure(thumb,box);tm.update({'canvas':[w,h],'text_bbox_area_share':((tm['white_ink_bbox_xyxy'][2]-tm['white_ink_bbox_xyxy'][0])*(tm['white_ink_bbox_xyxy'][3]-tm['white_ink_bbox_xyxy'][1]))/(w*h),'white_ink_area_share':tm['white_ink_pixels']/(w*h),'text_height_share':tm['glyph_height_px']/h,'text_width_share':tm['glyph_width_px']/w,'manually_observed_subject_boxes_xyxy':{'shooter_left':[145,108,655,720],'victim_right':[590,4,1240,720],'muzzle_burst':[650,135,812,255]},'box_note':'Subject extents are manual approximate silhouette bounding boxes; text white mask exact within stated ROI.'});dump(R/'thumbnail_metrics.json',tm);dump(R/'typography_metrics.json',type_metrics)
# Small crops only: representative subtitle, opening dateline, chapter, map, profile and annotation styles.
cap=cv2.VideoCapture(str(R/'tmp/ref_proxy.mp4'));spec=[(8,[95,295,540,335],'Subtitle, white bold sans'),(2.8,[220,20,440,80],'Date/location'),(20,[250,70,600,145],'Profile label'),(60.8,[210,15,465,90],'Time marker'),(90,[0,0,640,360],'Numeric inventory'),(126,[130,120,550,225],'Incident name'),(131.5,[355,22,560,100],'Chapter 1'),(184,[255,10,570,300],'Profile list'),(151,[290,20,490,290],'Newspaper highlight'),(235,[210,0,530,330],'Map route/time/death labels'),(241,[220,20,420,90],'Role label'),(434,[180,30,490,310],'Police absence diagram')]
sh=Image.new('RGB',(1200,6*205),(25,25,25));dr=ImageDraw.Draw(sh)
for i,(t,box,label) in enumerate(spec):
 cap.set(cv2.CAP_PROP_POS_MSEC,t*1000);ok,a=cap.read();x0,y0,x1,y1=box;crop=Image.fromarray(cv2.cvtColor(a[y0:y1,x0:x1],cv2.COLOR_BGR2RGB));crop.thumbnail((580,170));x=i%2*600;y=i//2*205;sh.paste(crop,(x,y+28));dr.text((x+4,y+4),f'{t}s {label}',font=ImageFont.truetype(FONT,15),fill='white')
sh.save(R/'type_crops.jpg',quality=92);cap.release()
print(json.dumps({'type':type_metrics,'thumbnail':tm},ensure_ascii=False,indent=2))
