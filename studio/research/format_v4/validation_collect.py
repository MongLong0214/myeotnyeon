"""Public YouTube metadata only. Never downloads video/audio, never uses cookies."""
import concurrent.futures as cf
import datetime as dt
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent
RAW = ROOT / 'validation_raw'
YTDLP = '$HOME/.local/bin/yt-dlp'
BASE = [YTDLP, '--ignore-config', '--no-cookies', '--no-warnings', '--socket-timeout', '25', '--retries', '1', '--extractor-retries', '1']
KST = dt.timezone(dt.timedelta(hours=9))
QUERIES = ['사건 다큐', '실화 사건', '범죄 다큐 애니', '판결', '법정', '형량', '결말', '최후', '참교육', '블랙박스', '사연 애니', '썰 애니', '법률 상식', '사건 재구성 애니메이션', '실화 애니메이션 범죄', '결말 쇼츠', '최후 shorts', '블랙박스 사고 판결', '법률 상식 쇼츠', '범죄 사건 이야기']

def now():
    return dt.datetime.now(KST).isoformat(timespec='seconds')

def run_json(key, args, timeout=160):
    dest = RAW / (key + '.jsonl')
    status = RAW / (key + '.status.json')
    if dest.exists() and status.exists():
        return [json.loads(l) for l in dest.read_text().splitlines() if l.strip()], json.loads(status.read_text())
    started = now()
    cmd = BASE + args
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        output, err, code = p.stdout, p.stderr, p.returncode
    except subprocess.TimeoutExpired as e:
        output, err, code = e.stdout or '', 'timeout', -1
        if isinstance(output, bytes): output = output.decode(errors='replace')
    rows = []
    for line in output.splitlines():
        try: rows.append(json.loads(line))
        except json.JSONDecodeError: pass
    dest.write_text(''.join(json.dumps(r, ensure_ascii=False) + '\n' for r in rows))
    s = dict(started_at_kst=started, finished_at_kst=now(), command=cmd, exit_code=code, error=err[-4000:], rows=len(rows))
    status.write_text(json.dumps(s, ensure_ascii=False, indent=2))
    print(key, len(rows), code, err[-100:] if code else '', flush=True)
    return rows, s

def searches():
    def one(iq):
        i, q = iq
        rows, s = run_json(f'search_{i:02}', ['--flat-playlist', '--dump-json', f'ytsearch50:{q}'])
        return dict(query=q, rows=rows, status=s)
    with cf.ThreadPoolExecutor(5) as ex:
        data = list(ex.map(one, enumerate(QUERIES)))
    (RAW / 'searches.json').write_text(json.dumps(data, ensure_ascii=False, indent=1))
    channels = {}
    for batch in data:
        for rank, r in enumerate(batch['rows'], 1):
            cid = r.get('channel_id')
            if not cid: continue
            c = channels.setdefault(cid, dict(channel_id=cid, name=r.get('channel'), discoveries=[]))
            c['discoveries'].append(dict(query=batch['query'], rank=rank, video_id=r['id'], title=r.get('title')))
    (RAW / 'discovered_channels.json').write_text(json.dumps(sorted(channels.values(), key=lambda c: len(c['discoveries']), reverse=True), ensure_ascii=False, indent=1))
    print('Unique channels', len(channels), flush=True)

def tabs():
    channels = json.loads((RAW / 'selected_channels.json').read_text())
    jobs = [(c['channel_id'], tab) for c in channels for tab in ['videos', 'shorts']]
    def one(job):
        cid, tab = job
        return run_json(f'{cid}_{tab}', ['--flat-playlist', '--dump-json', '--playlist-end', '40', '--extractor-args', 'youtubetab:approximate_date', f'https://www.youtube.com/channel/{cid}/{tab}'])
    with cf.ThreadPoolExecutor(6) as ex:
        list(ex.map(one, jobs))

def metadata(ids):
    def one(vid):
        return run_json(f'video_{vid}', ['--skip-download', '--ignore-no-formats-error', '--extractor-args', 'youtube:player_client=web', '--dump-json', f'https://www.youtube.com/watch?v={vid}'])
    with cf.ThreadPoolExecutor(5) as ex:
        list(ex.map(one, ids))

if __name__ == '__main__':
    RAW.mkdir(exist_ok=True)
    if sys.argv[1] == 'search': searches()
    elif sys.argv[1] == 'tabs': tabs()
    elif sys.argv[1] == 'metadata': metadata(sys.argv[2:])
