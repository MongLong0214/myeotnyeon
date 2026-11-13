#!/usr/bin/env python3
"""Publish queue and ledger for every channel in factory/channels/registry.json.

  queue.py status [--channel KEY]          package state per upload/pkg/*_B with READY.txt
  queue.py next-slots --channel KEY [--n 4] next free publish slots (KST) from ledger + registry
  queue.py record --pkg P --video ID --publish-at ISO --channel KEY [--state scheduled|published]
  queue.py mark --video ID --state deleted|replaced [--note TEXT]
  queue.py verify [--channel KEY]          read-only YouTube Data API check of privacy, publishAt, channel
  queue.py judge --channel KEY [--stats F --baseline F]   experiment kill rule (registry experiment_kill_rule)

Readback: each channel uses its own read-only OAuth token (for a brand channel, pick that brand channel at consent)
when present; otherwise the Data API key, which returns public videos only: scheduled and
private videos are invisible to it, and it has no Analytics (no 48 h views, no engaged views), so judge needs the token.

States: built (READY.txt, no CTO_PASS) -> approved (CTO_PASS) -> scheduled/published (ledger record).
The ledger keeps its historical shape (entries[].qid/video_id/state/date) so older readers keep working;
new records add channel, pkg and publish_at. Writes are atomic (tmp + rename) after a timestamped backup.
"""
import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

# this file is named queue.py: keep it from shadowing the stdlib queue module that the Google client imports
sys.path[:] = [p for p in sys.path if Path(p or '.').resolve() != Path(__file__).resolve().parent]

ROOT = Path(os.environ.get('FACTORY_ROOT', Path(__file__).resolve().parents[2]))
REGISTRY = Path(os.environ.get('FACTORY_REGISTRY', ROOT / 'factory/channels/registry.json'))
if not REGISTRY.exists() and 'FACTORY_REGISTRY' not in os.environ:
    REGISTRY = ROOT / 'factory/channels/registry.example.json'
LEDGER = Path(os.environ.get('FACTORY_LEDGER', ROOT / 'upload/ledger.json'))
PKG = Path(os.environ.get('FACTORY_PKG', ROOT / 'upload/pkg'))
KST = dt.timezone(dt.timedelta(hours=9))
LIVE = ('scheduled', 'published')
# Keychain service prefix: <prefix>.oauth_client_json, <prefix>.api_key, <prefix>.oauth_refresh_token[.<channel key>].
KEYCHAIN = os.environ.get('FACTORY_KEYCHAIN_PREFIX', 'studio.youtube')
# The baseline channel; its token has no suffix, and ledger entries without a channel belong to it.
OWN = os.environ.get('FACTORY_OWN_CHANNEL', 'main')


def load_json(p, default=None):
    try:
        return json.loads(Path(p).read_text())
    except FileNotFoundError:
        return default


def registry():
    return {c['key']: c for c in load_json(REGISTRY)['channels']}


def ledger():
    return load_json(LEDGER, {'entries': []})


def write_ledger(data):
    LEDGER.parent.mkdir(parents=True, exist_ok=True)
    if LEDGER.exists():
        bak = LEDGER.parent / 'ledger_bak'
        bak.mkdir(exist_ok=True)
        shutil.copy2(LEDGER, bak / f"ledger.{dt.datetime.now().strftime('%Y%m%dT%H%M%S%f')}.json")
    fd, tmp = tempfile.mkstemp(dir=LEDGER.parent, prefix='.ledger.', suffix='.json')
    with os.fdopen(fd, 'w') as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
        f.write('\n')
        f.flush()
        os.fsync(f.fileno())
    os.replace(tmp, LEDGER)


def channel_of_pkg(name, reg):
    stem = name[:-2] if name.endswith('_B') else name
    for key, c in sorted(reg.items(), key=lambda kv: -len(kv[1]['package_prefix'])):
        if re.fullmatch(re.escape(c['package_prefix']) + r'\d+', stem):
            return key, stem
    return None, stem


def parse_at(s):
    t = dt.datetime.fromisoformat(s.replace('Z', '+00:00'))
    if t.tzinfo is None:
        t = t.replace(tzinfo=KST)
    return t


def live_entries(led, channel=None):
    out = []
    for e in led.get('entries', []):
        if e.get('state') not in LIVE:
            continue
        if channel and e.get('channel', OWN) != channel:
            continue
        out.append(e)
    return out


def package_states(reg, led, channel=None):
    by_pkg = {}
    for e in live_entries(led):
        by_pkg.setdefault(e.get('pkg') or e.get('qid'), e)
    rows = []
    for d in sorted(PKG.glob('*_B')):
        if not (d / 'READY.txt').exists():
            continue
        key, stem = channel_of_pkg(d.name, reg)
        if channel and key != channel:
            continue
        e = by_pkg.get(d.name) or by_pkg.get(stem)
        if e:
            state = e['state']
            at = e.get('publish_at') or e.get('date')
            if state == 'scheduled' and at and parse_at(at) <= dt.datetime.now(KST):
                state = 'published'
        elif any(d.glob('CTO_PASS*')):
            state = 'approved'
        else:
            state = 'built'
        rows.append(dict(pkg=d.name, channel=key, state=state, video_id=(e or {}).get('video_id'),
                         publish_at=(e or {}).get('publish_at') or (e or {}).get('date')))
    return rows


def next_slots(reg, led, channel, n=4, now=None):
    c = reg[channel]
    now = now or dt.datetime.now(KST)
    taken = set()
    for e in live_entries(led, channel):
        at = e.get('publish_at') or e.get('date')
        if at:
            taken.add(parse_at(at).astimezone(KST).replace(second=0, microsecond=0))
    slots, day = [], now.astimezone(KST).date()
    while len(slots) < n:
        for hm in c['publish_slots_kst']:
            h, m = map(int, hm.split(':'))
            t = dt.datetime(day.year, day.month, day.day, h, m, tzinfo=KST)
            if t > now + dt.timedelta(minutes=30) and t not in taken and len(slots) < n:
                slots.append(t)
        day += dt.timedelta(days=1)
    return slots


def cmd_status(a):
    reg, led = registry(), ledger()
    rows = package_states(reg, led, a.channel)
    counts = {}
    for r in rows:
        counts[r['state']] = counts.get(r['state'], 0) + 1
        print(f"{r['pkg']:<10} {r['channel'] or '?':<16} {r['state']:<10} {r['video_id'] or '':<12} {r['publish_at'] or ''}")
    print('summary', json.dumps(counts, sort_keys=True))


def cmd_next(a):
    for t in next_slots(registry(), ledger(), a.channel, a.n):
        print(t.isoformat())


def cmd_record(a):
    reg, led = registry(), ledger()
    if a.channel not in reg:
        sys.exit(f'unknown channel {a.channel}')
    at = parse_at(a.publish_at).astimezone(KST).isoformat()
    for e in led['entries']:
        if e.get('video_id') == a.video:
            sys.exit(f'video {a.video} already in ledger ({e.get("qid")}, {e.get("state")})')
    clash = [e for e in live_entries(led, a.channel) if (e.get('publish_at') or e.get('date')) and
             parse_at(e.get('publish_at') or e['date']) == parse_at(at)]
    if clash:
        sys.exit(f'slot {at} already taken by {clash[0].get("qid")} {clash[0].get("video_id")}')
    _, stem = channel_of_pkg(a.pkg, reg)
    led['entries'].append(dict(qid=stem, pkg=a.pkg, channel=a.channel, video_id=a.video, state=a.state,
                               date=at, publish_at=at, evidence=[a.evidence] if a.evidence else [],
                               recorded_at=dt.datetime.now(KST).isoformat(timespec='seconds')))
    write_ledger(led)
    print('recorded', stem, a.video, at)


def cmd_mark(a):
    led = ledger()
    hit = [e for e in led['entries'] if e.get('video_id') == a.video]
    if not hit:
        sys.exit(f'video {a.video} not in ledger')
    for e in hit:
        e['state'] = a.state
        if a.note:
            e['note'] = a.note
    write_ledger(led)
    print('marked', a.video, a.state)


def kc(service):
    """Keychain value or None. Values stay in memory and are never printed."""
    r = subprocess.run(['security', 'find-generic-password', '-s', service, '-w'], capture_output=True, text=True)
    return r.stdout.strip() or None if r.returncode == 0 else None


def token_service(channel):
    # The baseline channel's token has no suffix; every other (brand) channel gets its own read-only token, created by
    # an OAuth consent run in which that brand channel is picked.
    return KEYCHAIN + '.oauth_refresh_token' + ('' if channel == OWN else '.' + channel)


def credentials(channel=None):
    """OAuth credentials for one channel, or None when that channel has no token yet."""
    channel = channel or OWN
    refresh = kc(token_service(channel))
    if not refresh:
        return None
    from google.oauth2.credentials import Credentials
    cfg = json.loads(kc(KEYCHAIN + '.oauth_client_json'))['installed']
    return Credentials(None, refresh_token=refresh, token_uri=cfg['token_uri'], client_id=cfg['client_id'],
                       client_secret=cfg['client_secret'],
                       scopes=['https://www.googleapis.com/auth/yt-analytics.readonly',
                               'https://www.googleapis.com/auth/youtube.readonly'])


def youtube(channel=None):
    """Data API client: the channel's own OAuth token (sees private/scheduled), else the API key (public videos only)."""
    channel = channel or OWN
    from googleapiclient.discovery import build
    creds = credentials(channel)
    if creds:
        return build('youtube', 'v3', credentials=creds, cache_discovery=False), 'oauth'
    return build('youtube', 'v3', developerKey=kc(KEYCHAIN + '.api_key'), cache_discovery=False), 'apikey'


def verify_rows(entries, items, reg):
    """Pure comparison of ledger entries with videos.list items; returns (entry, verdict) pairs."""
    got = {i['id']: i for i in items}
    out = []
    for e in entries:
        vid, key = e.get('video_id'), e.get('channel', OWN)
        i = got.get(vid)
        want_at = e.get('publish_at') or e.get('date')
        if e.get('state') == 'deleted':
            out.append((e, 'ok-gone' if i is None else 'STILL-EXISTS'))
            continue
        if e.get('state') == 'replaced':
            # Replacements go private and unscheduled; they are never deleted. Older ones may be gone already.
            st = (i or {}).get('status', {})
            ok = i is None or (st.get('privacyStatus') == 'private' and not st.get('publishAt'))
            out.append((e, ('ok-gone' if i is None else 'ok-private') if ok else 'BAD replaced-but-' + str(st.get('privacyStatus'))))
            continue
        if i is None:
            out.append((e, 'MISSING'))
            continue
        st, sn = i.get('status', {}), i.get('snippet', {})
        problems = []
        if sn.get('channelId') != reg.get(key, {}).get('channel_id'):
            problems.append('channel')
        privacy = st.get('privacyStatus')
        due = bool(want_at) and parse_at(want_at) <= dt.datetime.now(KST)
        if e['state'] == 'scheduled' and not (due and privacy == 'public'):
            if privacy == 'public':
                problems.append('already-public')
            elif privacy != 'private' or not st.get('publishAt'):
                problems.append(f'privacy={privacy}')
            elif want_at and parse_at(st['publishAt']) != parse_at(want_at):
                problems.append(f"publishAt={st['publishAt']}")
        elif privacy != 'public':
            problems.append(f'privacy={privacy}')
        out.append((e, 'ok' if not problems else 'BAD ' + ','.join(problems)))
    return out


def cmd_verify(a):
    reg, led = registry(), ledger()
    entries = [e for e in led['entries'] if e.get('video_id') and (not a.channel or e.get('channel', OWN) == a.channel)]
    bad = 0
    for key in sorted({e.get('channel', OWN) for e in entries}):
        group = [e for e in entries if e.get('channel', OWN) == key]
        yt, mode = youtube(key)
        items, ids = [], [e['video_id'] for e in group]
        for k in range(0, len(ids), 50):
            items += yt.videos().list(part='status,snippet', id=','.join(ids[k:k + 50])).execute().get('items', [])
        for e, v in verify_rows(group, items, reg):
            if mode == 'apikey' and v == 'MISSING' and e.get('state') == 'scheduled':
                # An API key sees public videos only; a scheduled (private) video is invisible, not missing.
                v = 'unverified (scheduled; needs this channel\'s OAuth token)'
            elif mode == 'apikey' and v.startswith('ok-gone'):
                v = 'unverified (gone or private; needs OAuth)'
            else:
                bad += not v.startswith('ok')
            print(f"{key:<16} {e.get('qid', ''):<8} {e['video_id']:<12} {e.get('state', ''):<10} {v}")
        if mode == 'apikey':
            print(f'{key}: API key only (public readback). For scheduled/private: create a read-only OAuth token for {key}')
    print('verify', 'ok' if not bad else f'{bad} problem(s)')
    sys.exit(1 if bad else 0)


def judge(rule, stats, baseline=None, now=None):
    """Experiment kill rule (registry experiment_kill_rule). stats: the channel's uploads in publish order, each
    {video_id, views_48h, engaged_views_48h}. baseline: the same for the baseline channel's recent uploads.
    Returns {verdict: pending|stop|continue, ...}. stop never deletes anything."""
    now = now or dt.datetime.now(KST)
    n, views_max, share_max = rule['first_uploads'], rule['views_48h_below'], rule['engaged_share_below']
    if len(stats) < n:
        return dict(verdict='pending', reason=f'{len(stats)}/{n} uploads have 48 h numbers')

    def share(x):
        return (x.get('engaged_views_48h') or 0) / x['views_48h'] if x.get('views_48h') else 0.0

    first = stats[:n]
    if all(x['views_48h'] < views_max and share(x) < share_max for x in first):
        return dict(verdict='stop', reason=f'all first {n}: views_48h < {views_max} and engaged share < {share_max:.0%}',
                    action=rule['action'])

    def med(rows):
        v = sorted(x['views_48h'] for x in rows)
        return (v[(len(v) - 1) // 2] + v[len(v) // 2]) / 2 if v else None

    window = stats[-7:]
    out = dict(verdict='continue', next_review=(now + dt.timedelta(days=rule['rejudge_every_days'])).date().isoformat(),
               median_views_48h=med(window), median_engaged_share=sorted(map(share, window))[len(window) // 2])
    if baseline:
        b = med(baseline[-7:])
        out.update(baseline_median_views_48h=b, ratio_to_baseline=round(out['median_views_48h'] / b, 3) if b else None)
    return out


def views_48h(channel, video_id, published):
    """Views and engaged views over the publish day and the next day (Analytics is day-granular, so this is the
    48 h approximation). Needs the channel's own OAuth token; returns None without one."""
    creds = credentials(channel)
    if not creds:
        return None
    from googleapiclient.discovery import build
    ya = build('youtubeAnalytics', 'v2', credentials=creds, cache_discovery=False)
    d0 = parse_at(published).astimezone(dt.timezone(dt.timedelta(hours=-8))).date()  # Analytics days are US Pacific
    r = ya.reports().query(ids='channel==MINE', startDate=d0.isoformat(), endDate=(d0 + dt.timedelta(days=1)).isoformat(),
                           metrics='views,engagedViews', filters=f'video=={video_id}').execute()
    row = (r.get('rows') or [[0, 0]])[0]
    return dict(video_id=video_id, views_48h=int(row[0]), engaged_views_48h=int(row[1]))


def channel_stats(led, channel, now=None):
    now = now or dt.datetime.now(KST)
    rows = sorted((e for e in led['entries'] if e.get('channel', OWN) == channel and e.get('state') in LIVE
                   and e.get('video_id') and (e.get('publish_at') or e.get('date'))),
                  key=lambda e: parse_at(e.get('publish_at') or e['date']))
    out = []
    for e in rows:
        at = e.get('publish_at') or e['date']
        if parse_at(at) + dt.timedelta(hours=48) > now:
            break
        s = views_48h(channel, e['video_id'], at)
        if s is None:
            sys.exit(f'{channel}: no OAuth token; create a read-only OAuth token for {channel} (pick that channel at consent)')
        out.append(s)
    return out


def cmd_judge(a):
    reg, led = registry(), ledger()
    rule = load_json(REGISTRY)['experiment_kill_rule']
    if reg[a.channel].get('status') != 'experiment':
        sys.exit(f'{a.channel} is not an experiment channel')
    if a.stats:
        stats, base = load_json(a.stats), load_json(a.baseline) if a.baseline else None
    else:
        stats, base = channel_stats(led, a.channel), channel_stats(led, rule['baseline_channel'])
    print(json.dumps(dict(channel=a.channel, **judge(rule, stats, base)), ensure_ascii=False))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    s = p.add_subparsers(dest='cmd', required=True)
    x = s.add_parser('status'); x.add_argument('--channel'); x.set_defaults(f=cmd_status)
    x = s.add_parser('next-slots'); x.add_argument('--channel', required=True); x.add_argument('--n', type=int, default=4); x.set_defaults(f=cmd_next)
    x = s.add_parser('record'); x.set_defaults(f=cmd_record)
    for k in ('--pkg', '--video', '--publish-at', '--channel'):
        x.add_argument(k, required=True)
    x.add_argument('--state', choices=LIVE, default='scheduled'); x.add_argument('--evidence')
    x = s.add_parser('mark'); x.add_argument('--video', required=True); x.add_argument('--state', choices=('deleted', 'replaced'), required=True); x.add_argument('--note'); x.set_defaults(f=cmd_mark)
    x = s.add_parser('verify'); x.add_argument('--channel'); x.set_defaults(f=cmd_verify)
    x = s.add_parser('judge'); x.add_argument('--channel', required=True); x.add_argument('--stats'); x.add_argument('--baseline'); x.set_defaults(f=cmd_judge)
    a = p.parse_args(argv)
    a.f(a)


if __name__ == '__main__':
    main()
