import json,concurrent.futures
from pathlib import Path
from yt_dlp import YoutubeDL
from yt_dlp.extractor.youtube import YoutubeIE
R=Path(__file__).resolve().parent;inv=json.loads((R/'inventory.json').read_text())
def find_links(x,path=''):
 out=[]
 if isinstance(x,dict):
  if 'watchEndpoint' in x and 'reelCarousel' in path:out.append({'id':x['watchEndpoint'].get('videoId'),'source_path':path+'/watchEndpoint'})
  for k,v in x.items():out+=find_links(v,path+'/'+k)
 elif isinstance(x,list):
  for i,v in enumerate(x):out+=find_links(v,path+f'/{i}')
 return out
def get(vid):
 d=R/vid
 with YoutubeDL({'quiet':True,'cachedir':False,'http_headers':{'Accept-Language':'ko-KR,ko;q=0.9'}}) as ydl:
  ie=YoutubeIE(ydl);x=ie._call_api('reel/reel_item_watch',{'playerRequest':{'videoId':vid},'disablePlayerResponse':False},vid)
  links=find_links(x.get('overlay',{}));out={'video_id':vid,'links':links,'has_related_video_carousel_link':bool(links),'method':'yt-dlp YoutubeIE download of public reel_item_watch response; only watchEndpoint inside the metapanel reelCarousel; observed UI link, not topic inference','overlay_present':bool(x.get('overlay'))}
  (d/'related_video.json').write_text(json.dumps(out,ensure_ascii=False,indent=2));print(vid,[l['id'] for l in links],flush=True)
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as ex:list(ex.map(get,inv['short']))
