#!/usr/bin/env python3
from pathlib import Path
import json, subprocess, hashlib, math
ROOT=Path(__file__).resolve().parent
mp4=ROOT/'n18_terra_full_preview.mp4'
data=json.loads((ROOT/'n18_full_preview_shots.json').read_text())
shots=data['shots']
review=ROOT/'review_extracts'; review.mkdir(exist_ok=True)
# 24 non-uniform actual-shot representatives, each with a middle and its true cut boundary.
idx=sorted(set(round(i*(len(shots)-1)/23) for i in range(24)))
items=[]
for j,i in enumerate(idx):
    s=shots[i]; mid=(s['start_s']+s['end_s'])/2
    for kind,t in [('boundary',s['start_s']+.10),('mid',mid)]:
        out=review/f'{j:02d}_{s["shot_id"]}_{kind}.png'
        subprocess.run(['ffmpeg','-y','-v','error','-ss',f'{t:.3f}','-i',str(mp4),'-frames:v','1',str(out)],check=True)
    items.append({'shot_index':i,'shot_id':s['shot_id'],'narration_id':s['narration_id'],'spoken_text':s['spoken_text'],'screen':s['screen'],'boundary_s':s['start_s'],'mid_s':round(mid,3),'boundary_frame':f'{j:02d}_{s["shot_id"]}_boundary.png','mid_frame':f'{j:02d}_{s["shot_id"]}_mid.png'})
# Build separate actual-frame contact sheets. ffmpeg's tile works against extracted images, not render inputs.
for kind in ('boundary','mid'):
    pattern=str(review/f'%02d_*_{kind}.png')
    # Numeric glob order is deterministic; FFmpeg accepts glob with filenames sorted lexically.
    subprocess.run(['ffmpeg','-y','-v','error','-pattern_type','glob','-i',str(review/f'*_{kind}.png'),'-vf','scale=213:120,tile=4x6:padding=3:margin=3','-frames:v','1',str(ROOT/f'n18_{kind}_sheet.png')],check=True)
ids=[s['shot_id'] for s in shots]
checks={'shot_count':len(shots),'unique_shot_ids':len(set(ids)),'duplicate_shot_ids':sorted({x for x in ids if ids.count(x)>1}),'missing_or_invalid_intervals':[s['shot_id'] for s in shots if s['end_s']<=s['start_s']],'screen_files_missing':sorted({s['screen'] for s in shots if not (ROOT/'full_renders'/(s['screen']+'.png')).exists()}),'reviewed_extract_count':len(items)*2,'review_items':items,'mp4_sha256':hashlib.sha256(mp4.read_bytes()).hexdigest()}
(ROOT/'n18_full_preview_review.json').write_text(json.dumps(checks,ensure_ascii=False,indent=2))
print(json.dumps(checks,ensure_ascii=False,indent=2))
