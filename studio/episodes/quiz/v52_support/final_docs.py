from pathlib import Path
import json,math
W=Path(__file__).resolve().parents[3];S=Path(__file__).parent
report={}
for q in ['q015','q012','q016','q017']:
 p=W/'episodes/quiz'/q/'v52';d=json.loads((p/'render.json').read_text());t=json.loads((p/'timing.json').read_text());rv=next(c for c in d['cues'] if c['scene']=='reveal');reveal=rv['from']+rv['a']['s1']+2;oldn=d['durationInFrames'];n=oldn
 if reveal/n<.75:n=math.floor(reveal/.75)
 assert n>=660 and t['items'][-1]['end']<=n,(q,n,t['items'][-1]['end'])
 d['durationInFrames']=n;d['cues'][-1]['dur']=n-d['cues'][-1]['from'];assert reveal/n>=.75
 for target in [p/'render_final.json',W/'production/compositor/public'/q/'v52/render_final.json']:
  with target.open('x') as f:json.dump(d,f,ensure_ascii=False,indent=1)
 report[q]=dict(original_planned_frames=oldn,final_frames=n,trailing_silence_removed_frames=oldn-n,all_speech_retained=True,reveal_ratio=reveal/n)
 print(q,report[q],flush=True)
with (S/'final_timing.json').open('x') as f:json.dump(report,f,indent=1)
