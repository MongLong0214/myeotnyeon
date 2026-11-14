"""q049 review gaps: A early answer reveal, B option/heading overflow (ko), C meta leaks.
  .venv/bin/python -m unittest factory.tests.test_quiz_integrity"""
import copy, json, sys, unittest
from pathlib import Path
W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W))
from factory.shorts import core  # noqa: E402

GOLD = {g: json.loads((W / f'factory/specs/golden/{g}.json').read_text()) for g in ('q044', 'en001', 'ja001')}


def spec(choices, answer, lines, pops=()):
    return {'locale': 'ko', 'hook': ['내기', '원샷'], 'quiz': {'choices': choices, 'answer': answer}, 'pops': list(pops),
            'lines': [dict(beat=b, text=t, **({'shots': sh} if sh else {})) for b, t, sh in lines]}


BASE = [('open', '원샷하면 500만 원.', None), ('hook', '몇 년 나왔을까요?', [{'scene': 'react'}]), ('guess', '징역형일 것 같지만,', [{'scene': 'bubble', 'lines': ['징역형?']}]),
        ('twist', '실제 판결은, 예상과 달랐습니다.', [{'scene': 'stamp', 'label': '판결', 'stamp': '반전'}]), ('fact', '숨졌습니다.', [{'scene': 'paper', 'lines': ['0.485%']}]),
        ('answer2', '금고 1년에 집행유예 2년이었습니다.', [{'scene': 'paper', 'lines': ['집행유예 2년']}]), ('loop', '양주를,', None)]
CH = ['징역 3년', '벌금 700만 원', '금고1년 집유2년']


class EarlyReveal(unittest.TestCase):
    def test_clean(self):
        self.assertEqual(core.early_reveal(spec(CH, 2, BASE)), [])

    def test_narration_and_card(self):
        L = copy.deepcopy(BASE)
        L[3] = ('twist', '실제 판결은, 집행유예였습니다.', [{'scene': 'stamp', 'label': '판결', 'stamp': '집유'}])
        e = core.early_reveal(spec(CH, 2, L))
        self.assertEqual(len(e), 2)
        self.assertIn('lines[twist]: narration', e[0])
        self.assertIn('"집행유예"', e[0])
        self.assertIn('stamp "집유"', e[1])

    def test_shared_word_is_not_a_reveal(self):  # 징역 is in a wrong choice too: saying it gives nothing away
        self.assertEqual(core.early_reveal(spec(['집행유예', '징역 3년', '징역 7년'], 1, BASE)), [])

    def test_pop_before_quiz(self):
        e = core.early_reveal(spec(CH, 2, BASE, [{'beat': 'hook', 'big': '결국 집유', 'small': ''}]))
        self.assertTrue(e and e[0].startswith('pops[hook]'))

    def test_goldens(self):
        for g, s in GOLD.items():
            self.assertEqual(core.early_reveal(s), [], g)


class ChoiceFit(unittest.TestCase):
    def test_q049_long_choice(self):
        e = core.choice_fit_ko({'quiz': {'choices': ['징역 3년', '벌금 700만 원', '금고 1년에 집행유예 2년'], 'answer': 2}})
        self.assertTrue(any('option card' in x for x in e))
        self.assertTrue(any('answer heading' in x and 'max ~8' in x for x in e))

    def test_short_ok(self):
        self.assertEqual(core.choice_fit_ko({'quiz': {'choices': CH, 'answer': 2}}), [])
        self.assertEqual(core.choice_fit_ko(GOLD['q044']), [])

    def test_renderer_keeps_words(self):  # "2년" must never break as "2 / 년"
        src = (W / 'episodes/quiz/batch_1107/b_format/BStandard.tsx').read_text()
        self.assertGreaterEqual(src.count("wordBreak:'keep-all'"), 2)


class MetaLeaks(unittest.TestCase):
    def test_formula_leak(self):
        e = core.meta_leaks('화면의 환산은 이해를 돕기 위한 계산입니다: amt = F1.bet = 500만')
        self.assertTrue(any('F1.' in x for x in e))

    def test_clean_and_human(self):
        self.assertEqual(core.meta_leaks('화면의 환산은 이해를 돕기 위한 계산입니다: 1년 = 12개월'), [])
        vals = core.fact_values(GOLD['q044'])
        hs = [h for p in GOLD['q044']['pops'] for h in core.human_calc(p, vals, 'ko')]
        self.assertTrue(hs)
        self.assertEqual(core.meta_leaks(' / '.join(hs)), [], hs)


class ResultFirst(unittest.TestCase):
    """format "result_first" (format B): no quiz lines, cta card, gap A off, gap B still on; default unchanged"""
    def test_default_quiz_unchanged(self):
        s = GOLD['q044']
        leg = core.compile_b3(s, core.fact_values(s))
        self.assertEqual([l['id'] for l in leg['lines'] if l['id'] in ('L09', 'L10', 'L11')], ['L09', 'L10', 'L11'])
        self.assertEqual(leg['format'], 'quiz')
        self.assertEqual(leg['opinion'], core.FIXED['ko']['opinion'])

    def test_switch(self):
        s = copy.deepcopy(GOLD['q044'])
        s.update(format='result_first')
        leg = core.compile_b3(s, core.fact_values(s))
        modes = [l['mode'] for l in leg['lines']]
        self.assertFalse({'choices', 'options', 'answer', 'opinion'} & set(modes))  # ends on the reveal, then the loop line
        self.assertEqual(modes[-2:], ['answer2', 'loop'])
        self.assertEqual(core.validate(s, core.SCHEMA), [])

    def test_gap_a_off_gap_b_on(self):
        s = copy.deepcopy(GOLD['q044'])
        s['lines'][3]['text'] = '실제 판결은, 징역 3년이었습니다.'
        self.assertTrue(any('before the quiz' in e for e in core.check_b3(s, core.fact_values(s))[0]))
        s['format'] = 'result_first'
        self.assertFalse(any('before the quiz' in e for e in core.check_b3(s, core.fact_values(s))[0]))
        s['quiz']['choices'][1] = '징역 3년에 집행유예 5년 사회봉사'
        self.assertTrue(any('option card' in e for e in core.check_b3(s, core.fact_values(s))[0]))


class ThreeShots(unittest.TestCase):
    def test_three_shots_only_in_result_first(self):
        s = copy.deepcopy(GOLD['q044'])
        s['lines'][4]['shots'] = s['lines'][4]['shots'][:2] + [{'scene': 'react', 'expr': 'smug', 'move': 'nod'}]
        e = core.check_b3(s, core.fact_values(s))[0]
        self.assertTrue(any('needs 1-2 shots' in x for x in e))
        s['format'] = 'result_first'
        self.assertFalse(any('shots: needs' in x for x in core.check_b3(s, core.fact_values(s))[0]))
        s['lines'][4]['shots'].append({'scene': 'money'})
        self.assertTrue(any('needs 1-3 shots' in x for x in core.check_b3(s, core.fact_values(s))[0]))


if __name__ == '__main__':
    unittest.main()
