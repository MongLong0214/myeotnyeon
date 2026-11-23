"""Restore or verify checksum-pinned Body Inside assets."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from urllib.parse import unquote, urlparse

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    with path.open('rb') as stream:
        sha256 = hashlib.sha256()
        for chunk in iter(lambda: stream.read(1024 * 1024), b''):
            sha256.update(chunk)
        return sha256.hexdigest()


def matches(path, entry):
    return (path.is_file() and path.stat().st_size == entry['size']
            and digest(path) == entry['sha256'])


def file_path(url):
    locator = urlparse(url)
    if locator.scheme == 'file' and locator.netloc in ('', 'localhost'):
        return Path(unquote(locator.path))
    return None


def download(url, path):
    subprocess.run(['curl', '--fail', '--location', '--silent', '--show-error',
                    '--proto', '=https', '--output', path, url], check=True)


def install(entry, target, archive_dir, mirrors):
    candidates = [mirror / entry['path'] for mirror in mirrors]
    origin = file_path(entry.get('local_source') or entry.get('source_url') or '')
    if origin is not None:
        candidates.append(origin)
    if target.exists():
        raise ValueError('existing file differs from manifest')
    target.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(dir=target.parent, prefix='.asset-')
    os.close(fd)
    temp = Path(temp_name)
    try:
        local = next((path for path in candidates if matches(path, entry)), None)
        if local is not None:
            shutil.copyfile(local, temp)
        elif entry.get('archive_member'):
            archive = archive_dir / (entry['archive_sha256'] + '.zip')
            if archive.exists() and digest(archive) != entry['archive_sha256']:
                archive.unlink()
            if not archive.exists():
                partial = archive.with_suffix('.part')
                try:
                    download(entry['download_url'], partial)
                    if digest(partial) != entry['archive_sha256']:
                        raise ValueError('source archive checksum differs')
                    partial.replace(archive)
                finally:
                    partial.unlink(missing_ok=True)
            with zipfile.ZipFile(archive) as pack, pack.open(entry['archive_member']) as src, temp.open('wb') as dst:
                shutil.copyfileobj(src, dst)
        elif entry.get('download_url'):
            download(entry['download_url'], temp)
        elif entry.get('availability') == 'local-mirror-only':
            raise ValueError('no public download; restore it with --mirror from the owner asset backup')
        else:
            raise ValueError('provide a matching local copy or mirror')
        if not matches(temp, entry):
            raise ValueError('restored bytes differ from manifest')
        # Publish the verified copy without replacing a concurrent restore.
        try:
            os.link(temp, target)
        except FileExistsError:
            if not matches(target, entry):
                raise ValueError('a different file appeared during restore')
    finally:
        temp.unlink(missing_ok=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('paths', nargs='*', help='repository-relative file/directory prefixes')
    parser.add_argument('--group', choices=['operative', 'review', 'topic3-replay'])
    parser.add_argument('--mirror', type=Path, action='append', default=[],
                        help='local directory mirroring repository-relative paths')
    parser.add_argument('--verify', action='store_true', help='verify working tree files')
    args = parser.parse_args()
    entries = json.loads((ROOT / 'assets/MANIFEST.json').read_text())['assets']
    selected = [e for e in entries if (not args.group or e.get('group') == args.group)
                and (not args.paths or any(e['path'] == p.rstrip('/') or
                     e['path'].startswith(p.rstrip('/') + '/') for p in args.paths))]
    if not selected:
        parser.error('no matching asset paths')
    unmatched = [p for p in args.paths if not any(e['path'] == p.rstrip('/') or e['path'].startswith(p.rstrip('/') + '/') for e in entries)]
    if unmatched:
        parser.error('no manifest entry for: ' + ', '.join(unmatched))
    failed = 0
    with tempfile.TemporaryDirectory(prefix='bodyinside-assets-') as temp:
        for entry in selected:
            target = ROOT / entry['path']
            if not target.resolve().is_relative_to(ROOT):
                raise ValueError(f'Asset path leaves the worktree: {target}')
            try:
                if not matches(target, entry):
                    if args.verify:
                        raise ValueError('missing or checksum mismatch')
                    install(entry, target, Path(temp), args.mirror)
            except (OSError, ValueError, KeyError, subprocess.CalledProcessError, zipfile.BadZipFile) as exc:
                failed += 1
                print(f"{entry['path']}: {exc}", file=sys.stderr)
    print(f'{len(selected)-failed}/{len(selected)} assets verified')
    return bool(failed)


if __name__ == '__main__':
    raise SystemExit(main())
