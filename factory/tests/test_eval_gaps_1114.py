"""Small-model EVAL gaps 2026-11-14 (Haiku zzh054, Sonnet zzs054): answer line whisper can hear, one exact fix per
misheard line, no amount split across cues (R8), no identical people shots in a row (R6), fetch before validate.
  .venv/bin/python -m unittest factory.tests.test_eval_gaps_1114"""
import io, json, sys, tempfile, unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch
W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W))
from factory import make_short  # noqa: E402
from factory.shorts import core, policy  # noqa: E402
from factory.shorts.voice import cer, norm  # noqa: E402

GOLD = W / 'factory/specs/golden/q044.json'


class Voice(unittest.TestCase):
    def test_numbers_and_spacing_compare_equal(self):
        self.assertEqual(cer(norm('징역 일 년 여섯 개월.', 'ko'), norm('징역 1년 6개월', 'ko')), 0)

    def test_answer_template_keeps_letter_apart_from_particle(self):
        # zzh054: "정답 에이" was heard as "정답에"; "정답은 A" keeps the letter a separate word
        self.assertEqual(core.FIXED['ko']['answer'].format(L='A', c='징역 1년'), '정답은 A, 징역 1년.')

    def test_fix_message_names_field_and_command(self):
        b = make_short.Build(GOLD)
        key = core.beat_keys(b.spec['lines'])[1]
        msg = b.voice_fix('L02', .1, 'x', {'tts': 'y', 'mode': 'hook'}, key)
        self.assertIn('lines[1].text', msg)
        self.assertIn('factory/make_short.py build factory/specs/golden/q044.json --from compile --force-tts', msg)

    def test_fix_message_for_compiler_line_says_report(self):
        msg = make_short.Build(GOLD).voice_fix('L11', .083, '정답에', {'tts': '정답 에이', 'mode': 'answer'}, None)
        self.assertIn('not yours to edit', msg)


class SplitNumber(unittest.TestCase):
    def test_detects_year_month_split(self):
        self.assertTrue(core.split_number('각각 징역 1년', '6개월,'))
        self.assertTrue(core.split_number('징역 1년,', '6개월'))
        self.assertFalse(core.split_number('징역 1년 6개월을', '선고했습니다.'))

    def test_chunker_keeps_amount_together(self):
        for ch in (core.chunk_ko('A 씨와 B 씨에게 각각 징역 1년 6개월,'), core.chunk_ko('부산지법은 두 사람에게 각각 징역 1년 6개월을 선고했습니다.')):
            self.assertFalse(any(core.split_number(a, b) for a, b in zip(ch, ch[1:])), ch)

    def test_compile_lint_blocks_split(self):
        b = make_short.Build(GOLD)
        errs = b.lint_chunks({'lines': [{'id': 'L05', 'chunks': ['각각 징역 1년', '6개월,']}]})
        self.assertTrue(any('splits one amount' in e for e in errs), errs)


class RepeatedShots(unittest.TestCase):
    def test_same_person_shot_twice_blocks(self):
        r = {'s': 'react', 'look': 'suit', 'expr': 'smug', 'move': 'nod', 'y': 2090}
        u = [{'id': 'L03', 'shots': [{'s': 'bubble'}, r]}, {'id': 'L04', 'shots': [dict(r)]}]
        self.assertEqual(len(core.repeated_shots(u)), 1)

    def test_props_and_changed_expression_pass(self):
        u = [{'id': 'L05', 'shots': [{'s': 'paper'}]}, {'id': 'L06', 'shots': [{'s': 'paper'}, {'s': 'react', 'look': 'suit', 'expr': 'smug'}]},
             {'id': 'L07', 'shots': [{'s': 'react', 'look': 'suit', 'expr': 'concern'}]}]
        self.assertEqual(core.repeated_shots(u), [])


class Fetch(unittest.TestCase):
    def test_skeleton_spec_fetches_without_schema(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, 'zzt.json')
            p.write_text(json.dumps({'id': 'zzt_fetch', 'sources': [{'id': 'S1', 'url': 'https://example.invalid/a'}]}))
            with patch.object(policy, 'fetch_sources', lambda s, refresh=False: {'S1': ('fetched', 'x' * 500)}), redirect_stdout(io.StringIO()) as o:
                self.assertEqual(make_short.main(['fetch', str(p)]), 0)
            self.assertIn('S1: fetched, 500 chars', o.getvalue())

    def test_missing_sources_explains(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d, 'zzt.json')
            p.write_text(json.dumps({'id': 'zzt_fetch'}))
            with redirect_stdout(io.StringIO()) as o:
                self.assertEqual(make_short.main(['fetch', str(p)]), 1)
            self.assertIn('sources', o.getvalue())


if __name__ == '__main__':
    unittest.main()
