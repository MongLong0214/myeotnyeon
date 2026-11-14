"""Hook rules R2 (first narration sound <= 0.30 s) and R4 (ko title).
  .venv/bin/python -m unittest factory.tests.test_hook_rules"""
import json, sys, tempfile, unittest
from pathlib import Path
import numpy as np
import soundfile as sf
W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W))
from factory.shorts import core  # noqa: E402


class TitleKo(unittest.TestCase):
    def test_pass(self):
        for t in ("통장·도장으로 '14억' 빼돌린 은행원, 몇 년?", '음주 사망 사고 운전자, 몇 년 나왔을까?', '보험금 노린 아내, 형량은?'):
            self.assertEqual(core.title_rules_ko(t), [], t)

    def test_too_long(self):
        e = core.title_rules_ko('가' * 27 + ' 몇 년?')
        self.assertEqual(len(e), 1)
        self.assertIn('> 30', e[0])

    def test_ending_and_banned(self):
        self.assertTrue(any('must end' in x for x in core.title_rules_ko('은행원의 최후')))
        e = core.title_rules_ko('쟁점? 어떤 형 받은 최후, 몇 년?')
        self.assertEqual(sorted(x.split('"')[1] for x in e if 'contains' in x), sorted(['쟁점', '어떤 형', '최후']))

    def test_golden_ko_title(self):
        s = json.loads((W / 'factory/specs/golden/q044.json').read_text())
        self.assertEqual(core.title_rules_ko(s['title']), [])


class LeadSilence(unittest.TestCase):
    def wav(self, lead):
        sr = 24000
        x = np.concatenate([np.zeros(int(lead * sr)), 0.3 * np.sin(np.arange(sr) / 10)]).astype('float32')
        p = Path(tempfile.mkdtemp()) / 'n.wav'
        sf.write(p, x, sr)
        return p

    def test_measure(self):
        self.assertAlmostEqual(core.first_sound_s(self.wav(.5)), .5, delta=.01)

    def test_rule(self):
        self.assertEqual(core.lead_silence_rule(core.first_sound_s(self.wav(.1))), [])
        e = core.lead_silence_rule(core.first_sound_s(self.wav(2.0)), 'L01_t1')
        self.assertEqual(len(e), 1)
        self.assertIn('trim the lead silence', e[0])
        self.assertEqual(len(core.lead_silence_rule(None)), 1)


if __name__ == '__main__':
    unittest.main()
