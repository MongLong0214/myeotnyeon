from analyze import *
d=R/'ref';m=meta('ref');fps=m['fps'];cs=json.loads((d/'candidates.json').read_text())+json.loads((d/'extra_candidates.json').read_text())
keep=[2,4,6,7,8,10,11,13,14,17,18,20,22,24,26,28,31,35,37,41,42,43,44,45,46,49,51,52,55,56,58,62,65,68,72,75,80,84,88,89,92,94,95,98,101,103,106,108,109,119,121,126,131,133,135,137,139,140,141,142,143,146,149,154,156,158,161,162,164,166,167,169,171,174,175,177,178,179,182,190,193,195,197,200,201,204,208,210,215,222,230,232,233,235,236]
spans={56:(3877,3892,3884),80:(5699,5703,5701),95:(6915,6930,6922),179:(12479,12494,12483),208:(14178,14198,14186)}
review=[]
for c in cs:
 yes=c['candidate'] in keep;typ='hardcut';fr=c['frame'];span=(fr,fr)
 if c['candidate'] in spans:
  a,b,fr=spans[c['candidate']];span=(a,b);typ='cross-dissolve' if c['candidate']==80 else 'glitch'
 review.append({**c,'frame':fr,'original_candidate_frame':c['frame'],'keep':yes,'transition':typ if yes else 'rejected','transition_start_frame':span[0] if yes else None,'transition_end_frame_exclusive':span[1] if yes else None,'review':'all six adjacent frames visually checked; continuous camera, labels, subtitles, particles and mesh changes excluded' if not yes else 'visual check; fine strip for gradual transition; hardcut=0 blended frames; 1-frame discontinuity'})
manual={'candidate':300,'frame':15411,'time_s':15411/fps,'sources':['manual_embedded_footage_review'],'keep':True,'transition':'embedded-footage-hardcut','transition_start_frame':15411,'transition_end_frame_exclusive':15411,'review':'f15410 room / f15411 interview; fine_231.jpg'}
review.append(manual);review.sort(key=lambda x:x['frame']);dump(d/'reviewed.json',review)
cuts=[]
for r in sorted([x for x in review if x['keep']],key=lambda x:x['frame']):
 cuts.append({'cut_id':len(cuts)+1,'candidate_id':r['candidate'],'frame':r['frame'],'time_s':r['frame']/fps,'transition_type':r['transition'],'transition_start_frame':r['transition_start_frame'],'transition_end_frame_exclusive':r['transition_end_frame_exclusive'],'transition_duration_frames':r['transition_end_frame_exclusive']-r['transition_start_frame'],'transition_duration_s':(r['transition_end_frame_exclusive']-r['transition_start_frame'])/fps,'sources':'+'.join(r['sources']),'review':'six-frame visual review; gradual-effect bounds ±2 frames; hardcut onset exact at proxy fps'})
csvwrite(R/'cuts.csv',cuts)
starts=[0]+[x['frame'] for x in cuts];ends=starts[1:]+[m['frames']]
def content(t):
 if 129.46<=t<132.133 or 230.73<=t<233.433 or 416.1<=t<418.8 or 472.86<=t<475.3:return 'chapter_card_archival_newspaper'
 if 132.133<=t<144.833 or 157.733<=t<166.267 or 180.4<=t<185.433:return 'archival_photo_profile_composite'
 if 144.833<=t<157.733 or 166.267<=t<180.4 or 287.933<=t<290.267 or 487.367<=t<513.367:return 'archival_newspaper_highlight'
 if 185.433<=t<199.667 or 233.433<=t<239.033 or 254.6<=t<256 or 267.633<=t<273.867 or 293.1<=t<296.567 or 312.867<=t<317.2 or 418.8<=t<423.8:return 'archival_map_animated_route'
 if 239.033<=t<248.3:return 'archival_news_video_plus_photo'
 if 403.833<=t<407.533:return 'archival_photo_location'
 if 513.367<=t:return 'archival_news_video_in_frame'
 if 427.967<=t<437.3:return 'typography_infographic'
 if 88.967<=t<94.5 or 407.533<=t<416.1:return '3D_inventory_infographic'
 if 310.767<=t<312.867:return 'abstract_red_effect'
 if 17<=t<27.1:return '3D_stylized_plus_archival_portrait'
 return '3D_stylized_reenactment'
chapters=[('cold_open',0,3884/fps),('01_우범곤_순경',3884/fps,6922/fps),('02_사건_당일',6922/fps,12483/fps),('03_경찰_출동',12483/fps,14186/fps),('04_범행_목적',14186/fps,m['duration'])]
shots=[]
for i,(a,b) in enumerate(zip(starts,ends)):
 t=(a+b)/2/fps;shots.append({'shot_id':i+1,'start_frame':a,'end_frame_exclusive':b,'start_s':a/fps,'end_s':b/fps,'duration_s':(b-a)/fps,'chapter':next(c[0] for c in chapters if c[1]<=t<c[2]),'content_type':content(t),'type_confidence':'visual family; production engine/assets provenance not established'})
csvwrite(R/'shots.csv',shots);dump(R/'chapters.json',[{'name':n,'start_s':a,'end_s':b,'duration_s':b-a} for n,a,b in chapters])
sections=[]
for name,a,b in [('first15',0,15),('first60',0,60)]+chapters:
 n=sum(a<c['time_s']<b for c in cuts);lens=[s['duration_s'] for s in shots if a<=s['start_s']<b]
 sections.append({'section':name,'start_s':a,'end_s':b,'cut_count':n,'cuts_per_minute':n*60/(b-a),'shot_start_count':len(lens),'median_full_shot_duration_s':float(np.median(lens)) if lens else None})
csvwrite(R/'cuts_by_section.csv',sections)
summary={'duration_s':m['duration'],'fps':fps,'frames':m['frames'],'cut_count':len(cuts),'shot_count':len(shots),'cut_per_minute':len(cuts)*60/m['duration'],'shot_duration_mean_s':float(np.mean([s['duration_s'] for s in shots])),'shot_duration_median_s':float(np.median([s['duration_s'] for s in shots])),'shot_duration_quantiles_s':dict(zip(['p10','p25','p75','p90','max'],[float(x) for x in np.percentile([s['duration_s'] for s in shots],[10,25,75,90,100])])),'shots_under_1s':sum(s['duration_s']<1 for s in shots),'shots_over_8s':sum(s['duration_s']>8 for s in shots),'transition_counts':{x:sum(c['transition_type']==x for c in cuts) for x in set(c['transition_type'] for c in cuts)},'sections':sections,'terminal_effect':{'type':'glitch_to_black','start_frame':15637,'end_frame_exclusive':15654,'duration_frames':17,'counted_as_content_cut':False},'method':'Same detector thresholds and dimensions as ref1. 239 union candidates + 60 isolated MAD candidates + 1 manual embedded-video cut, all reviewed. Excludes subtitles/type reveals, particles, continuous pans/pushes and mesh animation. Gradual anchors=first target-dominant frame. Ending glitch retained separately.'}
dump(R/'cuts_summary.json',summary)
# 6-frame validation for the manually found embedded boundary, and shot midpoint sheets.
cap=cv2.VideoCapture(str(R/'tmp/ref_proxy.mp4'));sh=Image.new('RGB',(1200,115));dr=ImageDraw.Draw(sh);dr.text((4,2),'C300 f15411 513.700 embedded footage cut',font=ImageFont.truetype(FONT,13),fill='white')
for off in range(-3,3):sh.paste(imageframe(cap,15411+off,(200,90)),((off+3)*200,25))
sh.save(d/'manual_300.jpg',quality=92)
for start in range(0,len(shots),25):
 group=shots[start:start+25];sh=Image.new('RGB',(1600,((len(group)+4)//5)*202));dr=ImageDraw.Draw(sh)
 for j,s in enumerate(group):
  x=j%5*320;y=j//5*202;sh.paste(imageframe(cap,(s['start_frame']+s['end_frame_exclusive'])//2,(320,180)),(x,y+22));dr.text((x+3,y+2),f"S{s['shot_id']:03} {s['start_s']:.2f}-{s['end_s']:.2f}",font=ImageFont.truetype(FONT,13),fill='white')
 sh.save(d/f'shots_{start//25+1:02}.jpg',quality=91)
cap.release();print(json.dumps(summary,ensure_ascii=False,indent=2))
