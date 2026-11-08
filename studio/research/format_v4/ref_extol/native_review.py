from analyze import *
notes=json.load(open(R/'review_notes.json'));ref=notes['ref'];ref['frame_offsets'].update({'73':3,'105':-2,'151':2,'334':1})
ref['transition_spans']={'73':[2843,2850],'105':[4425,4436],'151':[6541,6553],'334':[11990,12003]}
composition={'ours':[1,2,4,8,10,11,12,14,16,17,31,39,40,42,45,47,59,61,69,70,72,91,93,95,97,98,99,110,112,114], 'ours_fast':[1,3,7,13,14,16,20,46,56,58,64,65,86,90,103,106,139,141,142,144,168,172,173]}
for k in ['ours','ours_fast']:
 d=R/k;cs=json.load(open(d/'boundary_jumps.json'));note={'reviewed_pages':list(range(1,11 if k=='ours' else 16)),'keep':[],'frame_offsets':{},'types':{},'composition_candidates':composition[k],'notes':'All six-frame strips visually inspected. Abrupt lighting/viewport resets retained as render discontinuities, separate from composition changes. Crop MAD corroborates step location.'}
 accepted=[]
 for c in cs:
  pp=max(c['pairs'],key=lambda x:x['mad'])
  if pp['mad']<3:continue
  note['keep'].append(c['candidate']);note['frame_offsets'][str(c['candidate'])]=pp['off'];accepted.append(c['frame']+pp['off'])
  if c['candidate'] not in composition[k] and pp['scale']>2 and pp['inliers']>.3:note['types'][str(c['candidate'])]='push-in-cut'
 notes[k]=note
 # Native-rate supplementary sweep, no 4-frame hold or 3-frame grouping on 5-fps sources.
 cap=cv2.VideoCapture(str(R/'tmp'/f'{k}_proxy.mp4'));last=None;vals=[];idx=0
 while True:
  ok,im=cap.read()
  if not ok:break
  a=cv2.cvtColor(cv2.resize(im,(320,180)),cv2.COLOR_BGR2GRAY)[40:145]
  vals.append(float(np.abs(a.astype(float)-last).mean()) if last is not None else 0);last=a.astype(float);idx+=1
 cap.release();vals=np.array(vals);peaks,_=find_peaks(vals,height=3,prominence=2,distance=1);extra=[];fps=meta(k)['fps']
 old=json.load(open(d/'candidates.json'));old+=json.load(open(d/'extra_candidates.json')) if (d/'extra_candidates.json').exists() else []
 for fr in peaks:
  if fr in accepted:continue
  if vals[fr]<max(3,float(np.median(vals[max(0,fr-3):fr+4]))*2):continue
  extra.append({'candidate':max([c['candidate'] for c in old]+[0])+len(extra)+1,'frame':int(fr),'time_s':float(fr/fps),'sources':['native_frame_sweep'],'diff':float(vals[fr]),'hist':None})
 dump(d/'native_candidates.json',extra);np.save(d/'native_crop_mad.npy',vals)
 cap=cv2.VideoCapture(str(R/'tmp'/f'{k}_proxy.mp4'))
 for start in range(0,len(extra),12):
  g=extra[start:start+12];sheet=Image.new('RGB',(1440,len(g)*116));dr=ImageDraw.Draw(sheet)
  for j,c in enumerate(g):
   y=j*116;dr.text((5,y),f"C{c['candidate']:03} f{c['frame']} {c['time_s']:.3f}s native sweep",fill='white',font=ImageFont.truetype(FONT,12))
   for off in range(-3,3):sheet.paste(imageframe(cap,c['frame']+off,(200,90)),((off+3)*200,y+22))
   sheet.paste(imageframe(cap,c['frame']-3,(120,90)),(1200,y+22));sheet.paste(imageframe(cap,c['frame']+3,(120,90)),(1320,y+22))
  sheet.save(d/f'native_{start//12+1:02}.jpg',quality=90)
 cap.release();print(k,'accepted',len(accepted),'extra native',len(extra),flush=True)
dump(R/'review_notes.json',notes)
