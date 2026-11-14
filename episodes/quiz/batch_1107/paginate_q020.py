"""H5 layout pagination: words and parent speech intervals remain unchanged."""
from pathlib import Path
import json,difflib,sys
from finish import norm,character_clock

W=Path(__file__).resolve().parents[3];B=Path(__file__).parent;p=W/'upload/pkg/q020_batch1107'
c=json.loads((p/'case.json').read_text())
parents=json.loads((B/'q020_before_1200/case.json').read_text())['subtitles']
ar=json.loads((p/'asr_master.json').read_text());actual,starts,ends=character_clock(ar,norm)
expected=norm(' '.join(s['text'] for s in parents));mapping={}
for b in difflib.SequenceMatcher(None,expected,actual,autojunk=False).get_matching_blocks():
 for n in range(b.size):mapping[b.a+n]=b.b+n
def lines(t):
 w=t.split(' ')
 if len(t)<=14:return [t]
 return min([[' '.join(w[:i]),' '.join(w[i:])] for i in range(1,len(w))],key=lambda x:max(map(len,x))*100+abs(len(x[0])-len(x[1])))
splits={
 '달리는 지하철 안에 휘발유를 붓고 불을 질렀습니다.':['달리는 지하철 안에 휘발유를 붓고','불을 질렀습니다.'],
 '불길이 번지자 승객들은 대피했고, 연기를 마신 사람도':['불길이 번지자 승객들은 대피했고,','연기를 마신 사람도'],
 '검찰은 승객 160 명에 대한 살인미수 혐의도 적용했습니다.':['검찰은 승객 160 명에 대한','살인미수 혐의도 적용했습니다.'],
}
offset=0;subs=[];evidence=[]
for parent in parents:
 text=parent['text'];chunks=splits.get(text,[text]);assert ' '.join(chunks)==text
 if any(max(map(len,lines(z)))>14 for z in chunks):raise ValueError((text,[lines(z) for z in chunks]))
 at=parent['start_s'];child_offset=offset
 for i,z in enumerate(chunks):
  last=i==len(chunks)-1
  if last:end=parent['end_s']
  else:
   nxt=child_offset+len(norm(z));k=next(k for k in range(nxt,min(nxt+8,len(expected))) if k in mapping)
   end=max(at+.08,min(parent['end_s']-.08,float(starts[mapping[k]])))
  subs.append(dict(start_s=at,end_s=end,text=z,reference=z,parent_start_s=parent['start_s'],parent_end_s=parent['end_s']))
  at=end;child_offset+=len(norm(z))
 offset+=len(norm(text))
 evidence.append(dict(original=parent,children=subs[-len(chunks):],lines=[lines(z) for z in chunks]))
assert ' '.join(s['text'] for s in subs)==' '.join(s['text'] for s in parents)
c['subtitles']=subs;(p/'case.json').write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n')
(p/'subtitle_pagination.json').write_text(json.dumps(dict(reason='Latest owner H5 is a fail condition. Only overlong layouts subdivided at the unchanged master ASR word clock. No word rewrite, no audio or reveal change. Parent start/end unchanged.',font_px=64,weight=800,outline_px=8,center_x=540,subtitle_area_y=[1190,1344],max_lines=2,max_characters_per_line=14,parents=evidence),ensure_ascii=False,indent=2)+'\n')
print('q020',len(parents),'parents ->',len(subs),'pages; maximum',max(max(map(len,lines(s['text']))) for s in subs),'characters per line')
