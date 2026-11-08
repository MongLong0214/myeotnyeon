from analyze import *
notes=json.load(open(R/'review_notes.json'))
for k in sys.argv[1:] or list(notes):
 d=R/k;note=notes[k];c=json.load(open(d/'candidates.json'))
 if (d/'extra_candidates.json').exists():c+=json.load(open(d/'extra_candidates.json'))
 if (d/'native_candidates.json').exists():c+=json.load(open(d/'native_candidates.json'))
 rows=[]
 for x in c:
  x={**x,'original_frame':x['frame'],'frame':x['frame']+int(note.get('frame_offsets',{}).get(str(x['candidate']),0)),'keep':x['candidate'] in note['keep'],'transition_type':note.get('types',{}).get(str(x['candidate']),'hard'),'confidence':note.get('confidence',{}).get(str(x['candidate']),.98 if len(x['sources'])>=2 else .85),'visually_reviewed':True}
  x['boundary_kind']=('composition-change' if k=='ref' or x['candidate'] in note.get('composition_candidates',[]) else 'same-view-reset') if x['keep'] else 'rejected'
  x['review_note']='accepted scene/framing boundary or discontinuous background/viewport reset' if x['keep'] else 'same shot motion / overlay / duplicate nearby candidate'
  rows.append(x)
 rows.sort(key=lambda x:x['frame']);dump(d/'reviewed.json',rows)
 csvwrite(d/'candidate_review.csv',[{**x,'sources':';'.join(x['sources'])} for x in rows])
 print(k,len([x for x in rows if x['keep']]),flush=True)
