import json,re,csv,collections
from pathlib import Path
R=Path(__file__).resolve().parent;c=json.loads((R/'comments.json').read_text())
# Manual primary thematic coding, includes each root and reply. Replies default to thread discussion.
praise=[9,15,17,19,20,40,42,44,45,47,49,52,53,61,76,78,80,81,82,89,91,93,95,98,103,110,132,135,136,144,147,150,159,165,166,173,177,181,185,190,196,202,204]
police=[13,18,21,60,71,72,73,74,85,94,96,97,99,102,107,123,124,130,143,149,156,167,170,175,179,184,186,188,191,193,198,200]
crime=[0,2,16,41,51,55,75,79,84,90,92,101,104,105,106,109,134,140,141,145,152,153,157,158,160,161,163,164,168,171,174,178,183,195,199,201,205,206,207,209,212,213]
requests=[146]
abuse=[169,172,180,197,210,211,214,215,216]
sets={'제작·몰입·목소리·채널 성장':set(praise),'경찰 대응·제도·총기정책':set(police),'사건 반응·배경·정확성·문화 연상':set(crime),'다음 소재 요청':set(requests),'지역·정치 혐오 또는 가해자 찬양':set(abuse)}
rows=[]
for i,x in enumerate(c):
 root=x.get('parent')=='root';tags=[k for k,ids in sets.items() if i in ids]
 label=tags[0] if tags else '짧은 반응·맥락외'
 if not root:
  parentroot=x.get('parent','').split('.')[0]
  origin=next((rr for rr in rows if rr['id']==parentroot),None)
  if origin:label=origin['primary_theme']
 rows.append({'index':i,'id':x['id'],'is_root':root,'likes':x.get('like_count',0),'primary_theme':label,'timestamp_mentions':';'.join(re.findall(r'(?<!\d)\d{1,2}:\d{2}(?!\d)',x['text'])),'text':x['text']})
counts=collections.Counter(r['primary_theme'] for r in rows);roots=[r for r in rows if r['is_root']];rc=collections.Counter(r['primary_theme'] for r in roots)
summary={'downloaded':len(c),'root_count':len(roots),'reply_count':len(c)-len(roots),'primary_counts_all':counts,'primary_counts_roots':rc,'root_uncoded':[r['index'] for r in roots if r['primary_theme']=='짧은 반응·맥락외'],'timestamp_comments':[r for r in rows if r['timestamp_mentions']],'method':'All 217 comments read. Root comments manually coded; replies inherit thread primary theme (tangents possible), separately counted. Theme counts mutually exclusive; subthemes overlap. Top-ranked YouTube sample, not random viewers or retention analytics. No attempt to fill to 300 by recency.'}
(R/'audience_summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2))
with (R/'comments_coded.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
print(json.dumps({k:v for k,v in summary.items() if k!='timestamp_comments'},ensure_ascii=False,indent=2))
