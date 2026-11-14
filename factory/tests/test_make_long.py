"""make.py long-form path on the preserved N18 v4 build, without rendering.

The build's files are copied into a temp FACTORY_OUT_ROOT; stage commands are replaced by tiny
stand-ins so no render runs. Checks: originals untouched, protected builds and voice mixing
refused, mid-stage kill then resume, reuse on re-run.
  .venv/bin/python -m unittest factory/tests/test_make_long.py
"""
from pathlib import Path
import copy, hashlib, json, os, shutil, signal, subprocess, sys, tempfile, time, unittest
W = Path(__file__).resolve().parents[2]
PY = str(W / '.venv/bin/python'); MAKE = str(W / 'factory/make.py')
REAL = json.loads((W / 'channels/myeotnyeon/channel.json').read_text())
SPEC = json.loads((W / 'channels/myeotnyeon/episodes/n18_v4.json').read_text())
BUILD = W / SPEC['build']


def tree_hash(p):
    return {str(f.relative_to(p)): hashlib.sha256(f.read_bytes()).hexdigest() for f in sorted(p.rglob('*')) if f.is_file()}


class LongForm(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()); self.root = self.tmp / 'channels'; self.outroot = self.tmp / 'out'
        fake = copy.deepcopy(REAL); fake['id'] = 'fakechan'; fake['voice']['id'] = 'M2'
        for c in (REAL, fake):
            (self.root / c['id'] / 'episodes').mkdir(parents=True)
            (self.root / c['id'] / 'channel.json').write_text(json.dumps(c, ensure_ascii=False))
        spec = dict(SPEC, id='lf_t', commands=dict(
            captions=['{python}', '-c', "open('subtitles.srt','w').write('1\\n')"],
            render=['{python}', '-c', "import time; open('picture_360p.mp4','w').write('partial'); time.sleep(30)"],
            deliver=['{python}', '-c', "import pathlib; d=pathlib.Path('../../../../episodes/review_full/n18_v4/full'); d.mkdir(parents=True); (d/'full_360p.mp4').write_text('v'); (d/'av_check.json').write_text('{}')"]),
            outputs=dict(captions=['production/lf_toon/v4/n18/subtitles.srt'], render=['production/lf_toon/v4/n18/picture_360p.mp4'],
                         deliver=SPEC['outputs']['deliver']))
        self.spec = self.root / 'myeotnyeon/episodes/lf_t.json'; self.spec.write_text(json.dumps(spec))
        self.before = tree_hash(BUILD)

    def tearDown(self):
        shutil.rmtree(self.tmp)
        self.assertEqual(tree_hash(BUILD), self.before, 'original N18 v4 build changed')

    def make(self, ch, stage, spec=None, env=None):
        p = subprocess.run([PY, MAKE, '--channel', ch, '--episode', str(spec or self.spec), '--stage', stage], capture_output=True, text=True, cwd=W,
                           env=dict(os.environ, FACTORY_CHANNELS=str(self.root), FACTORY_OUT_ROOT=str(self.outroot), **(env or {})))
        return p.returncode, p.stdout + p.stderr

    def test_isolated_copy_kill_resume_reuse(self):
        out = self.outroot / 'myeotnyeon/lf_t'
        for s in ('inputs', 'facts', 'tts', 'captions'):
            code, log = self.make('myeotnyeon', s); self.assertEqual(code, 0, log)
        copy_dir = out / 'root' / SPEC['build']
        self.assertEqual((copy_dir / 'render.cjs').read_bytes(), (BUILD / 'render.cjs').read_bytes())
        self.assertFalse([p for p in (out / 'root').rglob('*') if p.is_symlink() and not os.path.realpath(p).startswith(str((out / 'root').resolve()))])
        self.assertTrue((out / 'root/production/lf_toon/src/ToonRig.tsx').is_file())
        self.assertGreater((copy_dir / 'build_audio.wav').stat().st_size, 1000)
        code, log = self.make('myeotnyeon', 'render', env=dict(FACTORY_FAIL_AT='render:1'))
        self.assertEqual(code, 2); self.assertIn('injected mid-stage failure', log)
        self.assertEqual((copy_dir / 'picture_360p.mp4').read_text(), 'partial')
        spec = json.loads(self.spec.read_text()); spec['commands']['render'] = ['{python}', '-c', "open('picture_360p.mp4','w').write('full')"]
        self.spec.write_text(json.dumps(spec))
        code, log = self.make('myeotnyeon', 'all')
        self.assertIn('inputs      reused', log); self.assertIn('tts         reused', log); self.assertIn('render      done', log); self.assertIn('deliver     done', log)
        self.assertEqual(code, 1, log)                                       # gates/review are manual: waiting, not done
        self.assertEqual((copy_dir / 'picture_360p.mp4').read_text(), 'full')
        self.assertEqual([p.read_text() for p in (out / 'superseded').rglob('picture_360p.mp4')], ['partial'])
        self.assertTrue((out / 'root/episodes/review_full/n18_v4/full/full_360p.mp4').is_file())
        code, log = self.make('myeotnyeon', 'all')
        for s in ('inputs', 'facts', 'tts', 'captions', 'render', 'deliver'): self.assertIn(f'{s:<11} reused', log)
        self.assertIn('gates       running', log); self.assertIn('waiting for CTO', log)

    def make_bg(self, ch, stage):
        return subprocess.Popen([PY, MAKE, '--channel', ch, '--episode', str(self.spec), '--stage', stage], cwd=W, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                env=dict(os.environ, FACTORY_CHANNELS=str(self.root), FACTORY_OUT_ROOT=str(self.outroot)))

    def test_write_through_copy_cannot_reach_original(self):
        engine = W / 'production/lf_toon/src/ToonRig.tsx'; before = hashlib.sha256(engine.read_bytes()).hexdigest()
        spec = json.loads(self.spec.read_text())
        spec['commands']['captions'] = ['{python}', '-c', "open('../../src/ToonRig.tsx','a').write('//x'); open('render.cjs','a').write('//x'); open('../../../../factory/lib/captions.py','a').write('#x'); open('subtitles.srt','w').write('1')"]
        self.spec.write_text(json.dumps(spec))
        for s in ('inputs', 'tts', 'captions'):
            code, log = self.make('myeotnyeon', s); self.assertEqual(code, 0, log)
        root = self.outroot / 'myeotnyeon/lf_t/root'
        self.assertTrue((root / 'production/lf_toon/src/ToonRig.tsx').read_text().endswith('//x'))
        self.assertEqual(hashlib.sha256(engine.read_bytes()).hexdigest(), before)
        self.assertFalse((W / 'factory/lib/captions.py').read_text().endswith('#x'))

    def test_guard_reports_foreign_engine_change(self):
        os.environ.update(FACTORY_CHANNELS=str(self.root), FACTORY_OUT_ROOT=str(self.outroot))
        sys.path[:0] = [str(W), str(W / 'factory')]
        import importlib, make as M
        M = importlib.reload(M); ctx = M.Ctx('myeotnyeon', str(self.spec))
        before = M.guard_snapshot(ctx); orig = M._stat_tree
        import contextlib, io
        try:
            M._stat_tree = lambda p: {**orig(p), str(p) + '/public/new.png': (1, 1)} if str(p).endswith('production/compositor') else orig(p)
            buf = io.StringIO()
            with contextlib.redirect_stdout(buf): M.guard_check(ctx, before)           # not an input: reported, not fatal
            self.assertIn('foreign changes during run', buf.getvalue())
            M._stat_tree = lambda p: {**orig(p), str(p) + '/node_modules/x.js': (1, 1)} if str(p).endswith('production/compositor') else orig(p)
            with self.assertRaises(M.StageFail) as e: M.guard_check(ctx, before)       # an input of this episode: fatal
            self.assertIn('an input of this episode changed', str(e.exception))
        finally:
            M._stat_tree = orig

    def test_tsx_or_engine_edit_reruns_render(self):
        self.assertEqual(self.make('myeotnyeon', 'inputs')[0], 0)
        os.environ.update(FACTORY_CHANNELS=str(self.root), FACTORY_OUT_ROOT=str(self.outroot))
        sys.path[:0] = [str(W), str(W / 'factory')]
        import importlib, make as M
        M = importlib.reload(M); ctx = M.Ctx('myeotnyeon', str(self.spec)); names = [s['name'] for s in ctx.stages]
        hashes = lambda: {n: M.input_hash(ctx, M.STAGE['long'][n]) for n in names}
        base = hashes(); orig = M.sha
        cases = {str(BUILD / 'Full.tsx'): {'inputs', 'render', 'deliver', 'captions'}, str(BUILD / 'render.cjs'): {'inputs', 'render', 'deliver', 'captions'},
                 str(W / 'production/lf_toon/src/ToonRig.tsx'): {'inputs', 'render'}}
        try:
            for t, want in cases.items():
                M.sha = lambda p, t=t: 'CHANGED' if str(Path(p).resolve()) == t else orig(p)
                now = hashes(); self.assertEqual({n for n in names if now[n] != base[n]}, want, t)
        finally:
            M.sha = orig

    def test_killed_make_leaves_child_recorded(self):
        for s in ('inputs', 'tts', 'captions'): self.assertEqual(self.make('myeotnyeon', s)[0], 0)
        p = self.make_bg('myeotnyeon', 'render'); lock = self.outroot / 'myeotnyeon/lf_t/.lock'
        for _ in range(100):
            if lock.exists() and json.loads(lock.read_text()).get('children'): break
            time.sleep(.1)
        child = json.loads(lock.read_text())['children'][0]
        p.kill(); p.wait()                                                   # make.py dies, render child keeps running
        r = subprocess.run([PY, MAKE, '--channel', 'myeotnyeon', '--episode', str(self.spec), '--stage', 'render', '--break-stale-lock'], capture_output=True, text=True, cwd=W,
                           env=dict(os.environ, FACTORY_CHANNELS=str(self.root), FACTORY_OUT_ROOT=str(self.outroot)))
        self.assertEqual(r.returncode, 3); self.assertIn('still run', r.stdout + r.stderr)
        os.killpg(child, signal.SIGKILL); time.sleep(.3)
        spec = json.loads(self.spec.read_text()); spec['commands']['render'] = ['{python}', '-c', "open('picture_360p.mp4','w').write('full')"]
        self.spec.write_text(json.dumps(spec))
        r = subprocess.run([PY, MAKE, '--channel', 'myeotnyeon', '--episode', str(self.spec), '--stage', 'render', '--break-stale-lock'], capture_output=True, text=True, cwd=W,
                           env=dict(os.environ, FACTORY_CHANNELS=str(self.root), FACTORY_OUT_ROOT=str(self.outroot)))
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr); self.assertIn('render      done', r.stdout)

    def test_installed_render_dependencies_key_render_and_deliver(self):
        def install(fx, versions, nested='1.0.0', version_file=True):
            nm = fx / 'node_modules'
            for n, v in versions.items():
                (nm / n).mkdir(parents=True, exist_ok=True); (nm / n / 'package.json').write_text(json.dumps(dict(name=n, version=v)))
            dep = nm / 'remotion/node_modules/tiny-dep'; dep.mkdir(parents=True, exist_ok=True)   # a transitive, nested dependency
            dep.joinpath('package.json').write_text(json.dumps(dict(name='tiny-dep', version=nested)))
            shell = nm / '.remotion/chrome-headless-shell'; b = shell / 'mac-arm64/chrome-headless-shell-mac-arm64'; b.mkdir(parents=True, exist_ok=True)
            (b / 'chrome-headless-shell').write_bytes(b'bin'); os.utime(b / 'chrome-headless-shell', ns=(1, 1))
            if version_file: (shell / 'VERSION').write_text('157')
            elif (shell / 'VERSION').exists(): (shell / 'VERSION').unlink()
            (fx / 'package.json').write_text('{"dependencies": {"remotion": "^4.0.0"}}')         # same package.json throughout
            (fx / 'package-lock.json').write_text('{"lockfileVersion": 3}')                    # same lock throughout
        pkgs = {'remotion': '4.0.538', '@remotion/renderer': '4.0.538', 'react': '18.3.1'}
        real = self.tmp / 'compositor'; install(real, pkgs)
        os.environ.update(FACTORY_CHANNELS=str(self.root), FACTORY_OUT_ROOT=str(self.outroot))
        sys.path[:0] = [str(W), str(W / 'factory')]
        import importlib, make as M
        M = importlib.reload(M); M.DEP_ROOT = real; ctx = M.Ctx('myeotnyeon', str(self.spec)); names = [s['name'] for s in ctx.stages]
        clone = M.l_root(ctx) / 'production/compositor'; install(clone, pkgs)
        hashes = lambda: {n: M.input_hash(ctx, M.STAGE['long'][n]) for n in names}
        changed = lambda a, b: {n for n in names if a[n] != b[n]}
        base = hashes(); self.assertEqual(hashes(), base)                                    # unchanged: reuse
        self.assertEqual(M.dep_identity(real), M.dep_identity(clone))
        up = dict(pkgs, **{'@remotion/renderer': '4.0.539'}); install(real, up)               # npm i --no-save in the real tree
        h1 = hashes(); self.assertEqual(changed(base, h1), {'inputs'})                        # re-clone first ...
        install(clone, up); h2 = hashes(); self.assertEqual(changed(h1, h2), {'render', 'deliver'})  # ... then the clone re-renders
        install(clone, up, nested='1.0.1'); h3 = hashes(); self.assertEqual(changed(h2, h3), {'render', 'deliver'})  # transitive change
        install(clone, up, nested='1.0.1', version_file=False); self.assertIsNone(M.dep_identity(clone))
        M.state = lambda c, st: ('done', '') if st['name'] != 'render' else M._state(c, st)
        ctx.records.mkdir(parents=True, exist_ok=True)
        (ctx.records / 'render.json').write_text(json.dumps(dict(stage='render', channel='myeotnyeon', status='done', input_hash=M.input_hash(ctx, M.STAGE['long']['render']), outputs={})))
        self.assertEqual(M._state(ctx, M.STAGE['long']['render'])[0], 'stale')              # missing browser VERSION: no reuse
        install(clone, up, nested='1.0.1')
        (ctx.records / 'render.json').write_text(json.dumps(dict(stage='render', channel='myeotnyeon', status='done', input_hash=M.input_hash(ctx, M.STAGE['long']['render']), outputs={})))
        self.assertEqual(M._state(ctx, M.STAGE['long']['render'])[0], 'done')

    def test_drift_warning(self):
        code, log = self.make('myeotnyeon', 'inputs')
        self.assertIn('inputs differ from delivered original', log)          # Fix2Stage/Rebuilt are newer than the delivered picture
        self.assertEqual(code, 0)

    def test_protected_build_refused(self):
        spec = json.loads(self.spec.read_text()); spec.update(id='lf_bad', build='production/lf_toon/lf3_heist')
        f = self.root / 'myeotnyeon/episodes/lf_bad.json'; f.write_text(json.dumps(spec))
        code, log = self.make('myeotnyeon', 'inputs', spec=f)
        self.assertEqual(code, 3); self.assertIn('protected in-progress build', log)
        self.assertFalse((self.outroot / 'myeotnyeon/lf_bad/root').exists())

    def test_voice_mix_refused(self):
        spec = json.loads(self.spec.read_text()); spec['channel'] = 'fakechan'
        f = self.root / 'fakechan/episodes/lf_t.json'; f.write_text(json.dumps(spec))
        code, log = self.make('fakechan', 'inputs', spec=f)
        self.assertEqual(code, 3); self.assertIn('build narration voice M1 != channel voice M2', log)
        self.assertFalse((self.outroot / 'fakechan/lf_t/root').exists())


if __name__ == '__main__':
    unittest.main()
