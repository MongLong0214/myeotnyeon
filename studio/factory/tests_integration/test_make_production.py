"""Integration: make.py stages that read the cached q017 production build.

Needs episodes/quiz/q017/v52/ (render.json, audio.json) and
production/compositor/public/hook_v51/q017.png from the production machine; those are
production outputs and are not in this repository. Without them these tests fail.
  .venv/bin/python -m unittest discover -s factory/tests_integration
"""
from pathlib import Path
import json, os, sys, unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tests'))
from test_make import ARCHIVE, W, MakeHarness


class MakeCLIProductionCache(MakeHarness):
    def test_voice_mix_refused(self):
        for s in ('spec', 'script'): self.assertEqual(self.make('fakechan', s)[0], 0)
        code, log = self.make('fakechan', 'tts')
        self.assertEqual(code, 2); self.assertIn('voice M1, channel fakechan voice is M2; refusing to mix voices', log)
        self.assertFalse((self.out('fakechan') / 'audio.json').exists())

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
            str(next(W.glob(ARCHIVE.format(sid=src)))): {'facts'},
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
