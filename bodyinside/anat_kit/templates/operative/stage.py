"""Run one Body Inside operative stage at a time."""
import argparse
import fcntl
import json
import subprocess
import sys
from pathlib import Path

from compose import assemble, assembly_signature, comparison_frames, compose_frame, mix_audio, preflight
from quality import playback, reference
from recipe import HERE, KIT, LIB, assets, digest, read, save, timeline
from render import Shots
from review import author, compare
from trial import write_evidence
from description_gate import check_description
from evidence_packet import contact_receipt, edition_sources, preflight_recipe


def verify_movie(folder, tag):
    movie = folder / f'{tag}.mp4'
    receipt = read(folder / 'gates' / f'{tag}_assembly.json')
    if digest(movie) != receipt['sha256']:
        raise ValueError(f'{tag} differs from its assembly receipt')
    return movie, receipt


def prepare(root, folder, case, tag, replay_author):
    if replay_author:
        path = folder / 'author.json'
        recorded = read(HERE / 'evidence/sonnet_trials.json')[case]['author']
        if path.exists() and read(path) != recorded:
            raise ValueError('This folder contains a different author recipe')
        if not path.exists():
            save(path, recorded)
    authored = author(folder, case)
    rows = authored['steps']
    segments = timeline(case, rows)
    manifest = assets(case)
    preflight_recipe(folder, case, rows, manifest)
    write_evidence(folder, case, rows, segments, manifest)
    ok, description = check_description(folder / 'description.txt', narrated=False)
    if not ok:
        raise ValueError(description)
    audio = folder / 'mix.wav'
    save(folder / 'audio.json', mix_audio(audio, segments, LIB['steps']))
    episodes = folder / 'gates'
    settings_path = episodes / f'{tag}_settings.json'
    settings = read(settings_path) if settings_path.exists() else {}
    shots = Shots(root / 'cache', case, settings)
    plan, result = preflight(folder, tag, segments, shots, settings)
    print(json.dumps(result, ensure_ascii=False), flush=True)
    if not result['pass_stills']:
        raise ValueError('Low-resolution still preflight failed')
    return rows, segments, settings, shots, plan, audio


def gate(folder, tag):
    movie, receipt = verify_movie(folder, tag)
    audio = playback(movie, receipt['frames'])
    save(folder / 'gates' / f'{tag}_audio.json', {**read(folder / 'audio.json'), **audio})
    edition_sources(folder, tag)
    contact_receipt(folder, tag)
    ok, description = check_description(folder / 'description.txt', narrated=False)
    if not ok:
        raise ValueError(description)
    print(json.dumps(audio))
    if not all(audio[key] for key in ('continuous', 'seam_ok', 'peak_ok')):
        raise ValueError('Encoded audio fails continuity, loop seam or peak threshold')
    return movie, receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('stage', choices=['preflight', 'draft', 'gates', 'compare', 'hq', 'post'])
    parser.add_argument('case', choices=LIB['cases'])
    parser.add_argument('--work', type=Path, required=True)
    parser.add_argument('--tag', default='draft1', choices=[f'draft{i}' for i in range(1, 6)])
    parser.add_argument('--replay-author', action='store_true', help='reuse the recorded Sonnet recipe')
    parser.add_argument('--confirmed', help='SHA-256 of the draft explicitly confirmed by the owner for HQ')
    args = parser.parse_args()
    root = args.work.resolve()
    folder = root / args.case
    gates = folder / 'gates'
    gates.mkdir(parents=True, exist_ok=True)
    with (folder / 'trial.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        if args.stage == 'post':
            tag = args.tag + '_hq'
            movie, receipt = gate(folder, tag)
            subprocess.run([sys.executable, KIT / 'gates/review_gate.py', folder, tag,
                            '--operative', '--model', 'opus'], check=True)
            print(f'Post passed for {movie} ({receipt["sha256"]})')
            return
        if args.stage == 'gates':
            gate(folder, args.tag)
            return
        rows, segments, settings, shots, plan, audio = prepare(
            root, folder, args.case, args.tag, args.replay_author)
        if args.stage in ('compare', 'hq'):
            movie, receipt = verify_movie(folder, args.tag)
            if assembly_signature(plan, settings, audio) != receipt['signature']:
                raise ValueError('The draft recipe, inputs or settings changed since assembly')
            gate(folder, args.tag)
            ref = reference(root, folder)
            if digest(Path(ref['movie'])) != ref['sha256']:
                raise ValueError('Reference no longer matches its audit')
            if args.stage == 'hq':
                pair = read(gates / f'pair_{args.tag}' / 'opus.json')
                score = read(gates / f'{args.tag}_review_opus.json')
                if (args.confirmed != receipt['sha256'] or not ref['certified']
                        or pair['sha256'][:2] != [receipt['sha256'], ref['sha256']]
                        or not pair['pass_pair'] or not score['pass']
                        or score.get('_md5') != movie_md5(movie)):
                    raise ValueError('HQ needs owner confirmation, a certified reference and passing Opus reviews')
        if args.stage == 'preflight':
            return
        if args.stage == 'draft':
            print(assemble(folder, args.tag, plan, shots, settings, audio))
            return
        if args.stage == 'compare':
            result = compare(folder, args.tag, Path(ref['movie']), Path(ref['audit']), segments, {
                'audio.json': gates / f'{args.tag}_audio.json',
                'contact.json': contact_receipt(folder, args.tag),
                'facts.json': gates / f'{args.tag}_facts.json',
                'licences.md': folder / 'LICENCE_AUDIT.md',
                'sources.md': folder / 'SOURCES.md',
                'assets.json': folder / 'assets.json',
            })
            print(json.dumps(result, ensure_ascii=False))
            subprocess.run([sys.executable, KIT / 'gates/review_gate.py', folder, args.tag,
                            '--operative', '--draft', '--model', 'opus'], check=True)
            if not result['pass_pair'] or not ref['certified']:
                raise ValueError('The comparison did not establish a production pass')
            return
        master = Shots(root / 'cache', args.case, settings, (1080, 1920))
        final_plan = [(shot, start, end, caption, badge, count,
                       master.load(shot, count, 'render', [])[0], geometry)
                      for shot, start, end, caption, badge, count, _, geometry in plan]
        tag = args.tag + '_hq'
        print(assemble(folder, tag, final_plan, master, settings, audio))
        choice = next(row for row in rows if row['step'] in ('expose_crown', 'deliver_whole'))
        shot, _, _, caption, badge, count, path, geometry = next(
            row for row in final_plan if row[0] == choice['step'])
        thumb = choice['thumbnail']
        before = comparison_frames(master, shot, count, [thumb], settings).get(thumb)
        compose_frame(path, thumb, count, caption, badge, geometry[thumb]['leader'],
                      settings.get(shot, {}), before).save(folder / 'thumbnail.jpg', quality=94)


def movie_md5(movie):
    import hashlib
    with movie.open('rb') as stream:
        return hashlib.file_digest(stream, 'md5').hexdigest()


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        raise SystemExit(str(error))
