import json,subprocess,concurrent.futures,os
from pathlib import Path
R=Path(__file__).resolve().parent;os.environ['TMPDIR']=str(R/'tmp')
def get(vid):
 d=R/vid
 cmd=['yt-dlp','--no-cache-dir','--skip-download','--ignore-no-formats-error','--write-comments','--extractor-args','youtube:comment_sort=top;max_comments=200,200,0,0','--add-header','Accept-Language:ko-KR,ko;q=0.9','--dump-json','https://www.youtube.com/watch?v='+vid]
 with (d/'comments_download.log').open('w') as f:r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=f,text=True)
 if r.stdout.strip():
  x=json.loads(r.stdout);cs=x.get('comments',[]);(d/'comments.json').write_text(json.dumps(cs,ensure_ascii=False,indent=2));(d/'comments_method.json').write_text(json.dumps({'sort':'top','max_total':200,'max_parents':200,'max_replies':0,'downloaded':len(cs),'note':'top-level comments only; truncated ranked convenience sample, not representative audience survey'}));print(vid,len(cs),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as e:list(e.map(get,json.loads((R/'inventory.json').read_text())['long']))
