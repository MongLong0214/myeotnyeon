"""Build sentence-level fresh narration and source binding from authored paragraphs."""
from pathlib import Path
import re,json,hashlib
ROOT=Path('.');P=ROOT/'production/astra_12min'
full={}
for name,ep in [('lf2','lf2_daejeon_bank'),('n18','v4/n18')]:
 e=ROOT/'episodes'/ep;out=e/'astra_12min';facts={}
 for file,prefix in [('facts.md',''),('facts_enrich.md','enrich:')]:
  if not (e/file).exists():continue
  for line in (e/file).read_text().splitlines():
   match=re.match(r'\|\s*([A-Z]\d+)\s*\|',line)
   if match:facts[prefix+match[1]]=dict(file=str(e/file),row=line,source_sha256=hashlib.sha256((e/file).read_bytes()).hexdigest())
 items=[];paragraphs=[]
 for line in (out/'script_source.txt').read_text().splitlines():
  if not line or line.startswith('#'):continue
  id,refs,shot,text=line.split('|',3);refs=refs.split(',');assert all(f in facts for f in refs),(id,refs)
  paragraphs.append(dict(id=id,facts=refs,direct_shot=shot,text=text,source_rows=[facts[f] for f in refs]))
  for i,sentence in enumerate(re.split(r'(?<=[.!?])\s+',text)):
   if sentence:items.append(dict(id=f'{id}_{i+1:02}',text=sentence,facts=refs,paragraph=id,direct_shot=shot,action='UNIMPLEMENTED_DIRECT_SHOT',before=shot.split('→')[0],after=shot.split('→')[-1]))
 (out/'source_mapping.json').write_text(json.dumps(dict(paragraphs=paragraphs,history='unavailable: episode/project are not Git repositories',target_seconds=720,policy='No new facts; source-specific attribution; all visuals are conceptual reconstructions'),ensure_ascii=False,indent=2))
 full[name+'_full']=dict(episode=ep,items=items,setting='DIRECT_SHOTS_NOT_YET_RENDERED',date='',target_seconds=720)
 print(name,len(paragraphs),'paragraphs',len(items),'sentences',sum(len(re.findall('[가-힣]',x['text'])) for x in items),'syllables')
(P/'full_narration.json').write_text(json.dumps(full,ensure_ascii=False,indent=2))
