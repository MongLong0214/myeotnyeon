"""core.placeholder_text: a placeholder ("auto", "TODO", "", "...") in on-screen or subtitle text fails validate/compile.
  .venv/bin/python -m unittest factory/tests/test_placeholder_text.py"""
import json, sys, unittest
from pathlib import Path
W = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(W))
from factory.shorts import core  # noqa: E402


class PlaceholderText(unittest.TestCase):
    def test_golden_specs_clean(self):
        for g in ('q044', 'en001', 'ja001', 'bc001'):
            self.assertEqual(core.placeholder_text(json.loads((W / f'factory/specs/golden/{g}.json').read_text())), [], g)

    def test_tokens_fail(self):
        for tok in ('auto', 'TODO', 'TBD', '', ' ', '...', '…', 'xxx'):
            e = core.placeholder_text({'lines': [{'text': tok}]})
            self.assertEqual(len(e), 1, tok)
            self.assertIn('$.lines[0].text', e[0])

    def test_unexpanded_chunks_fail(self):  # ja001 2026-11-14: chunks "auto" rendered as "a/u", "t/o"
        leg = {'lines': [{'id': 'L11', 'shown': '正解はC、実刑判決。', 'chunks': 'auto'}, {'id': 'L10', 'shown': None, 'chunks': None}]}
        e = core.placeholder_text(leg, ('shown', 'chunks'))
        self.assertEqual(len(e), 1)
        self.assertIn('lines[0].chunks', e[0])

    def test_list_items_and_real_text(self):
        self.assertEqual(len(core.placeholder_text({'quiz': {'choices': ['징역 1년', 'TBD', '벌금']}})), 1)
        self.assertEqual(core.placeholder_text({'lines': [{'text': 'auto loan fraud', 'chunks': ['auto loan', 'fraud']}]}), [])


if __name__ == '__main__':
    unittest.main()
