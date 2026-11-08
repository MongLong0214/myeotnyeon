"""factory/make.py: channel-pack separation, wrong-target refusal, output-dir scope, reuse hashes, resume.

Config-separation evidence only (a fake channel on the q017 registry entry); not production
evidence. No render, no synthesis, no network; FACTORY_OUT_ROOT points at a temp dir.
  .venv/bin/python -m unittest factory/tests/test_make.py
"""
from pathlib import Path
import copy, json, os, shutil, subprocess, sys, tempfile, unittest
W = Path(__file__).resolve().parents[2]
PY = str(W / '.venv/bin/python')
MAKE = str(W / 'factory/make.py')
REAL = json.loads((W / 'channels/myeotnyeon/channel.json').read_text())


def dead_pid():
    p = subprocess.Popen(['true']); p.wait(); return p.pid


class MakeCLI(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()); self.root = self.tmp / 'channels'; self.outroot = self.tmp / 'out'
        fake = copy.deepcopy(REAL); fake['id'] = 'fakechan'
        fake['voice']['id'] = 'M2'
        fake['templates']['short_title'] = '{title} #가짜채널'
        fake['templates']['title_rules']['must_end_with'] = '#가짜채널'
        fake['subtitle']['short'].update(line_max=10, splitter='auto', size_px=60)
        for c in (REAL, fake):
            d = self.root / c['id'] / 'episodes'; d.mkdir(parents=True)
            (d.parent / 'channel.json').write_text(json.dumps(c, ensure_ascii=False))
            for eid in ('t017', 'e2'):
                spec = dict(channel=c['id'], id=eid, format='short', registry='episodes/quiz/episodes_n16.py', source_id='q017', number=99, dry_number=True)
                (d / f'{eid}.json').write_text(json.dumps(spec))
        shutil.copytree(W / 'channels/_template', self.root / '_template')

    def tearDown(self): shutil.rmtree(self.tmp)

    def spec(self, ch, eid='t017'): return str(self.root / ch / f'episodes/{eid}.json')
    def out(self, ch, eid='t017'): return self.outroot / ch / eid

    def make(self, ch, stage, spec=None, out=None, env=None, channel_arg=True, extra=()):
        args = [PY, MAKE] + (['--channel', ch] if channel_arg else []) + ['--episode', spec or self.spec(ch), '--stage', stage]
        args += (['--out', str(out)] if out else []) + list(extra)
        p = subprocess.run(args, capture_output=True, text=True, cwd=W,
                           env=dict(os.environ, FACTORY_CHANNELS=str(self.root), FACTORY_OUT_ROOT=str(self.outroot), **(env or {})))
        return p.returncode, p.stdout + p.stderr

    def run_text_stages(self, ch):
        for s in ('spec', 'facts', 'script', 'meta'):
            code, log = self.make(ch, s); self.assertEqual(code, 0, log)

    def test_channel_config_changes_outputs(self):
        self.run_text_stages('myeotnyeon'); self.run_text_stages('fakechan')
        real, fake = [json.loads((self.out(c) / 'script.json').read_text()) for c in ('myeotnyeon', 'fakechan')]
        self.assertEqual((real['voice']['id'], fake['voice']['id']), ('M1', 'M2'))
        rows = lambda s: [r for l in s['lines'] for r in l['captions']]
        self.assertNotEqual(rows(real), rows(fake))
        self.assertTrue(all(len(line) <= 10 for r in rows(fake) for line in r.split('\n')), rows(fake))
        self.assertEqual(''.join(rows(real)).replace('\n', '').replace(' ', ''), ''.join(rows(fake)).replace('\n', '').replace(' ', ''))
        titles = [(self.out(c) / 'meta.txt').read_text().split('\n')[1] for c in ('myeotnyeon', 'fakechan')]
        self.assertTrue(titles[0].endswith('#형량퀴즈 #몇년나옴') and titles[1].endswith('#가짜채널'), titles)

    def test_extracted_pack_reproduces_existing_metadata(self):
        self.run_text_stages('myeotnyeon')
        sys.path[:0] = [str(W / 'factory'), str(W / 'episodes/quiz')]
        import fresh, short
        self.assertEqual((self.out('myeotnyeon') / 'meta.txt').read_text(), fresh.metadata(short.episode('q017')))

    def test_wrong_target_refusals(self):
        code, log = self.make('fakechan', 'spec', spec=self.spec('myeotnyeon'))
        self.assertEqual(code, 3); self.assertIn('wrong target: episode spec belongs to channel', log)
        code, log = self.make('_template', 'spec', spec=self.spec('myeotnyeon'))
        self.assertEqual(code, 3); self.assertIn('wrong target', log)
        code, log = self.make('myeotnyeon', 'spec', channel_arg=False)
        self.assertEqual(code, 2); self.assertIn('--channel', log)
        self.assertEqual(self.make('myeotnyeon', 'spec')[0], 0)
        clash = self.root / 'myeotnyeon/episodes/t017_copy.json'               # same episode id, other spec file
        clash.write_text((self.root / 'myeotnyeon/episodes/t017.json').read_text())
        code, log = self.make('myeotnyeon', 'spec', spec=str(clash))
        self.assertEqual(code, 3); self.assertIn('already holds myeotnyeon/t017', log)

    def test_out_must_be_the_episode_dir(self):
        """Reviewer case: --out at the channel root used to supersede e2/video.mp4."""
        e2 = self.out('fakechan', 'e2'); self.assertEqual(self.make('fakechan', 'spec', spec=self.spec('fakechan', 'e2'))[0], 0)
        (e2 / 'video.mp4').write_bytes(b'e2 video'); run = json.loads((e2 / 'run.json').read_text())
        run['files'].append('video.mp4'); (e2 / 'run.json').write_text(json.dumps(run))
        for bad in (self.outroot / 'fakechan', self.outroot, W, W / 'factory', self.out('myeotnyeon'), W / 'upload/pkg/x'):
            code, log = self.make('fakechan', 'spec', out=bad)
            self.assertEqual(code, 3, (bad, log)); self.assertIn('must be exactly', log)
        self.assertEqual((e2 / 'video.mp4').read_bytes(), b'e2 video')
        self.assertFalse((self.outroot / 'fakechan' / 'superseded').exists())
        self.assertEqual(self.make('fakechan', 'spec', out=self.out('fakechan'))[0], 0)      # the exact dir is accepted
        escape = self.tmp / 'elsewhere'; escape.mkdir(); (self.outroot / 'fakechan' / 'e3').symlink_to(escape)
        spec = json.loads(Path(self.spec('fakechan')).read_text()); spec['id'] = 'e3'
        (self.root / 'fakechan/episodes/e3.json').write_text(json.dumps(spec))
        code, log = self.make('fakechan', 'spec', spec=str(self.root / 'fakechan/episodes/e3.json'))
        self.assertEqual(code, 3); self.assertIn('symlink', log); self.assertEqual(list(escape.iterdir()), [])

    def test_foreign_dir_gets_no_run_json(self):
        out = self.out('fakechan'); out.mkdir(parents=True); (out / 'theirs.mp4').write_bytes(b'x')
        code, log = self.make('fakechan', 'spec')
        self.assertEqual(code, 3); self.assertIn('no run.json', log)
        self.assertEqual(sorted(p.name for p in out.iterdir()), ['theirs.mp4'])

    def test_channel_id_validated(self):
        for bad in ('../channels/fakechan', 'FakeChan', 'fake/chan', 'nochannel', ''):
            code, log = self.make(bad, 'spec')
            self.assertEqual(code, 3, (bad, log)); self.assertIn('unknown channel' if bad == 'nochannel' else 'must match', log)
        self.assertFalse(self.outroot.exists())

    def test_voice_mix_refused(self):
        for s in ('spec', 'script'): self.assertEqual(self.make('fakechan', s)[0], 0)
        code, log = self.make('fakechan', 'tts')
        self.assertEqual(code, 2); self.assertIn('voice M1, channel fakechan voice is M2; refusing to mix voices', log)
        self.assertFalse((self.out('fakechan') / 'audio.json').exists())

    def test_lock(self):
        self.assertEqual(self.make('fakechan', 'spec')[0], 0)
        lock = self.out('fakechan') / '.lock'
        lock.write_text(json.dumps(dict(pid=os.getpid())))                      # live writer: always refused
        code, log = self.make('fakechan', 'facts', extra=['--break-stale-lock'])
        self.assertEqual(code, 3); self.assertIn('another writer holds', log)
        lock.write_text(json.dumps(dict(pid=dead_pid())))                       # dead writer: reported, broken only on request
        code, log = self.make('fakechan', 'facts')
        self.assertEqual(code, 3); self.assertIn('--break-stale-lock', log); self.assertTrue(lock.exists())
        code, log = self.make('fakechan', 'facts', extra=['--break-stale-lock'])
        self.assertEqual(code, 0, log); self.assertIn('breaking stale lock', log); self.assertFalse(lock.exists())

    def test_supersede_touches_only_this_episodes_manifest(self):
        for s in ('spec', 'facts'): self.assertEqual(self.make('fakechan', s)[0], 0)
        out = self.out('fakechan')
        (out / 'stray.txt').write_text('not ours')                              # not created by this episode's runs
        code, log = self.make('fakechan', 'script')
        self.assertEqual(code, 3); self.assertIn('did not create', log)
        self.assertTrue((out / 'stray.txt').exists()); self.assertFalse((out / 'superseded').exists()); self.assertFalse((out / '.lock').exists())
        (out / 'stray.txt').unlink()
        code, log = self.make('fakechan', 'script', env=dict(FACTORY_FAIL_AT='script')); self.assertEqual(code, 2)
        self.assertEqual(self.make('fakechan', 'script')[0], 0)                  # partial script.json is ours: moved
        self.assertEqual({p.name for p in (out / 'superseded').rglob('*') if p.is_file()}, {'script.json'})
        self.assertTrue((out / 'spec.json').exists() and (out / 'facts.json').exists())

    def test_reuse_invalidation_and_resume(self):
        for s in ('spec', 'facts'): self.assertEqual(self.make('fakechan', s)[0], 0)
        code, log = self.make('fakechan', 'script', env=dict(FACTORY_FAIL_AT='script'))
        self.assertEqual(code, 2); self.assertIn('injected failure', log)
        self.assertEqual(json.loads((self.out('fakechan') / 'stages/script.json').read_text())['status'], 'failed')
        code, log = self.make('fakechan', 'all')  # resumes: reuses spec/facts, reruns script, stops at the voice refusal
        self.assertIn('spec        reused', log); self.assertIn('facts       reused', log); self.assertIn('script      done', log)
        self.assertEqual(code, 2)
        code, log = self.make('fakechan', 'meta'); self.assertEqual(code, 0, log)
        pack = json.loads((self.root / 'fakechan/channel.json').read_text()); pack['subtitle']['short']['line_max'] = 12
        (self.root / 'fakechan/channel.json').write_text(json.dumps(pack, ensure_ascii=False))
        for s, want in (('spec', 'reused'), ('facts', 'reused'), ('meta', 'reused'), ('script', 'running  (stale')):
            code, log = self.make('fakechan', s); self.assertIn(want, log, (s, log))

    def test_input_files_invalidate_the_right_stage(self):
        self.assertEqual(self.make('myeotnyeon', 'spec')[0], 0)
        os.environ.update(FACTORY_CHANNELS=str(self.root), FACTORY_OUT_ROOT=str(self.outroot))
        sys.path.insert(0, str(W)); sys.path.insert(0, str(W / 'factory'))
        import importlib, make as M
        M = importlib.reload(M)
        ctx = M.Ctx('myeotnyeon', self.spec('myeotnyeon'))
        names = [s['name'] for s in ctx.stages]
        def hashes(): return {n: M.input_hash(ctx, M.STAGE['short'][n]) for n in names}
        base = hashes(); orig = M.sha
        src = json.loads((self.out('myeotnyeon') / 'spec.json').read_text())['episode']['sources'][0]
        cases = {
            str(next(W.glob(f'research/raw*/{src}.txt'))): {'facts'},
            str(W / 'episodes/quiz/q017/v52/audio.json'): {'tts'},
            str(W / 'factory/prepare_v52.py'): {'tts'},
            str(W / 'production/compositor/src/Quiz.tsx'): {'render'},
            str(W / 'production/compositor/public/hook_v51/q017.png'): {'tts', 'render'},
            str(W / 'factory/make.py'): set(names),
        }
        try:
            for target, want in cases.items():
                self.assertTrue(Path(target).is_file(), target)
                M.sha = lambda p, t=target: 'CHANGED' if str(Path(p).resolve()) == t else orig(p)
                now = hashes()
                self.assertEqual({n for n in names if now[n] != base[n]}, want, target)
        finally:
            M.sha = orig


if __name__ == '__main__':
    unittest.main()
