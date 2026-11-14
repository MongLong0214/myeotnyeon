from measure import *
from collections import Counter
import shutil
REF_TYPES={**{i:'news footage' for i in list(range(59,74))+[97]+list(range(99,103))+list(range(104,107))+list(range(108,112))+list(range(113,119))+list(range(122,125))+list(range(126,133))+list(range(140,146))+[153,154,161]},**{i:'map' for i in [11,98,103,107,112,125]},**{i:'document or record card' for i in [37,74,95,96,119,120,121,156,158,159,160]},**{i:'text card' for i in [36,47,58,137]},44:'timeline',157:'archival photo'}
REF_DESCRIPTIONS={1:'교도소 외곽에서 건물로 접근하는 3D 전경; 날짜 타이핑',2:'창살 너머 수감실; 잠든 수감자와 일어나는 인물',3:'신창원 3D 인물 및 실제 사진·인적사항 합성',4:'화장실 뒤쪽에서 환풍구를 향해 접근',5:'환풍구 쇠창살과 손 클로즈업',6:'쇠창살을 든 인물 정면',7:'환풍구 위에서 몸과 32×28cm 치수',8:'환풍구로 구부린 몸; 와이어프레임 변형',9:'낮은 시점의 다리·탈출 동작',10:'사동 외벽 옆 인물 와이드',11:'교도소 평면도와 이동 지점',12:'공사장 벽과 4.5m 치수',13:'손에 쥔 쇠창살 클로즈업',14:'땅 파는 인물에서 투명화·통과 동작으로 연속 이동',15:'공사장 바닥·잔해 와이드',16:'담벼락 앞 사다리·쇠파이프·밧줄 인물'}
def readcsv(p):return list(csv.DictReader(p.open()))
def floats(rows,fields):
 for r in rows:
  for f in fields:r[f]=float(r[f])
 return rows

def make(k):
 d=R/k;m=meta(k);fps=m['fps'];dur=m['duration'];flow=floats(readcsv(d/'flow.csv'),['start_s','end_s','duration_s','flow_mean_px_per_s_at_320w','scale_change_pct_per_s']);review=[r for r in json.load(open(d/'reviewed.json')) if r['keep']];review.sort(key=lambda r:r['frame'])
 # Exact boundary list includes half-open shot ranges. A flash or fade within a continuous shot stays an event.
 assert len({r['frame'] for r in review})==len(review)
 assert len(flow)==len(review)+1,(k,len(flow),len(review))
 words=floats(readcsv(d/'words.csv'),['start','end']);ons=floats(readcsv(d/'audio_onsets.csv'),['time_s']);aud=json.load(open(d/'audio_summary.json'));notes=json.load(open(R/'review_notes.json'))[k]
 src=None
 if k!='ref':src=json.load(open(W/'production/compositor_pilot/src/v4'/('n18-film-fast.json' if k=='ours_fast' else 'n18-film.json')))
 cuts=[];shots=[];boundaries=[]
 for i,r in enumerate(flow):
  a=r['start_s'];b=r['end_s'];mid=(a+b)/2;boundary=review[i-1] if i else None
  chapter=False;quote=False;card_key='';desc='';kind='';content='3D render'
  if k=='ref':
   content=REF_TYPES.get(i+1,'3D render');chapter=i+1 in [36,47,58,137];quote=i+1 in [158,159,160];desc=REF_DESCRIPTIONS.get(i+1,content);card_key=f'ref-S{i+1}'
   onscreen=[] if chapter else ['subtitle']
   if chapter:onscreen=['chapter card']
   if content in ['document or record card','timeline','map'] or i+1 in [3,7,12,20,78,149,150]:onscreen+=['label or callout']
   if i+1 in [1,38,76,134,151]:onscreen+=['date or time card']
   if quote:onscreen+=['quote']
  else:
   # Source art labels used only to name the independently observed render; source counts do not set cut locations.
   ss=[s for s in src['shots'] if s['from']/30<=mid<(s['from']+s['dur'])/30]
   s=ss[0] if ss else src['shots'][-1];kind=s['kind'];art=s.get('art','');chapter=kind=='chapter';quote=bool(s.get('quote')) or 'quote' in str(s.get('category',''))
   if chapter:content='text card';desc=s.get('chapterTitle','chapter')
   elif kind=='silence':content='other';desc='black hold'
   elif art=='dossier':content='document or record card';desc='기록 카드: '+' / '.join(s.get('lines',[]))
   elif art=='diagram':content='illustration';desc='피해자별 행위 도식: '+' / '.join(s.get('lines',[]))
   elif art=='spatial':content='map';desc='연병장 개념 평면도; 훈련병 여섯 표식'
   else:
    content='illustration';base='추상 법정 배경' if art=='verdict' else ('빈 연병장' if any(t in ' '.join(s.get('lines',[])) for t in ['적절한 조치','훈련병 사망']) else '연병장 전경, 역할 인물과 훈련병 여섯 표식');desc=base+': '+' / '.join(s.get('lines',[]))
   card_key='|'.join([art,';'.join(s.get('lines',[])),s.get('chapterTitle','') if chapter else ''])
   onscreen=['chapter card'] if chapter else ([] if kind=='silence' else ['subtitle','label or callout'])
   if s.get('date'):onscreen+=['date or time card']
   if quote:onscreen+=['quote']
  transition=boundary['transition_type'] if boundary else 'other';confidence=boundary['confidence'] if boundary else 1
  before=[w for w in words if w['end']<=a+.2];prev=before[-1] if before else None
  after=[w for w in words if w['start']>=a-.2];nxt=after[0] if after else None
  gap=None
  p0=[w for w in words if w['end']<=a];n0=[w for w in words if w['start']>=a]
  if p0 and n0:gap=n0[0]['start']-p0[-1]['end']
  nearest=min(words,key=lambda w:abs(w['end']-a));lex=nearest['word'].strip();dist=abs(nearest['end']-a)
  grammatical=bool(re.search(r'[,\.!?]$|(?:니다|였다|했다|된다|준다|있다|한다|봤다|없다|고|지만|으며|면서|거나|때문에|뒤|후|면서도|에서는|하면|면)$',lex))
  inside=any(w['start']+.08<a<w['end']-.08 for w in words)
  clause=(dist<=.2 and grammatical) or (gap is not None and gap>.2 and not inside)
  position='clause-boundary' if clause else 'mid-clause'
  if i==0:position='not-a-cut'
  if k=='ref' and 418.6<a<457.133333:position='unknown-archive-ASR';clause=False
  hits=[o for o in ons if abs(o['time_s']-a)<=.1+1e-8] if i else []
  nonvoice=[o for o in hits if o['speech_overlap']=='False']
  shot={**r,'content_type':content,'content_confidence':.9,'on_screen_text':';'.join(dict.fromkeys(onscreen)),'is_chapter_card':chapter,'is_quote':quote,'visual_description':desc,'card_key':card_key,'transition_type':transition,'transition_confidence':confidence,'boundary_kind':boundary.get('boundary_kind','') if boundary else 'start','audio_onset_within_0_1s':bool(hits),'nonword_onset_within_0_1s':bool(nonvoice),'sfx_or_music_hit':'unconfirmed' if hits else 'no-onset-detected','sound_hit_source_confidence':'unresolved mixed audio','cut_clause_position':position,'clause_estimate_confidence':.65 if k=='ref' else .7,'nearest_word_end_s':nearest['end'],'nearest_word':lex,'nearest_word_distance_s':dist,'clause_method':'Whisper word end +/-0.2s + Korean connective/ending OR >0.2s gap; automatic syntactic proxy','speech_context':' '.join(w['word'].strip() for w in words if w['end']>a-1.2 and w['start']<a+1.2)}
  shots.append(shot);cuts.append({'index':i+1,'start_s':a,'end_s':b,'duration_s':r['duration_s'],'transition_type':transition,'confidence':confidence})
  if boundary:
   span=notes.get('transition_spans',{}).get(str(boundary['candidate']),[boundary['frame'],boundary['frame']])
   boundaries.append({'index':i,'candidate':boundary['candidate'],'frame':boundary['frame'],'time_s':a,'transition_type':transition,'transition_start_frame':span[0],'transition_end_frame_exclusive':span[1],'duration_frames':span[1]-span[0],'boundary_kind':shot['boundary_kind'],'confidence':confidence,'sources':';'.join(boundary['sources'])})
 csvwrite(d/'cuts.csv',cuts);csvwrite(d/'shots.csv',shots);csvwrite(d/'boundaries.csv',boundaries)
 csvwrite(d/'cards.csv',[{key:s[key] for key in ['index','start_s','end_s','duration_s','content_type','is_chapter_card','visual_description','card_key']} for s in shots if s['content_type'] in ['text card','document or record card','timeline']])
 sections=[]
 if k=='ref':ranges=[('도입',0,2843/30),('01 무기수',2843/30,4425/30),('02 탈옥 준비',4425/30,6541/30),('03 도주 생활',6541/30,11990/30),('04 체포 작전',11990/30,dur)]
 else:
  cs=[s for s in src['shots'] if s['kind']=='chapter'];ranges=[(s.get('chapterTitle',''),math.ceil(s['from']/30*fps-1e-7)/fps,math.ceil(cs[j+1]['from']/30*fps-1e-7)/fps if j+1<len(cs) else dur) for j,s in enumerate(cs)]
 for name,a,b in [('first15',0,15),('first60',0,60)]+ranges:
  ds=[max(0,min(b,s['end_s'])-max(a,s['start_s'])) for s in shots if s['end_s']>a and s['start_s']<b];n=sum(a<q['time_s']<b for q in boundaries)
  sections.append({'section':name,'start_s':a,'end_s':b,'cut_count':n,'cuts_per_minute':n*60/(b-a),'visible_shot_count':len(ds),'clipped_duration_mean_s':float(np.mean(ds)),'clipped_duration_p10_s':float(np.percentile(ds,10)),'clipped_duration_median_s':float(np.median(ds)),'clipped_duration_p90_s':float(np.percentile(ds,90))})
 csvwrite(d/'sections.csv',sections)
 csvwrite(d/'cuts_per_30s.csv',[{'start_s':a,'end_s':min(dur,a+30),'cut_count':sum(a<=q['time_s']<min(dur,a+30) for q in boundaries),'cuts_per_minute':sum(a<=q['time_s']<min(dur,a+30) for q in boundaries)*60/(min(dur,a+30)-a)} for a in np.arange(0,dur,30)])
 first=[]
 for t in range(60):
  ss=[s for s in shots if s['end_s']>t and s['start_s']<t+1];ww=[w for w in words if w['end']>t and w['start']<t+1]
  first.append({'start_s':t,'end_s':t+1,'shot_indices':';'.join(str(s['index']) for s in ss),'shown':' → '.join(s['visual_description'] for s in ss),'said_asr':' '.join(w['word'].strip() for w in ww),'said_corrected':re.sub(r'(?<!\d)24년','2024년',' '.join(w['word'].strip() for w in ww)).replace('인재','인제').replace('무기징용','무기징역').replace('타록','탈옥'),'correction_note':'obvious ASR lexical errors corrected against existing local captions; raw retained','word_timestamp_note':'overlapping words; edge word may repeat between seconds','cut_times_s':';'.join(f"{q['time_s']:.3f}" for q in boundaries if t<=q['time_s']<t+1)})
 csvwrite(d/'first60_log.csv',first)
 ds=[s['duration_s'] for s in shots];moves=Counter(s['camera_move'] for s in shots);contents=Counter(s['content_type'] for s in shots);tt=Counter(s['transition_type'] for s in shots[1:]);known=[s for s in shots[1:] if s['cut_clause_position']!='unknown-archive-ASR'];chap=[s['duration_s'] for s in shots if s['is_chapter_card']]
 summary={'video':k,'duration_s':dur,'fps':fps,'frame_count':m['frames'],'sha256':m['sha256'],'shot_count':len(shots),'cut_count':len(boundaries),'mean_shot_s':float(np.mean(ds)),'median_shot_s':float(np.median(ds)),'shot_percentiles_s':dict(zip(['p5','p10','p25','p50','p75','p90','p95'],map(float,np.percentile(ds,[5,10,25,50,75,90,95])))),'min_shot_s':min(ds),'max_shot_s':max(ds),'cuts_per_minute':len(boundaries)*60/dur,'transition_counts':dict(tt),'transition_shares':{t:n/len(boundaries) for t,n in tt.items()},'camera_move_counts':dict(moves),'camera_move_shares':{t:n/len(shots) for t,n in moves.items()},'content_type_counts':dict(contents),'content_type_shares':{t:n/len(shots) for t,n in contents.items()},'content_time_shares':{t:sum(s['duration_s'] for s in shots if s['content_type']==t)/dur for t in contents},'flow_median_px_s_at_320w':float(np.median([float(s['flow_mean_px_per_s_at_320w']) for s in shots])),'flow_mean_px_s_at_320w':float(np.mean([float(s['flow_mean_px_per_s_at_320w']) for s in shots])),'abs_scale_change_pct_s_median':float(np.median([abs(float(s['scale_change_pct_per_s'])) for s in shots])),'composition_change_count':sum(q['boundary_kind']=='composition-change' for q in boundaries),'same_view_reset_count':sum(q['boundary_kind']=='same-view-reset' for q in boundaries),'clause_boundary_estimate_count':sum(s['cut_clause_position']=='clause-boundary' for s in known),'clause_boundary_estimate_known_denominator':len(known),'clause_boundary_estimate_share':sum(s['cut_clause_position']=='clause-boundary' for s in known)/len(known),'unknown_clause_cut_count':len(boundaries)-len(known),'onset_hit_proxy_count':sum(s['audio_onset_within_0_1s'] for s in shots[1:]),'onset_hit_proxy_share':sum(s['audio_onset_within_0_1s'] for s in shots[1:])/len(boundaries),'nonword_onset_lower_proxy_count':sum(s['nonword_onset_within_0_1s'] for s in shots[1:]),'nonword_onset_lower_proxy_share':sum(s['nonword_onset_within_0_1s'] for s in shots[1:])/len(boundaries),'confirmed_sfx_hit_share':None,'chapter_card_durations_s':chap,'chapter_card_median_s':float(np.median(chap)),'audio':aud,'sections':sections,'measurement_status':{'cuts':'native-frame visual review; pilots include discontinuous viewport/background resets','camera':'optical-flow and affine classification estimate; object animation and low texture confound','clauses':'ASR + rule estimate, not full human linguistic audit','sfx':'spectral-onset proxy only; cannot identify SFX/music isolated sources','music':'mixed/side RMS proxy; isolated music/narrator loudness not available'}}
 dump(d/'summary.json',summary);return summary
if __name__=='__main__':
 summaries={k:make(k) for k in VIDEOS};dump(R/'summary.json',summaries)
 for name in ['cuts.csv','shots.csv']:
  shutil.copyfile(R/'ref'/name,R/name)
  for k in ['ours','ours_fast']:shutil.copyfile(R/k/name,R/f'{k}_{name}')
 print(json.dumps({k:{q:s[q] for q in ['shot_count','mean_shot_s','median_shot_s','cuts_per_minute','composition_change_count','flow_median_px_s_at_320w','clause_boundary_estimate_share','onset_hit_proxy_share','nonword_onset_lower_proxy_share']} for k,s in summaries.items()},ensure_ascii=False,indent=2))
