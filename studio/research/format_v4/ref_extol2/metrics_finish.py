from analyze import *
from collections import Counter,defaultdict
r=R
shots=list(csv.DictReader((r/'shots.csv').open()));cuts=list(csv.DictReader((r/'cuts.csv').open()));words=list(csv.DictReader((r/'ref/words.csv').open()));ons=list(csv.DictReader((r/'ref/audio_onsets.csv').open()));sideons=list(csv.DictReader((r/'reference_side_onsets.csv').open()))
for c in cuts:
 a=float(c['time_s']);nearest=min(words,key=lambda w:abs(float(w['end'])-a));lex=nearest['word'].strip();dist=abs(float(nearest['end'])-a);p0=[w for w in words if float(w['end'])<=a];n0=[w for w in words if float(w['start'])>=a];gap=float(n0[0]['start'])-float(p0[-1]['end']) if p0 and n0 else None;gram=bool(re.search(r'[,\.!?]$|(?:니다|였다|했다|된다|준다|있다|한다|봤다|없다|고|지만|으며|면서|거나|때문에|뒤|후|면서도|에서는|하면|면)$',lex));inside=any(float(w['start'])+.08<a<float(w['end'])-.08 for w in words);clause=(dist<=.2 and gram) or (gap is not None and gap>.2 and not inside);hits=[o for o in ons if abs(float(o['time_s'])-a)<=.1+1e-8];non=[o for o in hits if o['speech_overlap']=='False'];side=[o for o in sideons if abs(float(o['time_s'])-a)<=.1+1e-8]
 c.update({'clause_boundary_proxy':clause,'nearest_word_end_s':nearest['end'],'nearest_word':lex,'word_end_distance_s':dist,'mix_onset_within_100ms':bool(hits),'nonword_mix_onset_within_100ms':bool(non),'side_onset_within_100ms':bool(side)})
csvwrite(r/'cuts.csv',cuts)
# Add the same broad content labels that the first-reference job used.
def common(c):
 if c.startswith('3D_'):return '3D render'
 if 'chapter' in c:return 'text card'
 if 'map' in c:return 'map'
 if 'newspaper' in c:return 'document or record card'
 if 'news_video' in c:return 'news footage'
 if 'photo' in c:return 'archival photo'
 if 'infographic' in c:return 'document or record card'
 return 'other'
for s in shots:s['common_content_type']=common(s['content_type'])
csvwrite(r/'shots.csv',shots)
summary={'content_type_shot_counts':dict(Counter(s['common_content_type'] for s in shots)),'content_type_time_shares':{c:sum(float(s['duration_s']) for s in shots if s['common_content_type']==c)/521.8 for c in set(s['common_content_type'] for s in shots)},'clause_boundary_proxy_count':sum(c['clause_boundary_proxy'] for c in cuts),'clause_boundary_proxy_share':sum(c['clause_boundary_proxy'] for c in cuts)/len(cuts),'mix_onset_within_100ms_count':sum(c['mix_onset_within_100ms'] for c in cuts),'nonword_mix_onset_within_100ms_count':sum(c['nonword_mix_onset_within_100ms'] for c in cuts),'side_onset_within_100ms_count':sum(c['side_onset_within_100ms'] for c in cuts),'warning':'Onsets are not confirmed SFX; clauses are same ASR-rule estimate as ref1. Content labels identify visible format, not copyright status or asset origin.'}
gaps=list(csv.DictReader((r/'ref/pauses.csv').open()));g=[float(x['duration_s']) for x in gaps];summary['pause_distribution_gt200ms']={'count':len(g),'sum_s':sum(g),'median_s':float(np.median(g)),'p10_s':float(np.percentile(g,10)),'p90_s':float(np.percentile(g,90)),'max_s':max(g),'histogram':{'0.2_to_0.35':sum(.2<x<.35 for x in g),'0.35_to_0.5':sum(.35<=x<.5 for x in g),'0.5_to_1':sum(.5<=x<1 for x in g),'1_to_2':sum(1<=x<2 for x in g),'2_or_more':sum(x>=2 for x in g)}}
csvwrite(r/'pauses.csv',gaps);csvwrite(r/'narration_30s.csv',list(csv.DictReader((r/'ref/narration_30s.csv').open())))
# Narration-only endings exclude explicitly read teacher/article quotations for a fairer voice comparison.
sents=json.loads((r/'sentences.json').read_text());narr=[s for s in sents if not(148.6<=s['start_s']<157.5 or 489.7<=s['start_s']<508.81)];ending=Counter()
for s in narr:
 t=s['text'].rstrip('.,!?\"”');k='습니다' if t.endswith('니다') else '죠' if t.endswith(('죠','지요')) else '요' if t.endswith('요') else '다' if t.endswith('다') else 'other';ending[k]+=1
summary['narration_only_endings']={'sentences':len(narr),'counts':dict(ending),'shares':{k:v/len(narr) for k,v in ending.items()},'excluded':'Teacher quotation and final article quotation; indirect dialogue remains narrator.'}
dump(r/'additional_summary.json',summary)
# Source snapshots make later parallel edits distinguishable without copying any ref1 video/audio.
for folder,name in [('ref_extol','summary.json'),('ref_extol_story','devices.json'),('ref_extol_story','ours_fast_audio_summary.json'),('ref_extol_story','reference_audio_summary.json')]:
 p=r.parent/folder/name
 if p.exists():(r/f'{folder}_{name}').write_bytes(p.read_bytes())
print(json.dumps(summary,ensure_ascii=False,indent=2))
