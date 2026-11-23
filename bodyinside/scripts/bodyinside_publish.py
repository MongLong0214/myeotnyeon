"""Use the Body Inside Studio uploader with separate private and schedule commands."""
import argparse
import base64
import datetime as dt
import fcntl
import hashlib
import importlib.util
import json
import os
import re
import shutil
import stat
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPL = ROOT / 'factory/ops/uploader/repl'
spec = importlib.util.spec_from_file_location('bodyinside_queue', ROOT / 'factory/ops/queue.py')
queue = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue)


def readback(video_id, expected=None, *, check_slot=True):
    youtube, mode = queue.youtube('anatomy')
    if mode != 'oauth':
        raise ValueError('Authenticate read-only Body Inside OAuth first')
    result = youtube.videos().list(part='snippet,status', id=video_id).execute().get('items', [])
    if len(result) != 1:
        raise ValueError(f'Studio readback could not find {video_id}')
    snippet, status = result[0]['snippet'], result[0]['status']
    scheduled = status.get('publishAt')
    if (snippet.get('channelId') != queue.registry()['anatomy']['channel_id']
            or status.get('privacyStatus') != 'private'
            or status.get('license') != 'youtube'
            or (snippet.get('defaultLanguage'), snippet.get('defaultAudioLanguage')) != ('ko', 'ko')):
        raise ValueError(f'{video_id} must be a private Korean Body Inside video under the standard YouTube licence')
    if check_slot and (queue.parse_at(scheduled) if scheduled else None) != expected:
        raise ValueError(f'{video_id} has unexpected publishAt {scheduled}')
    return {'video_id': video_id, 'visibility': 'private', 'publish_at': scheduled,
            'title': snippet['title']}


def send(code):
    env = dict(os.environ, REPL_NO_RECOVER='1')
    try:
        proc = subprocess.run([REPL / 'send.sh', code, '45'], env=env, capture_output=True,
                              text=True, timeout=330)
    except subprocess.TimeoutExpired as exc:
        raise ValueError('Studio outcome unknown. Check the video ID or Studio before retrying.') from exc
    if proc.returncode or 'REPL session not found' in proc.stdout:
        raise ValueError('Studio outcome unknown. Check the video ID or Studio before retrying.')
    for line in reversed(proc.stdout.splitlines()):
        _, marker, result = line.partition('BODYINSIDE_RESULT=')
        if marker and result.startswith('{'):
            return json.JSONDecoder().raw_decode(result)[0]
    return None


def studio():
    channel = queue.registry()['anatomy']
    inbox = REPL / 'in'
    if (not inbox.exists() or not stat.S_ISFIFO(inbox.stat().st_mode) or not (REPL / 'session_dir').is_file()
            or not (REPL / 'session_dir').read_text().strip()):
        raise ValueError('Start the uploader REPL shown in README.md')
    # This command opens the uploader's tab and checks the active profile identity.
    location = 'https://studio.youtube.com/channel/' + channel['channel_id']
    js = f'var st = await openTab({json.dumps(location)});'
    js += ' await new Promise(r=>setTimeout(r,8000));'
    js += (' console.log("BODYINSIDE_RESULT="+JSON.stringify(await st.evaluate(()=>'
           '({path:location.pathname,name:document.querySelector("#entity-name")?.innerText?.trim()}))));')
    result = send(js)
    if (not result or result['path'].split('/')[2:3] != [channel['channel_id']]
            or result.get('name') != channel['name']):
        raise ValueError('Switch the Aside profile to the Body Inside identity before proceeding')
    return channel


STUDIO_LANGUAGE = {'ko': '한국어', 'en': '영어', 'ja': '일본어'}


def helper_prelude():
    """Channel identity and Studio language for upM.js, read from the local registry."""
    channel = queue.registry()['anatomy']
    names = {channel['channel_id']: channel['name']}
    langs = {channel['channel_id']: STUDIO_LANGUAGE[channel['language']]}
    return (f'var UPLOAD_CHANNELS = {json.dumps(names, ensure_ascii=False)};\n'
            f'var UPLOAD_LANGS = {json.dumps(langs, ensure_ascii=False)};\n')


def load_helpers(*names):
    source = helper_prelude() + '\n'.join((REPL / name).read_text() for name in names)
    encoded = base64.b64encode(source.encode()).decode()
    send(f"(0,eval)(new TextDecoder().decode(Uint8Array.from(atob('{encoded}'),c=>c.charCodeAt(0))));")


def private(folder, tag):
    movie, thumbnail = folder / f'{tag}.mp4', folder / 'thumbnail.jpg'
    if not thumbnail.is_file():
        raise ValueError('Missing reviewed thumbnail.jpg')
    description = (folder / 'description.txt').read_text()
    title, _, description = description.strip().partition('\n')
    with movie.open('rb') as stream:
        sha256 = hashlib.file_digest(stream, 'sha256').hexdigest()
    assembly = json.loads((folder / 'gates' / f'{tag}_assembly.json').read_text())
    review = json.loads((folder / 'gates' / f'{tag}_review_opus.json').read_text())
    with movie.open('rb') as stream:
        md5 = hashlib.file_digest(stream, 'md5').hexdigest()
    if not tag.endswith('_hq') or sha256 != assembly['sha256'] or not review['pass'] or review['_md5'] != md5:
        raise ValueError('Private upload requires the matching passing HQ cut')
    receipt_path = folder / 'gates' / f'{tag}_private_upload.json'
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text())
        if receipt['sha256'] != sha256:
            raise ValueError('The uploaded video differs from this cut')
        return readback(receipt['video_id'])
    channel = studio()
    load_helpers('lang.js', 'upM.js')
    session = Path((REPL / 'session_dir').read_text().strip()) / 'files'
    session.mkdir(exist_ok=True)
    video_name, thumb_name = f'{sha256}.mp4', f'{sha256}.jpg'
    shutil.copyfile(movie, session / video_name)
    shutil.copyfile(thumbnail, session / thumb_name)
    arguments = [channel['channel_id'], './files/' + video_name, './files/' + thumb_name,
                 title, description, 'PRIVATE', '']
    result = send('var bodyInsideUpload=await upM(...' + json.dumps(arguments) +
                  '); console.log("BODYINSIDE_RESULT="+JSON.stringify(bodyInsideUpload));')
    video_id = (result or {}).get('dialog_video_id') or (result or {}).get('video_id')
    saved = video_id and (not result.get('stop') or result.get('video_id') or result.get('sch'))
    if saved:
        receipt_path.write_text(json.dumps({'sha256': sha256, 'video_id': video_id}) + '\n')
        print(f'Studio returned {video_id}', flush=True)
    if not video_id or result.get('stop'):
        raise ValueError(f'Check existing upload in Studio before retrying: {result}')
    return readback(video_id)


def schedule(video_id, publish_at):
    current = readback(video_id, check_slot=False)
    if current['publish_at']:
        if queue.parse_at(current['publish_at']) != publish_at:
            raise ValueError(f'{video_id} already has a different schedule')
        return current
    studio()
    load_helpers('sched.js')
    local = publish_at.astimezone(queue.KST)
    date = f'{local.year}. {local.month}. {local.day}.'
    clock = f'{"오전" if local.hour < 12 else "오후"} {local.hour % 12 or 12}:{local.minute:02d}'
    result = send('var bodyInsideSchedule=await setSched(...' + json.dumps([video_id, date, clock]) +
                  '); console.log("BODYINSIDE_RESULT="+JSON.stringify(bodyInsideSchedule));')
    if not result or not result.get('saved'):
        raise ValueError(f'Schedule was not confirmed for {video_id}: {result}')
    return readback(video_id, publish_at)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    upload = commands.add_parser('private')
    upload.add_argument('folder', type=Path)
    upload.add_argument('tag')
    booking = commands.add_parser('schedule')
    booking.add_argument('video_id')
    booking.add_argument('publish_at')
    check = commands.add_parser('readback')
    check.add_argument('video_id')
    check.add_argument('--publish-at')
    args = parser.parse_args()
    if args.command == 'private':
        with (args.folder / 'gates' / 'studio.lock').open('a') as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            result = private(args.folder, args.tag)
    else:
        if not re.fullmatch(r'[A-Za-z0-9_-]{11}', args.video_id):
            parser.error('invalid 11-character video ID')
        when = dt.datetime.fromisoformat(args.publish_at) if args.publish_at else None
        if when and (when.utcoffset() != dt.timedelta(hours=9) or when.second or when.microsecond):
            parser.error('use an ISO 8601 KST time at minute precision')
        if args.command == 'schedule':
            if when <= dt.datetime.now(queue.KST):
                parser.error('publish time must be in the future')
            result = schedule(args.video_id, when)
        else:
            result = readback(args.video_id, when)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError) as error:
        raise SystemExit(str(error))
