"""Number gate: a ledger record without a number passes only as one declared unnumbered std upload per qid."""
from pathlib import Path
import sys, tempfile, unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from gates import number_gate, load

FIX = Path(__file__).resolve().parent / 'fixtures/number_gate'
P = lambda n: dict(badge=n, endCard=n, cover=n)


class NumberGate(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.pkg = Path(self.tmp.name)
        for q, text in (('q020', '번호 미배정. 업로드·예약 없음.\n'), ('q021', '설명에 번호 미배정이라고 적었을 뿐\n')):
            (self.pkg / f'{q}_std').mkdir(); (self.pkg / f'{q}_std/meta.txt').write_text(text)
        self.numbered = dict(qid='q014', no=15, state='published', video_id='S-eU5rbP9yg')
        self.legit = dict(qid='q020', video_id='S_apLF1EfZM', state='published')

    def tearDown(self): self.tmp.cleanup()
    def gate(self, entries, n=99): return number_gate(n, 'q017', P(n), dict(entries=entries), pkg=self.pkg)

    def test_legit_unnumbered_passes(self):
        g = self.gate([self.numbered, self.legit])
        self.assertEqual(g['status'], 'PASS', g); self.assertTrue(g['evidence']['unnumbered'][0]['accepted'])

    def test_malformed_unnumbered_fails(self):
        for bad in (dict(qid='q020', state='published'),                       # no video_id
                    dict(qid='q020', video_id='x', state='reserved'),          # not uploaded
                    dict(qid='q021', video_id='y', state='published'),         # 번호 미배정 only as a substring
                    dict(qid='q022', video_id='z', state='published'),         # no std meta
                    dict(qid='../q020', video_id='z', state='published')):     # qid not qNNN
            g = self.gate([self.numbered, bad])
            self.assertEqual(g['status'], 'FAIL', bad); self.assertIn('missing/invalid number', g['evidence']['reason'])

    def test_null_or_non_int_number_fails(self):
        for no in (None, '15', 15.0, True):
            g = self.gate([self.numbered, dict(qid='q016', no=no, state='scheduled', video_id='v')])
            self.assertEqual(g['status'], 'FAIL', no); self.assertEqual(g['evidence']['malformed'][0]['reason'], 'no must be an integer')

    def test_two_unnumbered_records_for_one_qid_fail(self):
        g = self.gate([self.numbered, self.legit, dict(self.legit, video_id='other')])
        self.assertEqual(g['status'], 'FAIL'); self.assertIn('more than one unnumbered', str(g['evidence']['malformed']))

    def test_duplicate_number_fails(self):
        g = self.gate([self.numbered, self.legit], n=15)
        self.assertEqual(g['status'], 'FAIL'); self.assertEqual(g['evidence']['conflicts'][0]['qid'], 'q014')

    def test_ledger_fixture_is_well_formed(self):
        g = number_gate(99, 'q017', P(99), load(FIX / 'ledger.json'), pkg=FIX / 'pkg')
        self.assertEqual(g['status'], 'PASS', g['evidence'].get('malformed'))
        self.assertEqual(sorted(u['qid'] for u in g['evidence']['unnumbered']), ['q018', 'q020'])


if __name__ == '__main__':
    unittest.main()
