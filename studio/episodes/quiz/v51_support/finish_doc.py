from pathlib import Path
import json,sys,copy
W=Path(__file__).resolve().parents[3]
def main(q):
 p=W/'episodes/quiz'/q/'v51';d=json.loads((p/'render.json').read_text());tim=json.loads((p/'timing.json').read_text());old=json.loads((W/'episodes/quiz'/q/'v5/render.json').read_text())
 # A four-frame visual lead preserves the shared reveal animation's valid swing range.
 # Audio remains back-to-back. Only scene boundaries and local sentence anchors move.
 for c in d['cues'][1:]:
  lead=min(i['start'] for i in tim['items'] if i['cue']==c['id'])
  newstart=lead-4;delta=c['from']-newstart;c['from']=newstart;c['a']={k:v+delta for k,v in c['a'].items()}
  original=next(x for x in old['cues'] if x['id']==c['id'])
  if 'headAt' in original['p']:c['p']['headAt']=original['p']['headAt']
 for a,b in zip(d['cues'],d['cues'][1:]):a['dur']=b['from']-a['from']
 d['cues'][-1]['dur']=d['durationInFrames']-d['cues'][-1]['from']
 for path in [p/'render.json',W/'production/compositor/public'/q/'v51/render.json']:path.write_text(json.dumps(d,ensure_ascii=False,indent=1))
 print(q,'scene leads fixed')
if __name__=='__main__':main(sys.argv[1])
