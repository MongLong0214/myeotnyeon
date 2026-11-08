from pathlib import Path
import json,re,hashlib,math
W=Path(__file__).resolve().parents[5]
E=W/'episodes/v4/n18'; O=E/'cartoon_v4'; S=Path(__file__).parent
O.mkdir(exist_ok=True); (S/'svg').mkdir(exist_ok=True)
d=json.loads((E/'shots_v3.json').read_text())
# Two editorial images for each approved narration line. No exercise, injury or patient reenactment.
views=[
('books','pack'),('hospital','hospital-door'),('court','balance'),('ground','ground-high'),('barracks','bunks'),('command','approval'),('procedure','empty-chair'),('thermometer','checklist'),('six','pack'),('ground','boots'),('command','track'),('track','books'),('clock','timeline'),('clock','hospital'),('investigation','medical-bag'),('investigation','court'),('court','link'),('defendants','court'),('defendant','dossier'),('balance','dossier'),('dossier','pack'),('court','balance'),('balance','court'),('books','letter'),
('letter','road'),('road','letter'),('barracks','bunks'),('phone','letter'),('phone','clock'),('hospital','route'),('hospital-night','clock'),('route','timeline'),('memorial','certificate'),('certificate','memorial'),('books','witness'),('witness','dossier'),('court','empty-chair'),('ground','shield'),('balance','dossier'),('defendant','court'),('approval','balance'),('court','dossier'),('prosecution','defendant'),('prosecution','defendants'),('shield','court'),('court','calendar'),('sentence-commander','defendant'),('sentence-deputy','defendants'),('balance','court'),('calendar','appeal'),('appeal','split'),('ground-high','split'),
('one-act','court'),('one-act','dossier'),('split','six'),('split','dossier'),('ground','split'),('many-act','appeal'),('six','balance'),('split','many-act'),('one-act','many-act'),('range','court'),('range','one-act'),('range','many-act'),('sentence-commander','balance'),('dossier','range'),('appeal','sentence-appeal'),('balance','calendar'),('appeal','shield'),('ground','appeal'),('shield','medical-bag'),('shield','six'),('court','shield'),('split','appeal'),('calendar','appeal'),('sentence-appeal','defendant'),('sentence-commander','sentence-appeal'),('sentence-deputy','defendants'),('defendants','balance'),('appeal','supreme'),('supreme','dossier'),('sentence-final','calendar'),('sentence-deputy','dossier'),('calendar','dossier'),('reform','ground'),('pack','reform'),('procedure','empty-chair'),('approval','reform'),('medical-bag','checklist'),('ground','reform'),('procedure','checklist'),('link','balance'),('split','shield'),('sentence-final','court'),('balance','host'),('host','court')]
assert len(views)==len(d['narration'])
setmap={}
for key in ['books','pack','six','boots','track','ground','ground-high','thermometer']:setmap[key]='training-ground'
for key in ['barracks','bunks','command','approval','procedure','checklist','empty-chair']:setmap[key]='barracks'
for key in ['hospital','hospital-door','hospital-night','medical-bag','route']:setmap[key]='hospital-exterior'
for key in ['investigation','dossier','phone','letter','road','clock','timeline']:setmap[key]='investigation'
for key in ['certificate','memorial']:setmap[key]='memorial'
for key in ['reform']:setmap[key]='briefing'
# Character identities are design roles, never likenesses or named historical participants.
characters={
 'narrator':{'role':'editorial narrator','identity':'fictional original design','face':'expressive','outfit':['#dca84b','#435765'],'voice':'existing narration only'},
 'recruits':{'role':'anonymous collective recruits','identity':'no singled-out victim','face':'back view or featureless neutral silhouette','outfit':['#879174','#596650'],'count':6,'actions':['stand','breathe'],'forbidden':['fall','kneel in distress','exercise','patient','individual label']},
 'commander':{'role':'중대장','face':'solid faceless silhouette','identity':'no age, sex, real likeness or rank badge','outfit':['#52634f','#263739']},
 'deputy':{'role':'부중대장','face':'solid faceless silhouette','identity':'no age, sex, real likeness or rank badge','outfit':['#52634f','#263739'],'note':'Source-backed role is 부중대장; do not relabel as 소대장.'},
 'medic':{'role':'generic medical-service symbol','identity':'fictional, no treatment reenactment','face':'simple cartoon face','outfit':['#f1eee1','#445c6a']},
 'judge':{'role':'generic court representative','identity':'fictional editorial figure','face':'simple expressive cartoon face','outfit':['#303344','#faf6e8'],'speaks':False},
 'investigator':{'role':'generic investigator','identity':'fictional editorial figure','face':'simple cartoon face','outfit':['#c0a785','#394c5b'],'speaks':False},
 'witness':{'role':'anonymous testimony symbol','identity':'back view only, no real person or victim likeness','face':'not visible','outfit':['#879174','#596650']}}
(S/'characters.json').write_text(json.dumps(characters,ensure_ascii=False,indent=2))
sets={k:{'palette':v,'representation':'symbolic 2D reconstruction; not the actual layout','parallax_layers':['sky-wall','architecture','props','foreground'],'medical_gore':False} for k,v in {'training-ground':['#e0d9b9','#9aa68a','#d1b887'],'barracks':['#c7d1bf','#6f8273','#bda982'],'hospital-exterior':['#b8d2cc','#e7e9da','#4e777c'],'investigation':['#52656b','#c5c7ae','#8b7657'],'courtroom':['#768782','#c5c4aa','#8b6649'],'memorial':['#c4d1bf','#e7e3cb','#788e7b'],'briefing':['#c8d4c3','#86a798','#e5debe']}.items()}
(S/'sets.json').write_text(json.dumps(sets,ensure_ascii=False,indent=2))
shots=[];types=['wide','insert','medium','close-up','over-the-shoulder','high-angle','low-angle','profile']
for i,n in enumerate(d['narration']):
 start=0 if i==0 else n['start_frame']; end=d['narration'][i+1]['start_frame'] if i+1<len(d['narration']) else round(d['credits_start_s']*30)
 num=max(2,math.ceil((end-start)/87))
 for j in range(num):
  a=round(start+(end-start)*j/num);b=round(start+(end-start)*(j+1)/num);view=views[i][j%2]
  sh={'id':f'C{len(shots)+1:03d}','start':a,'end':b,'start_s':a/30,'end_s':b/30,'view':view,'set':setmap.get(view,'courtroom'),'shot_type':types[(i*3+j)%len(types)],'narration_id':n['id'],'facts':n['fact_ids'],'source_context':n['source_context'],'motion':['eased-camera','parallax','secondary-animation'],'camera_direction':1 if len(shots)%2 else -1,'narrator_visible':view in ['host','range','balance','link'] or (i%7==2 and j==0),'safety':{'victim_identifiable':False,'collapse':False,'death_depicted':False,'gore':False,'invented_dialogue':False},'staging':'Symbolic cutaway; no exercises, treatment or event dialogue.'}
  shots.append(sh)
for j,view in enumerate(['books','court','shield','ground']):
 a=round(d['credits_start_s']*30)+j*60;b=min(d['duration_frames'],a+60)
 shots.append({'id':f'C{len(shots)+1:03d}','start':a,'end':b,'start_s':a/30,'end_s':b/30,'view':view,'set':setmap.get(view,'courtroom'),'shot_type':types[j*2],'narration_id':None,'facts':[],'source_context':'production endnote','motion':['eased-camera','parallax'],'camera_direction':1,'narrator_visible':False,'endnote':True,'safety':{'victim_identifiable':False,'collapse':False,'death_depicted':False,'gore':False,'invented_dialogue':False}})
shots[-1]['end']=d['duration_frames'];shots[-1]['end_s']=d['duration_s']
# First version keeps approved frame timings; audio adapter can substitute recovered exact-text final audio without generating speech.
sub=[]
for n in d['narration']:
 words=n['text'].split();parts=[];line=''
 for w in words:
  if len(line)+len(w)+1>25 and line:parts.append(line);line=w
  else:line=(line+' '+w).strip()
 if line:parts.append(line)
 lens=[len(x) for x in parts];total=sum(lens);p=n['start_frame']
 for z,l in zip(parts,lens):
  b=p+round((n['end_voice_frame']-n['start_frame'])*l/total);sub.append({'from':p,'to':min(b,n['end_voice_frame']),'text':z,'narration_id':n['id']});p=b
 sub[-1]['to']=n['end_voice_frame']
for i,s in enumerate(shots):assert s['start']==(0 if i==0 else shots[i-1]['end']);assert s['end']>s['start']
out={'version':'N18 cartoon v4','fps':30,'width':1920,'height':1080,'durationInFrames':d['duration_frames'],'duration_s':d['duration_s'],'shots':shots,'subtitles':sub,'narration':d['narration'],'chapters':d['chapters'],'judgement_silences':d['judgement_silences'],'source_documents':['script_v3.md','facts.md','facts_enrich.md'],'audio_status':'awaiting exact final voiced source; audio/na/index.json is older script','red_lines':{'all_characters_original':True,'victim_never_identified':True,'defendants_faceless':True,'no_collapse_death_gore':True,'no_invented_events_or_dialogue':True},'network':False,'uploads':False}
(O/'shots.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print('prepared',len(shots),'shots',len(sub),'captions',max((s['end']-s['start'])/30 for s in shots),'seconds max cut')
# Self-contained SVG construction parts, also used by the React scene via inline geometry.
parts={
'field-pack':'<path d="M-90-90Q0-125 90-90L105 82Q0 110-105 82Z" fill="#7a846b"/><path d="M-80-87L-60-38H63L83-87" fill="#a2ac86"/><path d="M-54-75V87M56-75V87" stroke="#485644" stroke-width="18"/><rect x="-19" y="-45" width="38" height="31" rx="5" fill="#d6b767"/>',
'books':'<path d="M-100-40L75-65L109 48L-66 73Z" fill="#b88e64"/><path d="M-84-32L66-53L89 35L-60 57Z" fill="#eee4c7"/><path d="M-100-40L-66 73" stroke="#6c6850" stroke-width="20"/><path d="M-65-15L60-34M-60 5L66-14M-53 25L72 6" stroke="#c4bba3" stroke-width="5"/>',
'medical-bag':'<rect x="-94" y="-65" width="188" height="143" rx="24" fill="#dbe6d7"/><path d="M-40-65V-95H40V-65" fill="none" stroke-width="14"/><path d="M-39 7H39M0-32V46" stroke="#528f83" stroke-width="23"/>',
'faceless-head':'<path d="M-67-45Q-73-100 0-104Q74-100 68-45L58 45Q0 83-58 45Z" fill="#263739"/><path d="M-76-61L-65-110Q0-132 65-110L77-61Z" fill="#46594d"/>',
'recruit-back-head':'<path d="M-65-38Q-69-95 0-103Q70-95 65-38L54 43Q0 70-54 43Z" fill="#788476"/><path d="M-75-56L-66-106Q0-123 66-106L76-56Z" fill="#8f9c7d"/><path d="M-61-59H62" stroke="#596d58" stroke-width="12"/>',
'court-scales':'<path d="M0-140V115M-130-90H130M-85 115H85" fill="none" stroke="#c9aa5b" stroke-width="17"/><path d="M-122-83L-177 30H-67ZM122-83L67 30H177Z" fill="#d6ba6c"/><circle cy="-143" r="20" fill="#d6ba6c"/>',
'phone':'<rect x="-64" y="-111" width="128" height="222" rx="21" fill="#34454c"/><rect x="-49" y="-86" width="98" height="161" rx="9" fill="#95bcb0"/><circle cy="93" r="7" fill="#e8dbba"/>',
'letter':'<path d="M-125-90H90L125-55V115H-125Z" fill="#eee5c8"/><path d="M90-90V-55H125" fill="#c3bda5"/><path d="M-92-42H58M-92-8H91M-92 26H91M-92 60H35" stroke="#a8ad96" stroke-width="10"/>',
'shield':'<path d="M0-135L115-90L101 28Q75 101 0 135Q-75 101-101 28L-115-90Z" fill="#4f827b"/><path d="M-54 1L-13 46L64-51" fill="none" stroke="#dfce8b" stroke-width="20"/>'}
for name,body in parts.items():
 (S/'svg'/f'{name}.svg').write_text(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-200 -160 400 320"><g stroke="#202b2e" stroke-width="7" stroke-linejoin="round">{body}</g></svg>')
(S/'parts.json').write_text(json.dumps(parts,ensure_ascii=False,indent=2))
