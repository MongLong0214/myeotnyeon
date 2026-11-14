#!/usr/bin/env python3
"""Screen candidate text before staging; check staged blobs before committing.

Usage: python3 repo_check.py screen   # refresh exclusions; names-only local report
       python3 repo_check.py check    # reject unsafe staged blobs
No source file is rewritten. Reports contain paths and rule names, never values.
"""
import collections
import hashlib
import json
import math
import os
from pathlib import Path
import re
import stat
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
LIMIT = 50_000_000  # owner 11-14: loosened from 1 MB
START = '# BEGIN repo_check generated exclusions'
END = '# END repo_check generated exclusions'
SKIP = {'.git', 'node_modules', '.venv', 'venv', '__pycache__', '.cache',
        'cache', 'caches', 'models', 'checkpoints', 'out', 'renders', 'bundle',
        'frames', 'tmp', '.tmp', '_work', 'dist', 'build', '.next', '.remotion'}
EXTS = {'.py', '.ts', '.tsx', '.js', '.cjs', '.mjs', '.json', '.md', '.txt',
        '.csv', '.jsonl', '.sh', '.toml', '.yaml', '.yml', '.ini', '.cfg',
        '.conf', '.config', '.lock', '.css', '.html', '.swift', '.tsv', '.srt',
        '.vtt', '.ass'}
NAMES = {'Dockerfile', 'Makefile', 'Procfile', '.gitignore', '.gitattributes',
         '.editorconfig', '.npmrc', '.nvmrc', '.python-version'}
UNTOUCHED = ('research/tools/stickman-video-director', 'tts_lab/engines/melotts/src',
             'production/lf_toon', 'episodes/review_full')
PATTERNS = {
    'private-key': r'-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----',
    'provider-token': r'\b(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16}|AIza[A-Za-z0-9_-]{30,}|xox[baprs]-[A-Za-z0-9-]{16,})\b',
    'bearer': r'(?i)\bBearer\s+[A-Za-z0-9._~-]{16,}',
    'jwt': r'\beyJ[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}\.[A-Za-z0-9_-]{12,}',
    'credential-url': r'(?i)\b[a-z][a-z0-9+.-]*://[^\s/:@]+:[^\s/@]+@',
}
COMPILED = {k: re.compile(v) for k, v in PATTERNS.items()}
# owner 11-14 "보안 최대한 느슨하게": entropy, email and phone rules are off; only rules that match real credential
# formats stay (private keys, provider tokens, bearer/JWT, credential URLs, credential assignments).
ENTROPY_RULE = False
ASSIGN = re.compile(r'''(?ix)(?:api[_-]?key|token|client[_-]?(?:secret|id)|secret|password|passwd|authorization|cookie|session[_-]?(?:id|key))[a-z0-9_]{0,64}["']?\s*[:=]\s*["']([^"'\r\n]{4,})["']''')
UNQUOTED = re.compile(r'(?im)^\s*(?:export\s+)?[A-Z0-9_]*(?:API_?KEY|TOKEN|SECRET|PASSWORD|PASSWD|COOKIE)[A-Z0-9_]*\s*[:=]\s*([^\s\x22\x27#]{4,})\s*(?:#.*)?$')
TOKEN = re.compile(r'(?<![A-Za-z0-9_])[A-Za-z0-9_+/=-]{24,160}(?![A-Za-z0-9_])')
PLACEHOLDER = re.compile(r'(?i)^(?:\$|<|\{|your[_ -]|example|placeholder|dummy|test[_ -]|changeme|none$|null$|undefined$|redacted|\*+$)|(?:process\.env|os\.(?:environ|getenv))')


def git(*args, data=None):
    return subprocess.run(['git', *args], cwd=ROOT, input=data,
                          stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True).stdout


# Public source citations are not credentials, but long news/PDF paths trip the entropy rule. Only these URL fields are
# exempt from entropy (never from the pattern rules, which run on the full text first): episode spec "url" values,
# the "url: " first line of a source snapshot, and "outlet | url" lines in package meta.txt. Userinfo URLs, URLs with a
# query string or fragment, and hosts that carry secrets in the path (webhooks) are never exempt.
SOURCE_FIELD = {
    'spec': (re.compile(r'^episodes/specs/[^/]+\.json$|^factory/specs/golden/[^/]+\.json$|^factory/specs/eval/[^/]+\.json$'),
             re.compile(r'"url"\s*:\s*"(https?://[^"\s]+)"')),
    'snapshot': (re.compile(r'^(?:episodes/specs|factory/specs/(?:golden|eval))/[^/]+\.sources/S\d\.txt$'), re.compile(r'\Aurl: (https?://\S+)')),
    'meta': (re.compile(r'^upload/pkg/[^/]+/meta\.txt$'), re.compile(r'(?m)^[^|\n]{2,80} \| (https?://\S+)$')),
    'case_pack': (re.compile(r'^factory/specs/eval/[^/]+\.md$'), re.compile(r'(?m)^- S\d [^\n]{1,40}? (https?://\S+)')),
}
SECRET_PATH_HOSTS = re.compile(r'(?i)^https?://(?:hooks\.slack\.com|(?:[a-z0-9-]+\.)?discord(?:app)?\.com/api/webhooks|[^/]*webhook|[^/]*\.logic\.azure\.com|outlook\.office\.com/webhook)')


def citation_urls_removed(text, path):
    """text with exempt citation URLs blanked, for the entropy scan only"""
    for rx_path, rx_url in SOURCE_FIELD.values():
        if path and rx_path.search(path):
            def blank(m):
                u = m.group(1)
                if re.search(r'[?#]|://[^/]*@', u) or SECRET_PATH_HOSTS.search(u):
                    return m.group(0)
                return m.group(0).replace(u, 'https://citation')
            text = rx_url.sub(blank, text)
    return text


def findings(data, path=None):
    if b'\0' in data:
        return ['binary']
    try:
        text = data.decode('utf-8-sig')
    except UnicodeDecodeError:
        return ['non-utf8']
    if path == '.gitignore':
        # Generated entries are filenames already screened as filenames, not values.
        # Do not mistake path entropy in the names-only report for credential entropy.
        before, rest = text.split(START, 1)
        _, after = rest.split(END, 1)
        text = before + after
    hits = {k for k, pat in COMPILED.items() if pat.search(text)}
    # a value with whitespace is a message or expression, not a secret (owner 11-14 loosening)
    if any(not PLACEHOLDER.search(m.group(1)) and not re.search(r'\s', m.group(1)) for pattern in (ASSIGN, UNQUOTED)
           for m in pattern.finditer(text)):
        hits.add('credential-assignment')
    for match in (TOKEN.finditer(citation_urls_removed(text, path)) if ENTROPY_RULE else ()):
        value = match.group()
        if not (re.search('[a-zA-Z]', value) and re.search('[0-9]', value)):
            continue
        freq = collections.Counter(value)
        entropy = -sum((n / len(value)) * math.log2(n / len(value)) for n in freq.values())
        # Hashes are also conservatively excluded; no hit is waived automatically.
        if entropy >= 4.5 or (len(value) >= 32 and re.fullmatch('[a-fA-F0-9]+', value) and entropy >= 3.5):
            hits.add('entropy')
            break
    return sorted(hits)


def allowed(path):
    p = Path(path)
    if any(path == x or path.startswith(x + '/') for x in UNTOUCHED):
        return False
    return (p.suffix.lower() in EXTS or p.name in NAMES) and not any(
        x in SKIP or x.startswith('render_') or x.startswith('.bak_')
        or x.startswith('bundle') for x in p.parts[:-1]) and not (
            'review_runs' in p.parts and 'images' in p.parts[:-1]) and not (
            p.name.startswith('render_') and p.suffix not in {'.py', '.ts', '.tsx', '.js', '.cjs', '.mjs', '.sh', '.swift'})


def literal(path):
    return '/' + ''.join('\\' + c if c in '\\*?[]#! ' else c for c in path)


def screen():
    ignore = ROOT / '.gitignore'
    original = ignore.read_text()
    # Keep prior exclusions sticky: a hit must never silently become eligible again.
    prior = ROOT / '.git' / 'repo-screen-report.json'
    report = json.loads(prior.read_text()) if prior.exists() else {'excluded': {}}
    excluded = report['excluded']
    inventory = {}
    scanned = 0
    for directory, dirs, files in os.walk(ROOT, followlinks=False):
        dirs[:] = [d for d in dirs if d not in SKIP and not d.startswith(('render_', '.bak_', 'bundle'))
                   and (Path(directory) / d).relative_to(ROOT).as_posix() not in UNTOUCHED]
        for name in files:
            p = Path(directory) / name
            rel = p.relative_to(ROOT).as_posix()
            if rel in excluded:
                continue
            if not allowed(rel) and not name.startswith('.env') and not re.search(r'(?i)(naver.*(?:key|secret)|credentials|cookies)', name):
                continue
            st = p.lstat()
            if not stat.S_ISREG(st.st_mode):
                excluded[rel] = ['non-regular-file']
                continue
            if st.st_size > LIMIT:
                excluded[rel] = sorted(set(excluded.get(rel, [])) | {'over-1MB'})
                continue
            data = p.read_bytes()
            inventory[rel] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
            scanned += 1
            if scanned % 1000 == 0:
                print('Screened', scanned, 'files', flush=True)
            hits = findings(data, rel)
            if name.startswith('.env') or re.search(r'(?i)(naver.*(?:key|secret)|credentials|cookies)', name):
                hits.append('credential-container')
            if hits:
                excluded[rel] = sorted(set(excluded.get(rel, [])) | set(hits))
    rules = '\n'.join(literal(p) for p in sorted(excluded))
    before, rest = original.split(START, 1)
    _, after = rest.split(END, 1)
    ignore.write_text(before + START + '\n' + rules + '\n' + END + after)
    report = {'limit_bytes': LIMIT, 'scanned_small_text_files': scanned, 'excluded': dict(sorted(excluded.items()))}
    prior.write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    (ROOT / '.git' / 'repo-screen-inventory.json').write_text(json.dumps(inventory, ensure_ascii=False))
    counts = collections.Counter(k for rules in excluded.values() for k in rules)
    print(json.dumps({'scanned': scanned, 'excluded_files': len(excluded), 'rules': counts}, ensure_ascii=False))


def check(changed_only=False):
    errors = {}
    total = 0
    entries = list(filter(None, git('ls-files', '--stage', '-z').split(b'\0')))
    if changed_only:
        changed = set(git('diff', '--cached', '--name-only', '--diff-filter=ACMRTUXB', '-z').split(b'\0'))
        entries = [entry for entry in entries if entry.split(b'\t', 1)[1] in changed]
    if not entries:
        print('No staged files to check')
        return False
    paths = [entry.split(b'\t', 1)[1] for entry in entries]
    ignored = subprocess.run(['git', 'check-ignore', '--no-index', '-z', '--stdin'],
                             cwd=ROOT, input=b'\0'.join(paths) + b'\0',
                             stdout=subprocess.PIPE, check=False)
    if ignored.returncode not in {0, 1}:
        raise RuntimeError('git check-ignore failed')
    ignored_paths = set(ignored.stdout.split(b'\0'))
    batch = subprocess.Popen(['git', 'cat-file', '--batch'], cwd=ROOT,
                             stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    for entry in entries:
        meta, rawpath = entry.split(b'\t', 1)
        mode, oid, stage = meta.decode().split()
        path = os.fsdecode(rawpath)
        reasons = []
        if mode not in {'100644', '100755'} or stage != '0':
            reasons.append('non-regular-or-unmerged')
        if not allowed(path):
            reasons.append('excluded-type-or-directory')
        if rawpath in ignored_paths:
            reasons.append('gitignored')
        batch.stdin.write(oid.encode() + b'\n')
        batch.stdin.flush()
        header = batch.stdout.readline().split()
        size = int(header[2])
        data = batch.stdout.read(size)
        assert batch.stdout.read(1) == b'\n'
        if size > LIMIT:
            reasons.append('over-1MB')
        else:
            reasons.extend(findings(data, path))
        if reasons:
            errors[path] = sorted(set(reasons))
        total += size
    batch.stdin.close()
    batch.stdout.close()
    if batch.wait() != 0:
        raise RuntimeError('git cat-file failed')
    print(json.dumps({'files': len(entries), 'bytes': total, 'rejected': errors}, ensure_ascii=False, indent=2))
    return bool(errors)


if __name__ == '__main__':
    os.chdir(ROOT)
    if sys.argv[1:] == ['screen']:
        screen()
    elif sys.argv[1:] == ['check']:
        sys.exit(check())
    elif sys.argv[1:] == ['check-staged']:
        sys.exit(check(changed_only=True))
    else:
        sys.exit('Usage: python3 repo_check.py screen|check|check-staged')
