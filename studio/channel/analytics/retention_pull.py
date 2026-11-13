"""Per-video audience retention through the YouTube Analytics API (read-only), analysed with
factory/lib/retention.py and matched to the spoken lines.

  .venv/bin/python channel/analytics/retention_pull.py                      # the default three Shorts
  .venv/bin/python channel/analytics/retention_pull.py VIDEO_ID=path/to/subs.srt ...

OAuth comes from the macOS keychain (KEYCHAIN_SERVICE_PREFIX.youtube.oauth_client_json,
KEYCHAIN_SERVICE_PREFIX.youtube.oauth_refresh_token), the same items api_pull.py uses. Secrets are never printed
or written; API errors are written verbatim with any token-looking string redacted.
Writes channel/analytics/retention/<video_id>.json and summary.md.
"""
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'factory'))
from lib import retention as rt  # noqa: E402

OUT = ROOT / 'channel' / 'analytics' / 'retention'
START = '2026-10-01'
SCOPES = ['https://www.googleapis.com/auth/yt-analytics.readonly', 'https://www.googleapis.com/auth/youtube.readonly']
# Published Shorts with a transcript of the published audio. The q013/q014 episode SRTs
# (subtitles.ko.srt) are an earlier cut (28.7 s / 33.2 s); the published v52 builds use v52/mix_master.wav,
# whose aligned transcript is v52/asr_master.json.
DEFAULT = {
    'VBEjj7mPjrI': ('q013', 'episodes/quiz/q013/v52/asr_master.json'),
    'oxZUrYF8Chg': ('q014', 'episodes/quiz/q014/v52/asr_master.json'),
    'S_apLF1EfZM': ('q020', 'upload/pkg/q020_batch1107/asr_master.json'),
    'zwgKEbvbxsU': ('q002', 'episodes/quiz/q002/subtitles.ko.srt'),
    'E4zk6oCIbjA': ('q007', 'episodes/quiz/q007/subtitles.ko.srt'),
}


def kc(service):
    return subprocess.check_output(['security', 'find-generic-password', '-s', service, '-w'],
                                   stderr=subprocess.DEVNULL).decode().strip()


def redact(s):
    return re.sub(r'(ya29\.[\w.-]+|1//[\w.-]+|GOCSPX-[\w-]+|[\w-]{40,})', '<redacted>', str(s))


def clients():
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    cfg = json.loads(kc('KEYCHAIN_SERVICE_PREFIX.youtube.oauth_client_json'))
    cfg = cfg.get('installed') or cfg.get('web')
    creds = Credentials(None, refresh_token=kc('KEYCHAIN_SERVICE_PREFIX.youtube.oauth_refresh_token'), token_uri=cfg['token_uri'],
                        client_id=cfg['client_id'], client_secret=cfg['client_secret'], scopes=SCOPES)
    return (build('youtubeAnalytics', 'v2', credentials=creds, cache_discovery=False),
            build('youtube', 'v3', credentials=creds, cache_discovery=False))


def iso_seconds(d):
    m = re.fullmatch(r'P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', d or '')
    if not m:
        return None
    dd, h, mi, s = (int(x or 0) for x in m.groups())
    return dd * 86400 + h * 3600 + mi * 60 + s


def pull(ya, yt, vid, transcript):
    end = datetime.date.today().isoformat()
    rec = dict(video_id=vid, start_date=START, end_date=end, transcript=transcript,
               query=dict(dimensions='elapsedVideoTimeRatio', metrics='audienceWatchRatio,relativeRetentionPerformance',
                          filters=f'video=={vid}'))
    try:
        v = yt.videos().list(part='contentDetails,snippet', id=vid).execute().get('items', [])
        rec['title'] = v[0]['snippet']['title'] if v else None
        rec['duration_s'] = iso_seconds(v[0]['contentDetails']['duration']) if v else None
    except Exception as e:  # noqa: BLE001 - report verbatim
        rec['duration_error'] = redact(e)[:600]
    try:
        resp = ya.reports().query(ids='channel==MINE', startDate=START, endDate=end, **rec['query']).execute()
    except Exception as e:  # noqa: BLE001
        rec['error'] = redact(e)[:1200]
        return rec
    rec['raw'] = dict(columnHeaders=resp.get('columnHeaders'), rows=resp.get('rows', []))
    rows, rel = rt.rows_from_api(resp)
    if len(rows) < 8:
        rec['error'] = f'query succeeded (HTTP 200) but returned {len(rows)} curve points for {START}..{end}'
        return rec
    dur = rec.get('duration_s')
    res = rt.analyse(rows, 'percent', dur, cutoff_s=rt.SHORTS_CUTOFF_S, rel=rel, end_s=rt.SHORTS_END_S)
    cues = rt.load_cues(ROOT / transcript)
    rec['transcript_end_s'] = round(cues[-1][1], 2) if cues else None
    rec['analysis'] = rt.attach_lines(res, cues, window=0.3)
    return rec


def summary(recs):
    lines = ['# Shorts retention — top drops with the spoken line', '',
             f'Pulled {datetime.date.today().isoformat()} (YouTube Analytics API, read-only; window {START}–today). '
             f'Hook window {rt.SHORTS_CUTOFF_S} s. `lost` = points of audienceWatchRatio x100 lost across one 1 % step; '
             '`rel` = relativeRetentionPerformance at the step end (0.5 = typical for similar-length videos).', '']
    for r in recs:
        lines.append(f"## {r.get('qid') or ''} {r['video_id']} — {r.get('title') or ''}")
        if 'error' in r:
            lines += ['', f"API error: `{r['error']}`", '']
            continue
        a = r['analysis']
        lines += ['', f"duration {r.get('duration_s')} s (transcript ends {r.get('transcript_end_s')} s) · start {a['start']} % "
                      f"→ end {a['end']} % · hook leak in first {a['cutoff_s']} s: {a['hook_leak']} pts · slide "
                      f"{a['slide_per_unit']} per {a['slide_unit']} · last {a['end_s']} s (sign-off) {a['end_drop']} pts", '',
                  *(["**transcript does not match the published length; lines below are unreliable**", '']
                    if r.get('duration_s') and r.get('transcript_end_s') and abs(r['duration_s'] - r['transcript_end_s']) > 2.5 else []),
                  f"transcript: `{r['transcript']}`", '',
                  '| at (s) | lost | rel | line |', '|---|---|---|---|']
        for c in a['cliffs']:
            lines.append(f"| {c['at_seconds']}–{c['to_seconds']} | {c['lost']} | {c.get('relative_retention', '')} | {c.get('said', '')} |")
        if not a['cliffs']:
            lines.append('| — | no drop above 0.8 | | |')
        lines.append('')
    return '\n'.join(lines)


def main(argv):
    targets = {}
    for a in argv:
        key, _, path = a.partition('=')          # [qid:]VIDEO_ID=transcript
        qid, _, vid = key.rpartition(':')
        targets[vid] = (qid or None, path)
    targets = targets or DEFAULT
    OUT.mkdir(parents=True, exist_ok=True)
    try:
        ya, yt = clients()
    except Exception as e:  # noqa: BLE001
        print('auth error:', redact(e)[:600])
        return 1
    recs = []
    for vid, (qid, path) in targets.items():
        r = pull(ya, yt, vid, path)
        r['qid'] = qid
        (OUT / f'{vid}.json').write_text(json.dumps(r, ensure_ascii=False, indent=1))
        recs.append(r)
        print(vid, 'ERROR ' + r['error'][:300] if 'error' in r else f"ok points={r['analysis']['points']} cliffs={len(r['analysis']['cliffs'])}")
    (OUT / 'summary.md').write_text(summary(recs))
    print(OUT / 'summary.md')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
