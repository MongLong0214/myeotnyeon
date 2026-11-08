import os,json,subprocess,concurrent.futures
from pathlib import Path
R=Path(__file__).resolve().parent;os.environ['TMPDIR']=str(R/'tmp')
inv=json.loads((R/'inventory.json').read_text())
def get(vid):
 d=R/vid
 cmd=['yt-dlp','--no-cache-dir','--skip-download','--ignore-no-formats-error','--no-playlist','--add-header','Accept-Language:ko-KR,ko;q=0.9','--dump-json','https://www.youtube.com/watch?v='+vid]
 with (d/'stats.log').open('w') as log:r=subprocess.run(cmd,stdout=subprocess.PIPE,stderr=log,text=True)
 if r.stdout.strip():
  (d/'stats_raw.json').write_text(r.stdout)
  x=json.loads(r.stdout);p=d/'metadata.json';m=json.loads(p.read_text()) if p.exists() else x
  for k in ['view_count','like_count','comment_count','upload_date','timestamp','age_limit','duration']:
   if x.get(k) is not None:m[k]=x[k]
  if not p.exists():m['analysis_kind']='long';m['metadata_language_status']='native/header requested; verify title';(d/'description.txt').write_text(x.get('description',''))
  m['counts_method']='yt-dlp separate metadata extraction without write-comments; avoids capped extracted count';p.write_text(json.dumps(m,ensure_ascii=False,indent=2))
  print(vid,x.get('view_count'),x.get('like_count'),x.get('comment_count'),flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:list(ex.map(get,inv['long']+inv['short']))
