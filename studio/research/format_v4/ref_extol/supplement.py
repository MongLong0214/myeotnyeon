from analyze import *
for k in sys.argv[1:] or list(VIDEOS):
 d=R/k;m=meta(k);arr=np.load(d/'frame_curves.npz')['data'];old=json.loads((d/'candidates.json').read_text());frames=[c['frame'] for c in old];fps=m['fps'];med=__import__('scipy').signal.medfilt(arr[:,2],15);peaks,_=find_peaks(arr[:,2],height=2.5,distance=2,prominence=2)
 extra=[]
 for fr in peaks:
  if min(abs(fr-x) for x in frames)<4:continue
  if arr[fr,3]<.08 or arr[fr,2]<max(3,med[fr]*2.2):continue
  extra.append({'candidate':len(old)+len(extra)+1,'frame':int(fr),'time_s':float(fr/fps),'sources':['raw_diff_peak'],'diff':float(arr[fr,2]),'hist':float(arr[fr,3])})
 if k=='ours':
  src=json.load(open(W/'production/compositor_pilot/src/v4/n18-film.json'))
  for s in src['shots'][1:]:
   fr=round(s['from']/30*fps)
   if min(abs(fr-x) for x in frames+[e['frame'] for e in extra])<4 or fr>=len(arr):continue
   extra.append({'candidate':len(old)+len(extra)+1,'frame':fr,'time_s':fr/fps,'sources':['authored_event'],'diff':float(arr[fr,2]),'hist':float(arr[fr,3])})
 dump(d/'extra_candidates.json',extra);cap=cv2.VideoCapture(str(R/'tmp/ref_proxy.mp4' if k=='ref' else VIDEOS[k]))
 for start in range(0,len(extra),12):
  group=extra[start:start+12];sheet=Image.new('RGB',(1440,len(group)*116),(20,20,20));dr=ImageDraw.Draw(sheet)
  for j,c in enumerate(group):
   y=j*116;dr.text((5,y),f"C{c['candidate']:03} f{c['frame']} {c['time_s']:.3f}s {'+'.join(c['sources'])}",font=ImageFont.truetype(FONT,12),fill='white')
   for off in range(-3,3):sheet.paste(imageframe(cap,c['frame']+off,(200,90)),((off+3)*200,y+22))
   sheet.paste(imageframe(cap,c['frame']-round(fps*.5),(120,90)),(1200,y+22));sheet.paste(imageframe(cap,c['frame']+round(fps*.5),(120,90)),(1320,y+22))
  sheet.save(d/f'extra_{start//12+1:02}.jpg',quality=88)
 cap.release();print(k,'EXTRA',len(extra),flush=True)
