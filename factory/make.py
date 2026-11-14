#!/usr/bin/env python3
"""Channel-pack factory CLI (files + CLI only; see factory/FACTORY_DESIGN.md).

  .venv/bin/python factory/make.py --channel myeotnyeon --episode channels/myeotnyeon/episodes/q014_factory.json --stage all
  ... --stage render          one stage (its dependencies must already be done)
  ... --stage all --dry-run   print the plan (done / stale / blocked); writes nothing

Each stage writes into the episode output dir (default out/factory/<channel>/<episode>/) and a
record stages/<stage>.json {status, input_hash, outputs{file: sha256}}. A stage is reused only
when status=done, its input hash (channel-pack slice + spec + dependency outputs + code) is
unchanged and every output still has its recorded hash. Stale or partial outputs are moved to
superseded/, never overwritten or deleted. `manual` is a waiting state naming the next owner and
the inputs it needs; it is never done. Upload is always manual: this CLI never uploads.
"""
from pathlib import Path
import os, sys
W = Path(__file__).resolve().parents[1]
PYTHON = W / '.venv/bin/python'
if Path(sys.prefix) != W / '.venv' and PYTHON.exists():
    os.execv(str(PYTHON), [str(PYTHON), __file__, *sys.argv[1:]])
import argparse, copy, hashlib, json, re, shutil, subprocess, time
sys.dont_write_bytecode = True

CHANNELS = Path(os.environ.get('FACTORY_CHANNELS', W / 'channels'))
OUT_ROOT = Path(os.environ.get('FACTORY_OUT_ROOT', W / 'out/factory'))  # env override is for tests only
CONTROL = {'run.json', '.lock', 'stages', 'superseded', 'signoffs'}
HERE = Path(__file__).resolve().parent
MAKE = Path(__file__).resolve()


class Refusal(Exception):
    """Wrong target or unsafe request: nothing is written."""


class StageFail(Exception):
    pass


class Manual(Exception):
    def __init__(self, owner, needs, reason):
        super().__init__(reason); self.owner, self.needs, self.reason = owner, needs, reason


_SHA = {}
OPAQUE = set()  # cloned engine dirs inside an out dir: one entry each, fingerprinted by stat (1 GB of node_modules is not re-hashed)
def sha(p):
    if os.path.islink(p): return 'symlink:' + os.readlink(p)  # links in the out dir are recorded by target, never followed
    if os.path.isdir(p):
        return 'tree:' + jhash(sorted((os.path.relpath(f, p), v) for f, v in _stat_tree(p).items()))
    st_ = os.stat(p); key = (str(p), st_.st_mtime_ns, st_.st_size)
    if key not in _SHA: _SHA[key] = _sha(p)
    return _SHA[key]


def _sha(p):
    h = hashlib.sha256()
    with Path(p).open('rb') as f:
        for b in iter(lambda: f.read(1 << 20), b''): h.update(b)
    return h.hexdigest()


def jhash(x): return hashlib.sha256(json.dumps(x, sort_keys=True, ensure_ascii=False, default=str).encode()).hexdigest()
def load(p): return json.loads(Path(p).read_text())
def save(p, x): Path(p).write_text(json.dumps(x, ensure_ascii=False, indent=2, default=str) + '\n')
def rel(p):
    try: return str(Path(p).relative_to(W))
    except ValueError: return str(p)


def files_under(root):
    out = {}
    for dirpath, dirs, names in os.walk(root):
        d = Path(dirpath)
        if d == root: dirs[:] = [x for x in dirs if x not in CONTROL]
        for x in [x for x in dirs if (d / x).is_symlink() or str(d / x) in OPAQUE]:  # linked or cloned-engine dir: one entry
            dirs.remove(x); out[str((d / x).relative_to(root))] = d / x
        for n in names:
            f = d / n
            if d == root and n in CONTROL: continue
            out[str(f.relative_to(root))] = f
    return out


# ---------------------------------------------------------------- context

class Ctx:
    def __init__(self, channel_id, spec_path, out=None):
        if not re.fullmatch(r'[a-z0-9_-]+', channel_id or ''): raise Refusal(f'--channel {channel_id!r} must match ^[a-z0-9_-]+$')
        cdir = CHANNELS / channel_id
        if cdir.is_symlink() or cdir.resolve().parent != CHANNELS.resolve(): raise Refusal(f'--channel {channel_id!r} is not a directory under {CHANNELS}')
        if not (cdir / 'channel.json').is_file(): raise Refusal(f'unknown channel {channel_id!r}: {cdir}/channel.json missing')
        self.channel = load(cdir / 'channel.json')
        if self.channel.get('id') != channel_id: raise Refusal(f'channel pack id {self.channel.get("id")!r} != directory {channel_id!r}')
        self.spec_path = Path(spec_path).resolve(); self.spec = load(self.spec_path)
        if self.spec.get('channel') != channel_id:
            raise Refusal(f'wrong target: episode spec belongs to channel {self.spec.get("channel")!r}, not {channel_id!r}')
        if not re.fullmatch(r'[A-Za-z0-9_\-]+', self.spec.get('id', '')): raise Refusal('episode spec needs an id [A-Za-z0-9_-]')
        fmt = self.spec.get('format')
        if fmt not in self.channel['formats']: raise Refusal(f'format {fmt!r} not in channel formats {list(self.channel["formats"])}')
        self.format = fmt
        self.out = canonical_out(channel_id, self.spec['id'], out)
        self.stages = STAGES[fmt]
        if fmt == 'long':
            OPAQUE.update(str(self.out / 'root' / e) for e in self.spec.get('engine', []) if (W / e).is_dir())

    @property
    def records(self): return self.out / 'stages'
    def record(self, name):
        f = self.records / f'{name}.json'
        return load(f) if f.exists() else None


def canonical_out(channel_id, episode_id, out=None):
    """The only output dir is OUT_ROOT/<channel>/<episode>; no other path, no symlink anywhere on the way."""
    root = Path(os.path.abspath(OUT_ROOT)); want = root / channel_id / episode_id
    if out is not None and Path(os.path.abspath(out)) != want:
        raise Refusal(f'--out {out} must be exactly {want}')
    for p in (want, want.parent, root):
        if p.is_symlink(): raise Refusal(f'output path component {p} is a symlink')
    if want.exists() and want.resolve() != Path(os.path.realpath(root)) / channel_id / episode_id:
        raise Refusal(f'output dir {want} resolves elsewhere ({want.resolve()})')
    return want


def pid_alive(pid):
    try: os.kill(int(pid), 0)
    except ProcessLookupError: return False
    except (PermissionError, ValueError, TypeError): return True
    return True


def pgid_alive(pgid):
    try: os.killpg(int(pgid), 0)
    except ProcessLookupError: return False
    except PermissionError: return pid_alive(pgid)  # macOS: EPERM for a group whose leader was reaped
    except (ValueError, TypeError): return True
    return True


def lock_children(ctx, add=None, drop=None):
    f = ctx.out / '.lock'; info = load(f)
    kids = [k for k in info.get('children', []) if k != drop] + ([add] if add else [])
    save(f, dict(info, children=kids))


def claim_dir(ctx, break_stale=False):
    """run.json binds the dir to one channel/episode; a lock file keeps one writer."""
    ctx.out.mkdir(parents=True, exist_ok=True)
    run = ctx.out / 'run.json'
    ident = dict(channel=ctx.channel['id'], episode=ctx.spec['id'], format=ctx.format, spec=rel(ctx.spec_path))
    if run.exists():
        prior = load(run)
        if {k: prior.get(k) for k in ident} != ident:
            raise Refusal(f'wrong target: {ctx.out} already holds {prior.get("channel")}/{prior.get("episode")} ({prior.get("spec")})')
    elif os.listdir(ctx.out):
        raise Refusal(f'wrong target: {ctx.out} has files but no run.json; it was not created by make.py for this episode')
    lock = ctx.out / '.lock'
    for attempt in (0, 1):
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY); break
        except FileExistsError:
            try: info = json.loads(lock.read_text())
            except ValueError: info = {}
            pid = info.get('pid'); kids = [k for k in info.get('children', []) if pgid_alive(k)]
            if pid is None or pid_alive(pid):
                raise Refusal(f'another writer holds {lock} (pid {pid}, alive or unknown)')
            if kids:
                raise Refusal(f'stale lock {lock}: pid {pid} is gone but its child process group(s) {kids} still run; stop them first')
            if not break_stale or attempt:
                raise Refusal(f'stale lock {lock}: pid {pid} is not running; check its outputs, then re-run with --break-stale-lock')
            print(f'  breaking stale lock of dead pid {pid}', flush=True); lock.unlink()
    os.write(fd, json.dumps(dict(pid=os.getpid(), started=time.time())).encode()); os.close(fd)
    try:
        reconcile(ctx)
    except Refusal:
        lock.unlink(missing_ok=True); raise
    if not run.exists():  # only after the path, ownership and reconcile checks passed
        save(run, dict(ident, created=time.strftime('%Y-%m-%dT%H:%M:%S%z'), files=[]))
    return lock


def manifest(ctx):
    f = ctx.out / 'run.json'
    return set(load(f).get('files', [])) if f.exists() else set()
def add_manifest(ctx, files):
    run = load(ctx.out / 'run.json'); run['files'] = sorted(set(run.get('files', [])) | set(files)); save(ctx.out / 'run.json', run)
def drop_manifest(ctx, files):
    run = load(ctx.out / 'run.json'); run['files'] = sorted(set(run.get('files', [])) - set(files)); save(ctx.out / 'run.json', run)


def reconcile(ctx):
    """Under the lock: files a crashed stage left (not in its `before` list) join this episode's manifest;
    any other file in the dir that this episode's runs did not create is refused, never moved."""
    if ctx.records.exists():
        for f in ctx.records.glob('*.json'):
            r = load(f)
            if r.get('status') == 'running':
                left = sorted(set(files_under(ctx.out)) - set(r.get('before', [])))
                add_manifest(ctx, left); save(f, dict(r, status='failed', reason='interrupted run', outputs={}))
    unknown = sorted(set(files_under(ctx.out)) - manifest(ctx))
    if unknown:
        raise Refusal(f'{ctx.out} holds files this episode\'s runs did not create: {unknown[:5]}; move them out by hand')


# ---------------------------------------------------------------- stage engine

def input_hash(ctx, st):
    deps = {}
    for d in st['deps']:
        r = ctx.record(d)
        deps[d] = r and r.get('status') == 'done' and r.get('outputs')
    cfg = {k: ctx.channel.get(k) for k in st.get('channel_keys', [])}
    files = [MAKE, *st.get('code', []), *(st['files'](ctx) if st.get('files') else [])]
    code = {rel(f): (sha(f) if Path(f).is_file() else 'MISSING') for f in files}
    per_stage = ('commands', 'outputs', 'rewritten')  # only this stage's entry counts
    spec = {k: v for k, v in ctx.spec.items() if k not in ('notes', *per_stage)}
    spec.update({k: ctx.spec.get(k, {}).get(st['name']) for k in per_stage})
    ident = dep_identity(st['deps_identity'](ctx)) if st.get('deps_identity') else None
    return jhash(dict(stage=st['name'], channel=ctx.channel['id'], cfg=cfg, spec=spec, deps=deps, code=code, render_deps=ident))


def state(ctx, st):
    """done | stale | failed | running | manual | pending | blocked (memoised until the next stage runs)"""
    memo = ctx.__dict__.setdefault('memo', {})
    if st['name'] not in memo: memo[st['name']] = _state(ctx, st)
    return memo[st['name']]


def _state(ctx, st):
    for d in st['deps']:
        if state(ctx, STAGE[ctx.format][d])[0] != 'done': return 'blocked', f'needs {d}'
    r = ctx.record(st['name'])
    if not r: return 'pending', ''
    if r.get('channel') != ctx.channel['id']: raise Refusal(f'record {st["name"]} belongs to channel {r.get("channel")}')
    if r['status'] != 'done':
        return r['status'], r.get('reason', '')
    if st.get('deps_identity') and dep_identity(st['deps_identity'](ctx)) is None:
        return 'stale', 'installed render dependencies cannot be identified (lock, browser VERSION or binary missing); never reused'
    if r['input_hash'] != input_hash(ctx, st): return 'stale', 'inputs changed'
    for f, h in r['outputs'].items():
        p = ctx.out / f
        if not p.exists() or sha(p) != h: return 'stale', f'output changed or missing: {f}'
    return 'done', ''


def supersede(ctx, name, keep):
    """Move this episode's own stale/partial files (listed in its run.json manifest, not owned by a done
    record) to superseded/ -- never delete, never touch a file the manifest does not list."""
    owned = set(keep); listed = manifest(ctx)
    moved = []
    dest = ctx.out / 'superseded' / f'{name}-{time.strftime("%Y%m%dT%H%M%S")}-{os.getpid()}'
    for f, p in files_under(ctx.out).items():
        if f in owned or f not in listed: continue
        target = dest / f; target.parent.mkdir(parents=True, exist_ok=True); shutil.move(str(p), target); moved.append(f)
    for dirpath, dirs, names in sorted(os.walk(ctx.out), reverse=True):
        d = Path(dirpath)
        if d != ctx.out and not any(d.is_relative_to(ctx.out / c) for c in CONTROL) and not os.listdir(d): d.rmdir()
    drop_manifest(ctx, moved)
    return moved


def owned_files(ctx, upto):
    keep = []
    for st in ctx.stages:
        if st['name'] == upto: continue
        r = ctx.record(st['name'])
        if r and r.get('status') == 'done': keep += list(r['outputs'])
    return keep


def run_stage(ctx, st):
    name = st['name']
    ctx.records.mkdir(exist_ok=True)
    moved = supersede(ctx, name, owned_files(ctx, name))
    if moved: print(f'  superseded {len(moved)} stale/partial file(s) -> superseded/', flush=True)
    ih = input_hash(ctx, st)
    base = dict(stage=name, channel=ctx.channel['id'], episode=ctx.spec['id'], input_hash=ih, started=time.time())
    before = {f: sha(p) for f, p in files_under(ctx.out).items()}
    save(ctx.records / f'{name}.json', dict(base, status='running', before=sorted(before)))
    def produced():
        outs = {f: sha(p) for f, p in files_under(ctx.out).items() if before.get(f) != sha(p)}
        add_manifest(ctx, outs); return outs
    guard = guard_snapshot(ctx) if ctx.format == 'long' else None
    try:
        info = st['fn'](ctx) or {}
        if guard is not None: guard_check(ctx, guard)
        if os.environ.get('FACTORY_FAIL_AT') == name: raise StageFail('injected failure (FACTORY_FAIL_AT)')
    except Manual as m:
        if guard is not None: guard_check(ctx, guard)
        save(ctx.records / f'{name}.json', dict(base, status='manual', next_owner=m.owner, needs=m.needs, reason=m.reason, outputs=produced()))
        return 'manual', f'waiting for {m.owner}: {m.reason}; needs {m.needs}'
    except (StageFail, subprocess.CalledProcessError, OSError, ValueError, RuntimeError, KeyError) as e:
        import traceback
        save(ctx.records / f'{name}.json', dict(base, status='failed', reason=f'{type(e).__name__}: {e}', traceback=traceback.format_exc()[-3000:], outputs=produced()))
        return 'failed', f'{type(e).__name__}: {e}'
    outs = produced()
    save(ctx.records / f'{name}.json', dict(base, status='done', outputs=outs,
                                            info=info, finished=time.time()))
    return 'done', f'{len(outs)} output(s)'


# ---------------------------------------------------------------- shared helpers

def episode_entry(ctx):
    """The channel's registry entry for this spec (Shorts: episodes_n16.EPISODES)."""
    reg = W / ctx.channel['sources']['episode_registry']
    if ctx.spec.get('registry', ctx.channel['sources']['episode_registry']) != ctx.channel['sources']['episode_registry']:
        raise Refusal(f'wrong target: spec registry {ctx.spec.get("registry")} is not this channel\'s {rel(reg)}')
    sys.path.insert(0, str(reg.parent))
    mod = __import__(reg.stem)
    qid = ctx.spec['source_id']
    if qid not in mod.EPISODES: raise StageFail(f'{qid} not in {rel(reg)}')
    return json.loads(json.dumps(copy.deepcopy(mod.EPISODES[qid])))


def source_files(ctx, ep):
    pat = ctx.channel['sources']['research_archive_glob']
    rows = []
    for sid in ep.get('sources', []):
        hits = sorted(W.glob(pat.format(sid=sid)))
        if len(hits) != 1: raise StageFail(f'archived source {sid}: expected 1 file for {pat}, found {len(hits)}')
        text = hits[0].read_text(errors='replace')
        m = re.search(r'^URL:\s*(https?://\S+)', text, re.M)  # the line factory/fresh.py metadata cites
        pub = re.search(r'^Publisher:\s*(.+)$', text, re.M)
        orig = m or re.search(r'^Original-URL:\s*(https?://\S+)', text, re.M)
        host = re.sub(r'^www\.|^m\.', '', re.match(r'https?://([^/]+)', orig[1])[1]) if orig else None
        rows.append(dict(id=sid, file=rel(hits[0]), sha256=sha(hits[0]), url=m[1] if m else None,
                         publisher=pub[1].strip() if pub else host))
    return rows


def red_line_hits(ctx, text):
    return sorted(set(re.findall(ctx.channel['red_lines']['topics_regex'], text)))


def caption_rows(ctx, ep, line, sid, first):
    """Caption text for one narration line, under the channel subtitle rules."""
    from factory.lib import captions as C
    rule = ctx.channel['subtitle'][ctx.format]
    if rule['splitter'] == 'authored':
        rows = ep.get('split', {}).get(sid)
        if rows is None:  # same fallback as factory/fresh.py: the shared S001 chunker
            import importlib.util
            spec = importlib.util.spec_from_file_location('shared_layout', W / 'episodes/S001/layout.py')
            layout = importlib.util.module_from_spec(spec); spec.loader.exec_module(layout)
            rows = layout.chunks(line)
        rows = list(rows)
        if first and ep.get('hook', {}).get('ask'): rows.append(ep['hook']['ask'])
        return rows
    def auto(text):
        toks = [dict(text=t) for t in text.split()]
        return ['\n'.join(' '.join(t['text'] for t in ln) for ln in C.wrap(g, rule['line_max'])) for g in C.split_long(toks, rule['line_max'])]
    return auto(line) + (auto(ep['hook']['ask']) if first and ep.get('hook', {}).get('ask') else [])


def caption_lint(ctx, rows):
    from factory.lib import captions as C
    rule = ctx.channel['subtitle'][ctx.format]
    cues = [dict(text=r, lines=r.split('\n')) for r in rows]
    issues = C.lint(cues, rule['line_max'])
    issues += [dict(cue=k, code='over_max_lines', text=c['text']) for k, c in enumerate(cues) if len(c['lines']) > rule['max_lines']]
    return issues


# ---------------------------------------------------------------- Shorts stages

def s_spec(ctx):
    ep = episode_entry(ctx)
    n = ctx.spec.get('number')
    if not isinstance(n, int) or n < 1: raise StageFail('spec.number must be a positive episode number')
    narration = ' '.join(t for c in ep['cues'] for t in c[2]) + ' ' + ep['hook']['narration']
    hits = red_line_hits(ctx, narration + ' ' + json.dumps(ep, ensure_ascii=False))
    if hits: raise StageFail(f'channel red line in narration/labels: {hits}')
    q = ctx.channel['formats']['short']['quiz']
    if ep.get('choices', q['choices']) != q['choices']: raise StageFail(f'choices {ep.get("choices")} differ from channel quiz {q["choices"]}')
    save(ctx.out / 'spec.json', dict(channel=ctx.channel['id'], spec=ctx.spec, episode=ep))


def s_facts(ctx):
    ep = load(ctx.out / 'spec.json')['episode']
    rows = source_files(ctx, ep)
    pubs = sorted({r['publisher'] for r in rows if r['publisher']})
    need = ctx.channel['facts']['min_sources']
    if len(pubs) < need: raise StageFail(f'facts need >= {need} independent archived publishers, have {pubs}')
    save(ctx.out / 'facts.json', dict(sources=rows, publishers=pubs, signoff='pending: CTO fact sign-off in the review stage'))


def s_script(ctx):
    sys.path.insert(0, str(HERE))
    from fresh import lexicon
    ep = load(ctx.out / 'spec.json')['episode']
    lex = lexicon(ep); lines = []; rows_all = []
    for cid, scene, texts, claims, pad, props in ep['cues']:
        for k, line in enumerate(texts, 1):
            sid = f'{cid}_{k}'; first = not lines
            text = ep['hook']['narration'] + ' ' + ep['hook'].get('ask', ctx.channel['formats']['short']['quiz']['ask']) if first else line
            spoken = text
            for a, b in lex: spoken = spoken.replace(a, b)
            rows = caption_rows(ctx, ep, line, sid, first)
            lines.append(dict(id=sid, cue=cid, scene=scene, text=text, tts_text=spoken, syllables=len(re.findall('[가-힣]', spoken)),
                              unmapped=re.findall('[0-9A-Za-z]+', spoken), captions=rows))
            rows_all += rows
    issues = caption_lint(ctx, rows_all)
    out = dict(voice=ctx.channel['voice'], subtitle=ctx.channel['subtitle'][ctx.format], lines=lines, caption_lint=issues)
    save(ctx.out / 'script.json', out)
    if issues: raise StageFail(f'caption rules (line_max {out["subtitle"]["line_max"]}): {issues[:3]}')
    return dict(lines=len(lines), unmapped=[l['id'] for l in lines if l['unmapped']])


def s_storyboard(ctx):
    ep = load(ctx.out / 'spec.json')['episode']
    cues = [dict(id=c[0], scene=c[1], set=c[5].get('set'), claims=c[3], narration=c[2]) for c in ep['cues']]
    empty = [c['id'] for c in cues if c['scene'] == 'incident' and not c['set']]
    if empty: raise StageFail(f'incident cues without a set illustration: {empty}')
    save(ctx.out / 'storyboard.json', dict(cues=cues, note='Shorts storyboard = registry cue sheet; composition is the v52 Quiz engine'))


def s_tts(ctx):
    """Wraps short.prepare: deterministic cached v52 narration, or local Supertonic for a fresh episode."""
    sys.path.insert(0, str(HERE))
    import short
    v = ctx.channel['voice']; q = ctx.spec['source_id']
    save(ctx.out / 'tts_request.json', dict(engine=v['engine'], voice=v['id'], local_only=v['local_only'], lines=[l['tts_text'] for l in load(ctx.out / 'script.json')['lines']]))
    base = W / 'episodes/quiz' / q
    cached = any((base / f'v52/{n}').exists() for n in ['render_final_aligned.json', 'render_final.json', 'render.json'])
    if cached:
        prior = load(base / 'v52/audio.json').get('voice')
        if prior != v['id']:
            raise StageFail(f'wrong target: cached narration for {q} is voice {prior}, channel {ctx.channel["id"]} voice is {v["id"]}; refusing to mix voices')
    elif (v['engine'], v['id']) != ('supertonic-3', 'M1'):
        raise Manual('CTO', ['a synthesis path for this voice'], f'fresh synthesis (factory/fresh.py) is wired only for supertonic-3 M1, not {v["engine"]} {v["id"]}')
    cfg = short.prepare(ctx.out, q, ctx.spec['number'], False, ctx.spec.get('video_id'), ctx.spec.get('dry_number', True))
    audio = load(ctx.out / 'audio.json')
    if audio.get('voice') != v['id']: raise StageFail(f'prepared narration voice {audio.get("voice")} != channel voice {v["id"]}')
    os.replace(ctx.out / 'render.json', ctx.out / 'render.prep.json')
    return dict(from_scratch=cfg['from_scratch'], voice=audio.get('voice'), synthesized=cfg['hook_regenerated'])


def s_captions(ctx):
    from factory.lib import captions as C
    doc = load(ctx.out / 'render.prep.json'); rule = ctx.channel['subtitle']['short']
    script_rows = [r for l in load(ctx.out / 'script.json')['lines'] for r in l['captions']]
    if rule['splitter'] == 'authored':
        got = [s['text'] for s in doc['subtitles']]
        if got != script_rows: raise StageFail(f'prepared subtitles differ from authored script captions: {got[:2]} vs {script_rows[:2]}')
        mode = 'authored rows, ASR-timed by the existing v52 alignment'
    else:
        asr = Path(load(ctx.out / 'recipe.json')['source']).parent / 'asr_master.json'
        if not asr.exists(): raise StageFail(f'auto caption split needs word timings: {asr}')
        doc['subtitles'] = C.shorts_from_subtitles(doc['subtitles'], C.load_words(str(asr)), C.silences_from_audio(str(ctx.out / 'mix_master.wav')), line_max=rule['line_max'])
        mode = 'factory/lib/captions.py shorts_from_subtitles'
    issues = caption_lint(ctx, [s['text'] for s in doc['subtitles']])
    save(ctx.out / 'captions.json', dict(mode=mode, rule=rule, rows=doc['subtitles'], lint=issues))
    if issues: raise StageFail(f'caption lint: {issues[:3]}')
    save(ctx.out / 'render.json', doc)


def s_meta(ctx):
    t = ctx.channel['templates']; ep = load(ctx.out / 'spec.json')['episode']; src = load(ctx.out / 'facts.json')['sources']
    title = ep.get('title') or ' '.join(ep['hook']['lines'])
    title_line = t['short_title'].format(title=title)
    desc = t['short_description'].format(description=' '.join(x for c in ep['cues'] if c[1] == 'incident' for x in c[2]), source_line=ep['source'],
                                          source_urls=' · '.join(f'{s["id"]}: {s["url"] or s["file"]}' for s in src))
    text = t['meta_layout'].format(title_line=title_line, description_block=desc, pinned_comment=t['pinned_comment'])
    r = t['title_rules']; bad = []
    if len(title_line) > r['max_chars']: bad.append(f'{len(title_line)} > {r["max_chars"]} chars')
    if not title_line.endswith(r['must_end_with']): bad.append(f'must end with {r["must_end_with"]}')
    if re.search(r['forbidden_regex'], title_line): bad.append('forbidden title pattern')
    if red_line_hits(ctx, text): bad.append(f'red line in metadata {red_line_hits(ctx, text)}')
    (ctx.out / 'meta.txt').write_text(text)
    if bad: raise StageFail(f'title rules: {bad}')
    return dict(title=title_line)


def s_render(ctx):
    cfg = load(ctx.out / 'recipe.json'); p = ctx.out
    if cfg.get('dry_number'): (p / 'TEST_ARTIFACT').write_text('factory/make.py rebuild; not for upload; no ledger writes.\n')
    with (p / 'render.log').open('w') as f:
        subprocess.run(['node', str(HERE / 'render.cjs'), str(p)], stdout=f, stderr=subprocess.STDOUT, check=True, cwd=W)
    subprocess.run(['ffmpeg', '-v', 'error', '-n', '-i', str(p / 'video_muted.mp4'), '-i', cfg['aac'], '-map', '0:v:0', '-map', '1:a:0',
                    '-c', 'copy', '-movflags', '+faststart', str(p / 'video.mp4')], check=True, cwd=W)


def s_gates(ctx):
    sys.path.insert(0, str(HERE))
    from gates import evaluate
    from review_gates import OPERATIONS, LIMIT
    p = ctx.out
    report = evaluate(p)
    report.setdefault('limits', [])
    if LIMIT not in report['limits']: report['limits'].append(LIMIT)
    save(p / 'qa.json', report)
    g = report['gates']
    hard = {k: v for k, v in g.items() if v['status'] == 'FAIL' and v.get('review_state') == 'DECIDED' and not v.get('advisory') and k not in OPERATIONS}
    pend = sorted(k for k, v in g.items() if v['status'] in ('NEEDS_REVIEW', 'INPUT_MISSING') and not v.get('advisory'))
    if hard:
        reasons = {k: (json.dumps(v.get('evidence'), ensure_ascii=False, default=str)[:160]) for k, v in hard.items()}
        raise StageFail(f'{len(hard)} automatic gate FAIL(s): {reasons}')
    return dict(pending_review=pend, operational=sorted(OPERATIONS & set(g)), counts={s: sum(1 for v in g.values() if v['status'] == s) for s in {v['status'] for v in g.values()}})


def s_review(ctx):
    """Human boundary: CTO facts + gate sign-offs, then CEO visual PASS, then owner viewing."""
    sys.path.insert(0, str(HERE))
    from gates import apply_cto_signoffs
    from review_gates import OPERATIONS
    p = ctx.out; sd = p / 'signoffs'; qa = load(p / 'qa.json'); video = sha(p / 'video.mp4')
    facts_sha = load(ctx.records / 'facts.json')['outputs']['facts.json']
    def ok(name, role, key, value):
        f = sd / name
        if not f.exists(): return False
        s = load(f); return s.get('role') == role and s.get('verdict') == 'PASS' and s.get(key) == value and s.get('name')
    needs = []
    if not ok('facts.json', 'CTO', 'facts_sha256', facts_sha):
        raise Manual('CTO', [f'signoffs/facts.json {{role:CTO,name,verdict:PASS,facts_sha256:{facts_sha[:12]}..}}'], 'fact sign-off (>=2 sources, 구형/선고, red lines)')
    cto = load(sd / 'cto.json') if (sd / 'cto.json').exists() else {}
    g = apply_cto_signoffs(copy.deepcopy(qa['gates']), qa['input_sha256'], cto)
    open_items = sorted(k for k, v in g.items() if k not in OPERATIONS and not v.get('advisory') and v['status'] != 'PASS')
    if open_items:
        raise Manual('CTO', [f'signoffs/cto.json {{<gate>: {{role:CTO,name,reason,input_sha256:{qa["input_sha256"][:12]}..}}}}'], f'unsigned/unresolved gates: {open_items}')
    if not ok('ceo.json', 'CEO', 'video_sha256', video):
        raise Manual('CEO', [f'signoffs/ceo.json {{role:CEO,name,verdict:PASS,video_sha256:{video[:12]}..}}'], 'CEO visual review (F3)')
    if not ok('owner.json', 'owner', 'video_sha256', video):
        raise Manual('owner', [f'signoffs/owner.json {{role:owner,name,verdict:PASS,video_sha256:{video[:12]}..}}'], 'owner viewing')
    save(p / 'review.json', dict(video_sha256=video, gates_signed=True))


def s_package(ctx):
    p = ctx.out; d = p / 'package'; d.mkdir()
    names = ['video.mp4', 'cover.jpg', 'meta.txt', 'qa.json', 'review.json', 'review_sheet.jpg']
    for n in names: shutil.copyfile(p / n, d / n)
    (d / 'SHA256').write_text(''.join(f'{sha(d / n)}  {n}\n' for n in names))
    (d / 'UPLOAD_APPROVAL_REQUIRED').write_text('make.py never uploads. Upload only after approval, per factory/upload_precheck.md.\n')


def s_upload(ctx):
    u = ctx.channel['upload']
    raise Manual('owner -> CTO', [f'upload approval for {rel(ctx.out / "package")}', f'G1 cadence: {u["cadence"]}', f'precheck {u["precheck"]}',
                                  f'ledger {u["ledger"]} entry + Studio readback', u['after_replace']],
                 'upload and readback are outside the factory approval boundary')


# ---------------------------------------------------------------- long-form: one preserved build, run as an isolated copy

def l_root(ctx): return ctx.out / 'root'
def l_build(ctx): return l_root(ctx) / ctx.spec['build']


GUARD_WIDE = ['production/lf_toon/src', 'production/compositor', 'factory']  # watched whole; changes outside our inputs are reported


def _stat_tree(p):
    p = Path(p); out = {}
    if p.is_file(): return {str(p): (p.stat().st_mtime_ns, p.stat().st_size)}
    for dirpath, dirs, names in os.walk(p):
        for n in names:
            f = os.path.join(dirpath, n)
            try: st_ = os.lstat(f); out[f] = (st_.st_mtime_ns, st_.st_size)
            except FileNotFoundError: pass
    return out


def guard_snapshot(ctx):
    """Before a long-form stage: content hashes of the original build; stat of the engine/compositor/factory trees and never_touch builds."""
    b = W / ctx.spec['build']
    return dict(build={str(f): sha(f) for f in sorted(b.rglob('*')) if f.is_file()},
                wide={r: _stat_tree(W / r) for r in [*GUARD_WIDE, *ctx.spec.get('never_touch', [])]})


def _diff(a, b): return sorted(k for k in set(a) | set(b) if a.get(k) != b.get(k))


def guard_check(ctx, before):
    """FAIL if the original build or one of this episode's own inputs (spec.engine) changed during the stage;
    any other change under the watched trees is another agent's: reported as 'foreign changes during run'."""
    after = guard_snapshot(ctx)
    changed = _diff(before['build'], after['build'])
    if changed: raise StageFail(f'original build {ctx.spec["build"]} changed during the stage: {[rel(c) for c in changed[:5]]}')
    ours = [str(W / e) for e in ctx.spec['engine']]
    for r in before['wide']:
        d = _diff(before['wide'][r], after['wide'][r])
        hit = [rel(c) for c in d if any(c == o or c.startswith(o + '/') for o in ours)]
        if hit: raise StageFail(f'an input of this episode changed during the stage (re-run): {hit[:5]}')
        if d: print(f'  WARNING foreign changes during run: {len(d)} file(s) in {r}, e.g. {rel(d[0])} (not an input of this episode)', flush=True)


def drift(ctx):
    """Copied inputs newer than the delivered original's render: that render used other sources."""
    d = W / ctx.spec['delivered']
    if not d.is_file(): return [f'delivered original missing: {ctx.spec["delivered"]}']
    names = [*ctx.spec['copy'], *[n for v in ctx.spec.get('rewritten', {}).values() for n in v]]
    return [n for n in names if (W / ctx.spec['build'] / n).is_file() and (W / ctx.spec['build'] / n).stat().st_mtime > d.stat().st_mtime]


def _clone(src, dst):
    """APFS clone (copy-on-write): an independent copy; writes to it never reach the original."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    r = subprocess.run(['cp', '-cRp', str(src), str(dst)], capture_output=True)
    if r.returncode: shutil.copytree(src, dst, symlinks=True) if src.is_dir() else shutil.copy2(src, dst)


def l_inputs(ctx):
    """Clone the build's code/data into root/<build> (a W-shaped tree) and clone the engine and data inputs
    beside it. No links: the build's scripts compute the workspace from their own location (../../../..)
    and run unmodified, with every read and write inside this episode's out dir."""
    s = ctx.spec; src = W / s['build']; nv = s.get('narration', {}).get('voice')
    if nv != ctx.channel['voice']['id']: raise Refusal(f'wrong target: build narration voice {nv} != channel voice {ctx.channel["voice"]["id"]}')
    if not src.is_dir() or not src.is_relative_to(W / 'production/lf_toon'): raise StageFail(f'build {src} missing or outside production/lf_toon')
    for bad in s.get('never_touch', []):
        if src == W / bad or src.is_relative_to(W / bad): raise Refusal(f'build {src} is a protected in-progress build ({bad})')
    dst = l_build(ctx); dst.mkdir(parents=True, exist_ok=True)  # later stages' kept outputs may live here
    for name in s['copy']:
        f = src / name
        if not f.is_file(): raise StageFail(f'build input missing: {f}')
        (dst / name).parent.mkdir(parents=True, exist_ok=True); shutil.copy2(f, dst / name)
    for item in s['engine']:
        target = W / item; here = l_root(ctx) / item
        if not target.exists(): raise StageFail(f'engine/data input missing: {target}')
        if os.path.lexists(here): raise StageFail(f'{here} already exists')
        _clone(target, here)
    rewrites = {}
    for name, (old, new) in s.get('path_rewrites', {}).items():  # a copied file that hard-codes its own install path
        f = l_root(ctx) / name; text = f.read_text(); n = text.count(old)
        if not n: raise StageFail(f'path rewrite: {old!r} not found in {name}')
        f.write_text(text.replace(old, new.replace('{root}', str(l_root(ctx))))); rewrites[name] = n
    code = [f for e in s['engine'] for f in ([l_root(ctx) / e] if (l_root(ctx) / e).is_file() else _tree(l_root(ctx) / e, CODE_EXT | {'.py', '.sh'}))
            if f.suffix != '.json']
    escapes = [rel(f) for f in code if str(W) + '/' in f.read_text(errors='replace').replace(str(l_root(ctx)), '')]
    links = [str(p) for p in l_root(ctx).rglob('*') if p.is_symlink() and not Path(os.path.realpath(p)).is_relative_to(l_root(ctx).resolve())]
    save(ctx.out / 'inputs.json', dict(build=s['build'], copied={n: sha(src / n) for n in s['copy']}, engine=s['engine'], path_rewrites=rewrites,
                                       drift=drift(ctx), outward_links=links, absolute_paths_left=escapes))
    if links: raise StageFail(f'copied inputs contain links pointing outside root/: {links[:5]}')
    if escapes: raise StageFail(f'copied engine code still names the real workspace (add a path_rewrite): {escapes[:5]}')


def l_facts(ctx):
    f = W / ctx.spec['facts']
    if not f.is_file(): raise StageFail(f'fact table missing: {f}')
    save(ctx.out / 'facts.json', dict(file=rel(f), sha256=sha(f), signoff='pending: CTO fact sign-off in review'))


def l_tts(ctx):
    """Narration. This build has no synthesis call: it reuses the delivered M1 track (spec.narration.source).
    The extraction is the build's own ffmpeg command and is cached by input hash like any stage."""
    n = ctx.spec['narration']
    if n.get('synthesize'):
        raise Manual('CTO', ['a synthesis command for this build'], 'this build has no synthesis step of its own')
    out = l_build(ctx) / n['output']
    subprocess.run(['ffmpeg', '-v', 'error', '-n', '-i', str(W / n['source']), '-map', '0:a:0', '-ac', '1', '-ar', '16000', str(out)], check=True)


def l_cmd(stage):
    def fn(ctx):
        cmd = ctx.spec['commands'][stage]
        argv = [str(PYTHON) if a == '{python}' else a for a in cmd]
        for name in ctx.spec.get('rewritten', {}).get(stage, []):  # inputs this command rewrites in place: fresh copy each run
            shutil.copy2(W / ctx.spec['build'] / name, l_build(ctx) / name)
        fail = os.environ.get('FACTORY_FAIL_AT', '')
        with (ctx.out / f'{stage}.log').open('w') as f:
            p = subprocess.Popen(argv, cwd=l_build(ctx), stdout=f, stderr=subprocess.STDOUT, start_new_session=True,
                                 env=dict(os.environ, PYTHONDONTWRITEBYTECODE='1'))
            lock_children(ctx, add=p.pid)  # its own process group (pgid == pid), recorded in the lock
            try:
                if fail.startswith(stage + ':'):  # mid-stage failure injection for tests: kill after N seconds
                    try: p.wait(timeout=float(fail.split(':')[1]))
                    except subprocess.TimeoutExpired:
                        kill_group(p.pid); p.wait(); raise StageFail(f'injected mid-stage failure: killed {stage} after {fail.split(":")[1]} s')
                rc = p.wait()
            except BaseException:
                kill_group(p.pid); raise
            finally:
                if p.poll() is None: kill_group(p.pid)
                lock_children(ctx, drop=p.pid)
        if rc: raise StageFail(f'{stage} exited {rc}; see {stage}.log')
        missing = [o for o in ctx.spec.get('outputs', {}).get(stage, []) if not (l_root(ctx) / o).is_file()]
        if missing: raise StageFail(f'{stage} did not produce {missing}')
    return fn


def kill_group(pgid):
    import signal
    try: os.killpg(pgid, signal.SIGKILL)
    except (ProcessLookupError, PermissionError): pass  # group already gone (macOS reports EPERM for a reaped group)


def l_manual(what, owner, needs):
    def fn(ctx): raise Manual(owner, needs, what)
    return fn


# ---------------------------------------------------------------- stage tables

CODE_EXT = {'.ts', '.tsx', '.js', '.cjs', '.mjs', '.json', '.css'}
def _st(name, fn, deps, keys=(), code=(), files=None): return dict(name=name, fn=fn, deps=list(deps), channel_keys=list(keys), code=list(code), files=files)
def _tree(d, ext=None): return sorted(f for f in Path(d).rglob('*') if f.is_file() and 'node_modules' not in f.parts and (ext is None or f.suffix in ext))
def _ep(ctx):
    f = ctx.out / 'spec.json'
    return load(f)['episode'] if f.is_file() else None
def _registry_files(ctx):
    reg = W / ctx.channel['sources']['episode_registry']; return [reg, *sorted(reg.parent.glob('episodes*.py'))]
def _facts_files(ctx):
    ep = _ep(ctx); pat = ctx.channel['sources']['research_archive_glob']
    return [f for sid in (ep or {}).get('sources', []) for f in sorted(W.glob(pat.format(sid=sid)))]
def _public_reads(ctx):
    """Public assets the v52 render reads: fonts, the hook hero and the narration master (as factory/short.py picks them)."""
    q = ctx.spec['source_id']; base = W / 'episodes/quiz' / q / 'v52'
    pub = W / ('episodes/quiz/v52_q013_q014_support/bundle_v52_revised/public' if q in ('q013', 'q014') else 'production/compositor/public')
    src = next((base / n for n in ['render_final_aligned.json', 'render_final.json', 'render.json'] if (base / n).exists()), None)
    audio = [pub / load(src)['audio']] if src and load(src).get('audio') else []
    return [*_tree(pub / 'fonts'), pub / 'hook_v51' / f'{"q013_clouds" if q == "q013" else q}.png', *audio]
def _tts_files(ctx):
    q = ctx.spec['source_id']
    return [*_tree(W / 'episodes/quiz' / q / 'v52'), HERE / 'prepare_v52.py', HERE / 'fresh.py', *_tree(HERE / 'vendor'), *_public_reads(ctx)]
def _render_files(ctx):
    return [*_tree(W / 'production/compositor/src', CODE_EXT), HERE / 'offline_chromium.sh', *_public_reads(ctx)]
def _long_inputs(ctx): return [W / ctx.spec['build'] / n for n in ctx.spec['copy']]
def _long_data(ctx):
    """Data inputs: engine entries that are files, plus the originals of in-place rewritten files."""
    return [*(W / r for r in ctx.spec['engine'] if (W / r).is_file()),
            *(W / ctx.spec['build'] / n for v in ctx.spec.get('rewritten', {}).values() for n in v)]
def _long_engine(ctx):
    return [*_tree(W / 'production/lf_toon/src', CODE_EXT), *_tree(W / 'production/compositor/src/v4', CODE_EXT),
            W / 'production/compositor/src/v4spike/chromium.sh', W / 'production/compositor/package.json']
def _long_render(ctx): return [*_long_inputs(ctx), *_long_engine(ctx), *_long_data(ctx)]
DEP_ROOT = W / 'production/compositor'
SHELL = 'node_modules/.remotion/chrome-headless-shell'
def dep_identity(root=None):
    """Content identity of an installed compositor: package-lock.json + every installed package.json
    (name, version, resolved, integrity; transitives and nested node_modules included) + the headless
    browser's VERSION and binary size/mtime. None (= never reuse) when the lock, VERSION or binary is missing."""
    root = Path(root or DEP_ROOT); lockf = root / 'package-lock.json'
    shell = root / SHELL; binary = shell / 'mac-arm64/chrome-headless-shell-mac-arm64/chrome-headless-shell'
    if not (lockf.is_file() and (shell / 'VERSION').is_file() and binary.is_file()): return None
    rows = []
    for dirpath, dirs, names in os.walk(root / 'node_modules'):
        d = Path(dirpath); parent = d.parent
        if 'package.json' in names and (parent.name == 'node_modules' or (parent.name.startswith('@') and parent.parent.name == 'node_modules')):
            try: pj = load(d / 'package.json')
            except ValueError: return None
            rows.append((str(d.relative_to(root)), pj.get('name'), pj.get('version'), pj.get('_resolved'), pj.get('_integrity')))
    st_ = binary.stat()
    return jhash(dict(lock=sha(lockf), packages=sorted(rows, key=str), shell=(shell / 'VERSION').read_text().strip(), binary=(st_.st_size, st_.st_mtime_ns)))
STAGES = {
    'short': [
        _st('spec', s_spec, [], ['sources', 'red_lines', 'formats'], files=_registry_files),
        _st('facts', s_facts, ['spec'], ['sources', 'facts'], files=_facts_files),
        _st('script', s_script, ['spec'], ['voice', 'subtitle'], [HERE / 'fresh.py', HERE / 'lib/captions.py', W / 'episodes/S001/tts.py', W / 'episodes/S001/layout.py', W / 'episodes/quiz/make.py']),
        _st('storyboard', s_storyboard, ['spec']),
        _st('tts', s_tts, ['script'], ['voice'], [HERE / 'short.py'], files=_tts_files),
        _st('captions', s_captions, ['script', 'tts'], ['subtitle'], [HERE / 'lib/captions.py']),
        _st('meta', s_meta, ['spec', 'facts'], ['templates', 'red_lines']),
        _st('render', s_render, ['storyboard', 'tts', 'captions'], ['art'], [HERE / 'render.cjs'], files=_render_files),
        _st('gates', s_gates, ['render', 'meta'], ['checklist'], [HERE / 'gates.py', HERE / 'review_gates.py', HERE / 'shorts_rules.py', *_tree(HERE / 'lib', {'.py'})]),
        _st('review', s_review, ['gates', 'facts'], ['review']),
        _st('package', s_package, ['review']),
        _st('upload', s_upload, ['package'], ['upload']),
    ],
    'long': [
        dict(_st('inputs', l_inputs, [], ['voice'], files=lambda c: [*_long_inputs(c), *_long_engine(c), *_long_data(c)]), deps_identity=lambda c: DEP_ROOT),
        _st('facts', l_facts, ['inputs'], ['facts'], files=lambda c: [W / c.spec['facts']]),
        _st('tts', l_tts, ['inputs'], ['voice'], files=lambda c: [W / c.spec['narration']['source']]),
        _st('captions', l_cmd('captions'), ['inputs', 'tts'], ['subtitle'], [HERE / 'lib/captions.py'], files=lambda c: [*_long_inputs(c), *_long_data(c)]),
        dict(_st('render', l_cmd('render'), ['inputs', 'captions'], ['art'], files=_long_render), deps_identity=lambda c: l_root(c) / 'production/compositor'),
        dict(_st('deliver', l_cmd('deliver'), ['inputs', 'render', 'tts'], [], files=lambda c: [*_long_inputs(c), *_long_data(c)]), deps_identity=lambda c: l_root(c) / 'production/compositor'),
        _st('gates', l_manual('long-form QA (factory/longform_qa.py) is run by the CTO on the delivered encode', 'CTO', ['qa_args for factory/longform_qa.py']), ['deliver']),
        _st('review', l_manual('long-form review', 'CTO -> CEO -> owner', ['CTO sign-offs', 'CEO visual PASS', 'owner viewing']), ['gates', 'facts']),
        _st('upload', s_upload, ['review'], ['upload']),
    ],
}
STAGE = {k: {s['name']: s for s in v} for k, v in STAGES.items()}


def _term(signum, frame): raise KeyboardInterrupt(f'signal {signum}')


def main(argv=None):
    import signal
    signal.signal(signal.SIGTERM, _term)
    a = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    a.add_argument('--channel', required=True, help='channel pack id under channels/ (no default)')
    a.add_argument('--episode', required=True, type=Path, help='episode spec JSON')
    a.add_argument('--stage', required=True, help='stage name or all')
    a.add_argument('--out', type=Path, help='must equal out/factory/<channel>/<episode> (the default); anything else is refused')
    a.add_argument('--dry-run', action='store_true', help='print the plan; write nothing')
    a.add_argument('--break-stale-lock', action='store_true', help='remove a lock whose pid is no longer running (never automatic)')
    args = a.parse_args(argv)
    if str(W) not in sys.path: sys.path.insert(0, str(W))
    try:
        ctx = Ctx(args.channel, args.episode, args.out)
        names = [s['name'] for s in ctx.stages]
        if args.stage != 'all' and args.stage not in names: raise Refusal(f'unknown stage {args.stage!r}; {ctx.format} stages: {names}')
        todo = ctx.stages if args.stage == 'all' else [STAGE[ctx.format][args.stage]]
        print(f'channel={ctx.channel["id"]} episode={ctx.spec["id"]} format={ctx.format} spec={rel(ctx.spec_path)} out={rel(ctx.out)}', flush=True)
        if ctx.format == 'long' and ctx.spec.get('delivered'):
            d = drift(ctx)
            if d: print(f'  WARNING inputs differ from delivered original ({ctx.spec["delivered"]}): {d}', flush=True)
        if args.dry_run:
            for st in ctx.stages:
                s, why = state(ctx, st) if ctx.out.exists() else (('pending' if not st['deps'] else 'blocked'), '')
                print(f'  {st["name"]:<11} {s:<8} {why}')
            return 0
        lock = claim_dir(ctx, args.break_stale_lock)
    except Refusal as e:
        print(f'REFUSED: {e}', file=sys.stderr); return 3
    code = 0
    try:
        for st in todo:
            try:
                s, why = state(ctx, st)
            except Refusal as e:
                print(f'REFUSED: {e}', file=sys.stderr); return 3
            if s == 'done':
                print(f'  {st["name"]:<11} reused   (inputs and outputs unchanged)', flush=True); continue
            if s == 'blocked':
                print(f'  {st["name"]:<11} blocked  {why}', flush=True)
                if args.stage != 'all': code = 4
                continue
            print(f'  {st["name"]:<11} running  ({s}{": " + why if why else ""})', flush=True)
            try:
                res, msg = run_stage(ctx, st); ctx.memo = {}
            except Refusal as e:
                print(f'REFUSED: {e}', file=sys.stderr); return 3
            print(f'  {st["name"]:<11} {res:<8} {msg}', flush=True)
            if res == 'failed': return 2
            if res == 'manual': code = max(code, 1)
        return code
    finally:
        lock.unlink(missing_ok=True)


if __name__ == '__main__':
    sys.exit(main())
