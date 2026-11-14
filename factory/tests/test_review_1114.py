"""Review findings 2026-11-14 (P0 1-4, P1 5-10, P2 11-12): sentence type + unit, quotes-only numbers, sourced finality,
meta numbers, ja finality text, negated "final", unknown verdict date, stage vs case, result_first streak, R2 for every
locale, no blind take reuse.
  .venv/bin/python -m unittest factory.tests.test_review_1114"""
import copy, json, sys, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
import soundfile as sf
W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W))
from factory import make_short  # noqa: E402
from factory.shorts import core, policy  # noqa: E402

Q049 = json.loads((W / 'factory/tests/fixtures/review_1114_q049.json').read_text())
GOLD = {k: json.loads((W / f'factory/specs/golden/{k}.json').read_text()) for k in ('q044', 'en001', 'ja001')}
SQ = ['각각 금고 1년에 집행유예 2년, 사회봉사 120시간을 선고했다고 20일 밝혔다.']


def b3(spec, hist=()):
    with patch.object(core, 'history', lambda s: list(hist)):
        return core.check_b3(spec, core.fact_values(spec))[0]


class P0(unittest.TestCase):
    def test_1a_sentence_type_and_unit(self):
        ok = lambda t, q=SQ, L='ko': core.sentence_errors('x', t, q, L)  # noqa: E731
        self.assertEqual(ok('금고1년 집유2년'), [])
        self.assertEqual(ok('금고 1년, 집행유예 2년, 사회봉사 120시간'), [])
        for bad in ('징역 2년', '징역 1년', '금고 2년', '집행유예 1년', '금고 1개월'):
            self.assertTrue(ok(bad), bad)
        self.assertTrue(ok('징역 3년', ['징역 5년을 선고했다.', '3억 원을 챙겼다.']))
        self.assertEqual(ok('30 days in jail', ['sentenced to 30 days in jail and five years of probation'], 'en'), [])
        self.assertTrue(ok('5 years in jail', ['sentenced to 30 days in jail and five years of probation'], 'en'))
        self.assertTrue(ok('懲役3年', ['拘禁刑6か月の実刑判決', '3年前から'], 'ja'))
        s = copy.deepcopy(Q049)
        s['quiz']['choices'][2] = '징역 2년'
        self.assertTrue(any('quiz.answer' in e and '징역' in e for e in b3(s)))
        s = copy.deepcopy(Q049)
        s['hook'][1] = '징역 2년?'  # result_first: the hook is the outcome
        self.assertTrue(any(e.startswith('hook[1]') for e in b3(s)))
        self.assertEqual(b3(Q049), [])

    def test_1b_number_with_unit(self):
        self.assertEqual(core.nums_missing('징역 3년', '3억 원을 챙겼다', 'ko'), ['3년'])
        self.assertEqual(core.nums_missing('12번 위조, 500만', '12차례에 걸쳐 현금 500만 원', 'ko'), [])
        self.assertEqual(core.nums_missing('기준의 6배, 0.485%', '0.08%의 6배, 혈중알코올농도 0.485%', 'ko'), [])  # no unit: bare number
        self.assertEqual(core.nums_missing('2명', '2년', 'ko'), ['2명'])
        s = copy.deepcopy(Q049)
        s['lines'][-2]['shots'][0]['lines'] = ['금고 1개월', '집행유예 2년']
        self.assertTrue(any('card number' in e for e in b3(s)))

    def test_2_claim_is_not_a_number_source(self):
        s = copy.deepcopy(Q049)
        s['facts'][0]['claim'] += ' 업주는 3명이었다.'
        s['lines'][1]['text'] = '업주 3명이 건 내기였습니다.'
        self.assertTrue(any(e.startswith('lines[hook]') and '3명' in e for e in b3(s)))

    def test_3_finality_needs_a_quote(self):
        self.assertEqual(policy.finality_errors(Q049), [])
        s = copy.deepcopy(Q049)
        s['facts'][2]['quotes'] = s['facts'][2]['quotes'][:1]
        e = policy.finality_errors(s)
        self.assertTrue(e and 'case.finality' in e[0] and '항소 미확인 / appeal_unknown or add the quote' in e[0])
        s['facts'][2]['quotes'].append({'source': 'S4', 'text': '아직 형이 확정되지 않았다. 확정 전이다.'})
        self.assertTrue(policy.finality_errors(s))
        s['case']['finality'] = '항소'
        self.assertTrue(policy.finality_errors(s))
        s['facts'][2]['quotes'].append({'source': 'S4', 'text': '피고인은 항소했다.'})
        self.assertEqual(policy.finality_errors(s), [])
        for g in GOLD.values():
            self.assertEqual(policy.finality_errors(g), [], g['id'])

    def test_4_meta_numbers(self):
        self.assertEqual(policy.meta_numbers(Q049), [])
        for field, val in (('title', "'원샷하면 700만' 부추긴 업주, 몇 년?"), ('description', '업주 5명이 내기를 걸었습니다.'), ('cover', '원샷 내기\n3년 뒤')):
            s = copy.deepcopy(Q049)
            s[field] = val
            self.assertTrue(any(e.startswith(field) for e in policy.meta_numbers(s)), field)
        s = copy.deepcopy(Q049)
        s['hook'][0] = '9명이 죽었는데'
        self.assertTrue(any(e.startswith('hook[0]') for e in policy.meta_numbers(s)))
        s = copy.deepcopy(Q049)
        s['quiz']['choices'][0] = '징역 99년'  # wrong choices are exempt
        self.assertEqual(policy.meta_numbers(s), [])
        self.assertTrue(any('meta' in e or 'not in any fact quote' in e for e in policy.lint(dict(Q049, title="'원샷하면 700만' 부추긴 업주, 몇 년?"))[0]))


class P1(unittest.TestCase):
    def test_5_ja_finality_text(self):
        want = {'final': '判決は確定しました。', 'appeal_unknown': '控訴の有無は確認されていません。', 'appealed': '控訴され、判決は確定していません。', 'not_final': '判決は確定していません。'}
        for k, v in want.items():
            self.assertEqual(core.finality_text(k, 'ja'), v)
        self.assertEqual(core.finality_text('appealed', 'en'), 'The sentence has been appealed and is not final.')
        self.assertEqual(core.finality_text('확정', 'ko'), '판결은 확정됐습니다.')
        self.assertEqual(policy.lint(GOLD['ja001'])[0], [])

    def test_6_negated_final_is_not_flagged(self):
        hit = lambda L, t: bool(__import__('re').search(policy.NOT_FINAL[L], t, __import__('re').I))  # noqa: E731
        for L, t in (('en', 'The ruling is not final.'), ('en', "It isn't final."), ('en', 'It is not yet final.'), ('ko', '확정 전입니다.'), ('ko', '확정되지 않았습니다.'),
                     ('ko', '확정 안 됐습니다.'), ('ko', '미확정 판결'), ('ja', '未確定です。'), ('ja', '判決は確定していません。')):
            self.assertFalse(hit(L, t), t)
        for L, t in (('en', 'The sentence is final.'), ('en', 'The verdict was upheld.'), ('ko', '형이 확정됐다.'), ('ja', '判決が確定しました。')):
            self.assertTrue(hit(L, t), t)

    def test_7_verdict_date_unknown_or_sourced(self):
        s = copy.deepcopy(Q049)
        self.assertEqual(s['case']['verdict_date'], 'unknown')
        self.assertEqual(core.validate(s, core.SCHEMA), [])
        self.assertEqual(policy.verdict_date_errors(s), [])
        s['case']['verdict_date'] = '2026-10-20'  # the sources only say "20일 밝혔다" (report date)
        self.assertEqual(core.validate(s, core.SCHEMA), [])
        e = policy.verdict_date_errors(s, ['선고했다고 20일 밝혔다. 2026.10.20 09:26'])
        self.assertTrue(e and '"unknown"' in e[0])
        self.assertEqual(policy.verdict_date_errors(s, ['창원지법은 10월 20일 선고했다']), [])
        self.assertEqual(policy.verdict_date_errors(s, ['sentenced on Oct. 20 in court']), [])
        self.assertEqual(policy.verdict_date_errors(s, ['10月20日に言い渡した']), [])
        self.assertTrue(policy.verdict_date_errors(s, ['10월 2일', '1월 20일']))
        s['case']['verdict_date'] = 'soon'
        self.assertTrue(core.validate(s, core.SCHEMA))
        src = (W / 'factory/make_short.py').read_text()
        self.assertIn('verdict date not in sources', src)

    def test_8_stage_must_match_the_case(self):
        s = copy.deepcopy(Q049)
        s['stage'] = 'soju'  # convenience-store stage on a bar case
        e = [x for x in b3(s) if x.startswith('stage:')]
        self.assertTrue(e and 'stages that match' in e[0] and 'bar' in e[0].split('stages that match')[1])
        self.assertFalse([x for x in b3(Q049) if x.startswith('stage:')])

    def test_9_runbooks(self):
        spec = (W / 'factory/runbooks/SPEC.md').read_text()
        self.assertNotIn('≤45', spec)
        for w in ('≤30', 'result_first', 'pinned', 'stage_day', 'answer_text'):
            self.assertIn(w, spec)
        self.assertIn('report --scan', (W / 'factory/runbooks/RESEARCH.md').read_text())

    def test_10_result_first_and_answer_streak(self):
        two = [('q048', 'holiday', 2, 'quiz'), ('q047', 'kick', 2, 'quiz')]
        self.assertFalse([x for x in b3(Q049, two) if '3rd in a row' in x])  # result_first: never checked
        s = copy.deepcopy(Q049)
        del s['format']
        self.assertTrue([x for x in b3(s, two) if '3rd in a row' in x])
        self.assertFalse([x for x in b3(s, [('q048', 'holiday', 2, 'result_first'), ('q047', 'kick', 2, 'quiz')]) if '3rd in a row' in x])  # not counted
        self.assertTrue([x for x in b3(s, [('q048', 'holiday', 2, 'result_first')] + two) if '3rd in a row' in x])


class P2(unittest.TestCase):
    def build(self, tmp):
        b = make_short.Build(W / 'factory/specs/golden/en001.json')
        b.P = Path(tmp) / 'pkg'
        b.P.mkdir()
        return b

    def test_11_lead_silence_runs_for_en_and_ja(self):
        for L in ('en', 'ja'):
            with tempfile.TemporaryDirectory() as tmp:
                b = self.build(tmp)
                b.L = L
                (b.P / 'case.json').write_text(json.dumps(dict(utterances=[dict(id='L01', dur=90, mode='open', take='t1')], subtitles=[], duration=25.0)))
                sr = 24000
                sf.write(b.P / 'narration.wav', np.concatenate([np.zeros(sr), 0.3 * np.sin(np.arange(sr) / 10)]).astype('float32'), sr)
                with patch.object(make_short, 'sh', lambda *a, **k: (0, ['{}'])):
                    with self.assertRaises(core.Fail) as cm:
                        b.s_timing()
                self.assertTrue(any('R2' in x for x in cm.exception.errors), L)

    def test_12_takes_without_manifest_are_not_reused(self):
        with tempfile.TemporaryDirectory() as tmp:
            b = self.build(tmp)
            bf = Path(tmp) / 'bf'
            raw = bf / 'raw' / b.id
            raw.mkdir(parents=True)
            (bf / 'specs').mkdir()
            (bf / 'specs' / f'{b.id}.json').write_text(json.dumps(dict(lines=[dict(id='L01', tts='new words')])))
            (raw / 'L01_a.wav').write_bytes(b'old take')
            calls = []
            with patch.object(make_short, 'BF', bf), patch.object(make_short, 'sh', lambda cmd, **k: calls.append(cmd) or (0, [])):
                out = b.s_tts()
                self.assertTrue(calls and 'reused' not in out)
                self.assertEqual(json.loads((raw / '_tts.json').read_text()), {'L01': 'new words'})
                calls.clear()
                self.assertIn('reused', b.s_tts())  # same spoken text + manifest: reuse
                self.assertEqual(calls, [])


if __name__ == '__main__':
    unittest.main()
