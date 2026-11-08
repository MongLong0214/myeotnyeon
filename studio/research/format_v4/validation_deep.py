"""Fetch public text, thumbnails, and sb storyboard sprites only; never AV or cookies."""
import concurrent.futures as cf
import datetime as dt
import json
import pathlib
import subprocess
import urllib.request
from PIL import Image, ImageDraw, ImageFont

R = pathlib.Path(__file__).resolve().parent
D = R / 'validation_deep'
Y = '$HOME/.local/bin/yt-dlp'
BASE = [Y, '--ignore-config', '--no-cookies', '--socket-timeout', '25', '--retries', '1', '--extractor-retries', '1', '--ignore-no-formats-error', '--extractor-args', 'youtube:player_client=web']
KST = dt.timezone(dt.timedelta(hours=9))
def now(): return dt.datetime.now(KST).isoformat(timespec='seconds')
def run(vid, kind, args):
    out = D / vid / (kind + '.txt')
    status = D / vid / (kind + '.status.json')
    if out.exists() and status.exists(): return out.read_text(), json.loads(status.read_text())
    t = now()
    try:
        p = subprocess.run(BASE + args + [f'https://www.youtube.com/watch?v={vid}'], capture_output=True, text=True, timeout=150)
        txt, err, code = p.stdout, p.stderr, p.returncode
    except subprocess.TimeoutExpired:
        txt, err, code = '', 'timeout', -1
    out.write_text(txt)
    s = dict(started_at_kst=t, finished_at_kst=now(), command=BASE+args+[f'https://www.youtube.com/watch?v={vid}'], exit_code=code, error=err[-3500:])
    status.write_text(json.dumps(s, ensure_ascii=False, indent=1))
    return txt, s
def get(url, path):
    if path.exists() and path.stat().st_size: return True
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=40) as f:
            path.write_bytes(f.read())
        return True
    except Exception: return False
def one(vid):
    folder = D / vid; folder.mkdir(parents=True, exist_ok=True)
    txt, s = run(vid, 'metadata', ['--skip-download','--dump-json'])
    try: m = json.loads(txt)
    except Exception: print(vid,'metadata failed',flush=True);return
    run(vid, 'formats', ['-F'])
    run(vid, 'auto_subtitles', ['--skip-download','--write-auto-subs','--sub-langs','ko','--sub-format','vtt','-o',str(folder/'%(id)s.%(ext)s')])
    if 'ko-orig' in m.get('automatic_captions', {}):
        run(vid, 'original_auto_subtitles', ['--skip-download','--write-auto-subs','--sub-langs','ko-orig','--sub-format','vtt','-o',str(folder/'%(id)s.%(ext)s')])
    sb = [f for f in m.get('formats',[]) if f.get('format_id','').startswith('sb')]
    f = next((f for f in sb if f['format_id']=='sb0'), sb[-1] if sb else None)
    manifest = dict(id=vid, observed_at_kst=now(), metadata_status=s, storyboard_format=f.get('format_id') if f else None, sprites=[], thumbnails=[])
    if f:
        frs=f.get('fragments',[]);chosen=sorted(set([0,len(frs)//2,len(frs)-1]));start=0
        for i,fr in enumerate(frs):
            dur=fr.get('duration') or 0
            if i in chosen:
                p=folder/f"{f['format_id']}_{i}.jpg"
                if get(fr['url'],p):manifest['sprites'].append(dict(path=str(p.relative_to(R)),index=i,start_s=start,duration_s=dur,rows=f.get('rows'),columns=f.get('columns'),tile_width=f.get('width'),tile_height=f.get('height')))
            start+=dur
    thumbs=[t for t in m.get('thumbnails',[]) if t.get('width') and t.get('url')]
    if thumbs:
        t=max(thumbs,key=lambda t:t['width']*t.get('height',0));p=folder/'thumbnail.jpg'
        if get(t['url'],p):manifest['thumbnails'].append(dict(path=str(p.relative_to(R)),url=t['url']))
    (folder/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=1))
    print(vid, m.get('channel'), 'subs',len(list(folder.glob('*.vtt'))),'sprites',len(manifest['sprites']),flush=True)
def boards():
    for c in json.load(open(R/'validation_raw/deep_selected.json')):
        ids=list(dict.fromkeys([r['id'] for r in c['top']+c['recent']]))
        out=Image.new('RGB',(1500,220*len(ids)),(25,25,25));dr=ImageDraw.Draw(out)
        for row,vid in enumerate(ids):
            p=D/vid/'manifest.json'
            if not p.exists():continue
            man=json.load(open(p));m=json.load(open(D/vid/'metadata.txt'))
            dr.text((5,row*220+3),f"{vid} {m.get('duration')}s {m.get('upload_date')}",fill='white')
            if man['thumbnails']:
                im=Image.open(R/man['thumbnails'][0]['path']).convert('RGB');im.thumbnail((288,180));out.paste(im,(0,row*220+30))
            cells=[]
            for sp in man['sprites']:
                im=Image.open(R/sp['path']);w,h=sp['tile_width'],sp['tile_height'];n=sp['rows']*sp['columns']
                for k in [0,n//2]:
                    rr,cc=divmod(k,sp['columns']);t=sp['start_s']+k*sp['duration_s']/n
                    if t <= (m.get('duration') or 0): cells.append((t,im.crop((cc*w,rr*h,(cc+1)*w,(rr+1)*h))))
            for col,(t,im) in enumerate([cells[i] for i in sorted(set([0,1,len(cells)//2,len(cells)-1])) if 0 <= i < len(cells)],1):
                im.thumbnail((288,180));out.paste(im,(col*300,row*220+30));dr.text((col*300,row*220+15),f'{t:.1f}s',fill='yellow')
        out.save(D/(c['channel_id']+'_board.jpg'))
if __name__=='__main__':
    D.mkdir(exist_ok=True)
    ids=list(dict.fromkeys(r['id'] for c in json.load(open(R/'validation_raw/deep_selected.json')) for r in c['top']+c['recent']))
    with cf.ThreadPoolExecutor(5) as ex:list(ex.map(one,ids))
    boards()
