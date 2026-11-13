#!/usr/bin/env python3
"""Publish queue and ledger for every channel in factory/channels/registry.json.

  queue.py status [--channel KEY]          package state per upload/pkg/*_B with READY.txt
  queue.py next-slots --channel KEY [--n 4] next free publish slots (KST) from ledger + registry
  queue.py record --pkg P --video ID --publish-at ISO --channel KEY [--state scheduled|published]
  queue.py mark --video ID --state deleted|replaced [--note TEXT]
  queue.py verify [--channel KEY]          read-only YouTube Data API check of privacy, publishAt, channel

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
# Keychain service prefix holding the read-only OAuth client JSON and refresh token of the verifiable channel.
KEYCHAIN = os.environ.get('FACTORY_KEYCHAIN_PREFIX', 'studio.youtube')
# Channel whose OAuth token verify uses; ledger entries without a channel belong to it.
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


def youtube():
    def kc(s):
        return subprocess.check_output(['security', 'find-generic-password', '-s', s, '-w']).decode().strip()
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    cfg = json.loads(kc(KEYCHAIN + '.oauth_client_json'))['installed']
    creds = Credentials(None, refresh_token=kc(KEYCHAIN + '.oauth_refresh_token'), token_uri=cfg['token_uri'],
                        client_id=cfg['client_id'], client_secret=cfg['client_secret'],
                        scopes=['https://www.googleapis.com/auth/yt-analytics.readonly',
                                'https://www.googleapis.com/auth/youtube.readonly'])
    return build('youtube', 'v3', credentials=creds, cache_discovery=False)


def verify_rows(entries, items, reg):
    """Pure comparison of ledger entries with videos.list items; returns (entry, verdict) pairs."""
    got = {i['id']: i for i in items}
    out = []
    for e in entries:
        vid, key = e.get('video_id'), e.get('channel', OWN)
        i = got.get(vid)
        want_at = e.get('publish_at') or e.get('date')
        if e.get('state') in ('deleted', 'replaced'):
            out.append((e, 'ok-gone' if i is None else 'STILL-EXISTS'))
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
    own = [e for e in entries if e.get('channel', OWN) == OWN]
    other = [e for e in entries if e not in own]
    yt = youtube()
    items = []
    ids = [e['video_id'] for e in own]
    for k in range(0, len(ids), 50):
        items += yt.videos().list(part='status,snippet', id=','.join(ids[k:k + 50])).execute().get('items', [])
    bad = 0
    for e, v in verify_rows(own, items, reg):
        bad += not v.startswith('ok')
        print(f"{e.get('qid', ''):<8} {e['video_id']:<12} {e.get('state', ''):<10} {v}")
    for e in other:
        print(f"{e.get('qid', ''):<8} {e['video_id']:<12} {e.get('state', ''):<10} unverified (no OAuth for {e.get('channel')})")
    print('verify', 'ok' if not bad else f'{bad} problem(s)')
    sys.exit(1 if bad else 0)


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
    a = p.parse_args(argv)
    a.f(a)


if __name__ == '__main__':
    main()
