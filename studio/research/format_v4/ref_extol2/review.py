from analyze import *
d=R/'ref';m=meta('ref');fps=m['fps'];cs=json.loads((d/'candidates.json').read_text());cap=cv2.VideoCapture(str(R/'tmp/ref_proxy.mp4'))
# Fine transition strips: all individual frames covering the whole effect.
for cid in [1,36,56,70,71,80,95,179,208,231,238,239]:
 c=cs[cid-1];lo=c['frame']-12;hi=min(m['frames'],c['frame']+19)
 if cid==1:lo=115;hi=146
 if cid==36:lo=1935;hi=1980
 if cid==231:lo=15410;hi=15436
 sh=Image.new('RGB',(8*160,((hi-lo+7)//8)*112));dr=ImageDraw.Draw(sh)
 for j,fr in enumerate(range(lo,hi)):
  x=j%8*160;y=j//8*112;sh.paste(imageframe(cap,fr,(160,90)),(x,y+22));dr.text((x+3,y+2),f'f{fr} {fr/fps:.3f}',font=ImageFont.truetype(FONT,11),fill='white')
 sh.save(d/f'fine_{cid:03}.jpg',quality=93)
cap.release()
# A supplementary isolated-difference sweep recovers small embedded-footage cuts.
a=np.load(d/'frame_curves.npz')['data'];mad=a[:,2];base=__import__('scipy').ndimage.median_filter(mad,21);peaks,_=find_peaks(mad,height=1,prominence=1,distance=2)
extra=[]
for fr in peaks:
 if min(abs(fr-c['frame']) for c in cs)<=8:continue
 if mad[fr]<max(1.5,4*base[fr]):continue
 extra.append({'candidate':len(cs)+len(extra)+1,'frame':int(fr),'time_s':float(fr/fps),'sources':['isolated_mad_supplement'],'diff':float(mad[fr]),'hist':float(a[fr,3])})
dump(d/'extra_candidates.json',extra);cap=cv2.VideoCapture(str(R/'tmp/ref_proxy.mp4'))
for start in range(0,len(extra),12):
 group=extra[start:start+12];sh=Image.new('RGB',(1440,len(group)*116));dr=ImageDraw.Draw(sh)
 for j,c in enumerate(group):
  y=j*116;dr.text((5,y),f"C{c['candidate']} f{c['frame']} {c['time_s']:.3f}s supplemental",fill='white',font=ImageFont.truetype(FONT,12))
  for off in range(-3,3):sh.paste(imageframe(cap,c['frame']+off,(200,90)),((off+3)*200,y+22))
  sh.paste(imageframe(cap,c['frame']-15,(120,90)),(1200,y+22));sh.paste(imageframe(cap,c['frame']+15,(120,90)),(1320,y+22))
 sh.save(d/f'extra_{start//12+1:02}.jpg',quality=90)
print('extra',len(extra))
