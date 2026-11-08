from measure import *
for k in VIDEOS:
 d=R/k;y,sr=sf.read(d/'analysis_audio_stereo.wav');mono=y.mean(1);side=(y[:,0]-y[:,1])/2;m=meta(k);words=floats=[]
 words=[{**w,'start':float(w['start']),'end':float(w['end'])} for w in csv.DictReader(open(d/'words.csv'))];mask=np.zeros(len(mono),bool)
 for w in words:mask[round(w['start']*sr):round(w['end']*sr)]=1
 def rms(a):return float(20*np.log10(max(1e-9,np.sqrt(np.mean(a*a))))) if len(a) else None
 rows=[]
 for a in np.arange(0,m['duration'],30):
  b=min(a+30,m['duration']);lo=int(a*sr);hi=min(len(mono),int(b*sr));z=mono[lo:hi];q=mask[lo:hi];sp=rms(z[q]);ns=rms(z[~q]);rows.append({'start_s':a,'end_s':b,'mixed_rms_dbfs':rms(z),'asr_word_mixed_rms_dbfs':sp,'asr_nonword_mixed_rms_dbfs':ns,'side_rms_dbfs':rms(side[lo:hi]),'nonword_minus_word_db':ns-sp if ns is not None and sp is not None else None,'music_presence_status':'unresolved-music-vs-ambience' if k=='ref' else 'production-source-music-false','music_vs_narrator_isolated_loudness_db':None})
 csvwrite(d/'audio_windows_30s.csv',rows)
# A terminal fade is a within-shot event, so it does not inflate cut counts.
events=[{'event':'terminal fade','start_frame':15969,'end_frame_exclusive':16038,'start_s':532.3,'end_s':534.6,'duration_frames':69,'transition_type':'fade-black','new_shot':False,'confidence':.8,'method':'observable luma reduction after final movement; onset threshold, encoding/ease obscures mathematical start'}, {'event':'vent camera traversal','start_frame':4734,'end_frame_exclusive':4770,'start_s':157.8,'end_s':159.0,'duration_frames':36,'transition_type':'zoom-through','new_shot':False,'confidence':.7,'method':'visual interval of continuous camera through vent; event extent approximate'}, {'event':'body wireframe traversal','start_frame':1540,'end_frame_exclusive':1681,'start_s':1540/30,'end_s':1681/30,'duration_frames':141,'transition_type':'other','new_shot':False,'confidence':.9,'method':'continuous object transformation and camera, not a dissolve/cut'}]
csvwrite(R/'ref/within_shot_events.csv',events)
# Curves: native measurements in gray, precisely time-resampled 0.5s mean in cyan; red ticks are reviewed boundaries.
fig=Image.new('RGB',(1800,950),'white');dr=ImageDraw.Draw(fig);font=ImageFont.truetype(FONT,18)
for j,k in enumerate(VIDEOS):
 d=R/k;m=meta(k);arr=np.load(d/'frame_curves.npz')['data'];cr=list(csv.DictReader(open(d/'frame_diff_0_5s.csv')));tt=np.array([float(x['time_s']) for x in cr]);sm=np.array([float(x['rolling_0_5s_mean_mad']) for x in cr]);left=80;top=50+j*300;width=1650;height=220;maxval=max(10,float(np.percentile(arr[:,2],99.5)))
 dr.text((80,top-30),f'{k} / native fps={m["fps"]} / luma MAD + rolling 0.5 s / scale 0..{maxval:.1f}',font=font,fill='black');dr.rectangle((left,top,left+width,top+height),outline='black')
 for lo in range(0,math.ceil(m['duration']),60):
  xx=left+width*lo/m['duration'];dr.line((xx,top,xx,top+height),fill='#dddddd');dr.text((xx,top+height+5),str(lo)+'s',fill='black')
 pts=[]
 for px in range(width):
  a=int(px/width*len(arr));b=max(a+1,int((px+1)/width*len(arr)));v=float(np.max(arr[a:b,2]));pts.append((left+px,top+height-height*min(1,v/maxval)))
 dr.line(pts,fill='#bbbbbb',width=1)
 pts=[(left+width*t/m['duration'],top+height-height*min(1,v/maxval)) for t,v in zip(tt[::10],sm[::10])];dr.line(pts,fill='#007e9b',width=2)
 for b in csv.DictReader(open(d/'boundaries.csv')):
  xx=left+width*float(b['time_s'])/m['duration'];dr.line((xx,top+height-8,xx,top+height),fill='#c83435',width=1)
fig.save(R/'frame_difference_curves.jpg',quality=92)
print('audio windows, within-shot events, curves done')
