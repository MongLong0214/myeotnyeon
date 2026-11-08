import os,json,subprocess,concurrent.futures,time,shutil,hashlib
from pathlib import Path
R=Path(__file__).resolve().parent; W=R.parents[2]
os.environ['TMPDIR']=str(R/'tmp');(R/'tmp').mkdir(exist_ok=True)
LONG=['H_GaGKQp17k','w_LJ_GQObic','C1eXfwC7uAw','OwQm8ZIZfiQ','nMg8D0I5GXc','wScaIvRspYc','yYe6svotmck','E_DrBRjGAQI','_qQK1LZpyJI']
SHORT=[e['id'] for e in json.loads((R/'shorts_listing.json').read_text())['entries']]
(R/'inventory.json').write_text(json.dumps({'long':LONG,'short':SHORT},indent=2))
def collect(vid):
 d=R/vid;d.mkdir(exist_ok=True);kind='long' if vid in LONG else 'short'
 # Copy existing reference media before the other jobs delete their own copies.
 old=R.parent/({'w_LJ_GQObic':'ref_extol','OwQm8ZIZfiQ':'ref_extol2'}.get(vid,'__none'))/'reference.mp4'
 if old.exists() and not (d/'media.mp4').exists():shutil.copy2(old,d/'media.mp4')
 cmd=['yt-dlp','--no-cache-dir','--no-playlist','--extractor-args','youtube:lang=ko;comment_sort=top;max_comments=200','--add-header','Accept-Language:ko-KR,ko;q=0.9','--write-info-json','--write-thumbnail','--convert-thumbnails','jpg','-o',str(d/'media.%(ext)s')]
 if kind=='long':cmd+=['--write-comments']
 if (d/'media.mp4').exists():cmd+=['--skip-download']
 else:cmd+=['-f','bv*[height<=1080][vcodec^=avc1]+ba/b[height<=1080]/bv*[height<=1080]+ba','--merge-output-format','mp4']
 cmd+=['https://www.youtube.com/watch?v='+vid]
 with (d/'download.log').open('w') as f:p=subprocess.run(cmd,stdout=f,stderr=f,env=os.environ)
 if (d/'media.info.json').exists():
  m=json.loads((d/'media.info.json').read_text());m['analysis_kind']=kind
  # Avoid retaining expiring media URLs and massive format metadata in the analysis summary.
  fields=['id','title','description','upload_date','timestamp','duration','view_count','like_count','comment_count','chapters','channel','channel_id','channel_follower_count','webpage_url','categories','tags','language','automatic_captions','subtitles','heatmap','availability','age_limit']
  clean={k:m.get(k) for k in fields};clean['analysis_kind']=kind;clean['collected_local']=time.strftime('%Y-%m-%dT%H:%M:%S%z')
  (d/'metadata.json').write_text(json.dumps(clean,ensure_ascii=False,indent=2))
  (d/'description.txt').write_text(m.get('description',''));(d/'comments.json').write_text(json.dumps(m.get('comments',[]),ensure_ascii=False,indent=2))
  if (d/'media.jpg').exists():shutil.copy2(d/'media.jpg',d/'thumbnail.jpg')
  print(vid,kind,p.returncode,m.get('title'),m.get('view_count'),len(m.get('comments',[])),flush=True)
 else:print(vid,'FAILED',p.returncode,flush=True)
 return vid
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as ex:list(ex.map(collect,LONG+SHORT))
