"""youtube-agent-skill adoption: retention, sourcekit, chapters (factory/lib); synthetic inputs, no network."""
from pathlib import Path
import sys, tempfile, unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from lib import retention as rt, sourcekit as sk, chapters as ch


def srt(cues):
    def ts(t):
        h, m, s = int(t // 3600), int(t % 3600 // 60), t % 60
        return f'{h:02d}:{m:02d}:{s:06.3f}'.replace('.', ',')
    return '\n'.join(f'{i}\n{ts(a)} --> {ts(b)}\n{t}\n' for i, (a, b, t) in enumerate(cues, 1))


def api_resp(points):
    return dict(columnHeaders=[dict(name='elapsedVideoTimeRatio'), dict(name='audienceWatchRatio'),
                               dict(name='relativeRetentionPerformance')],
                rows=[[x, y, 0.5] for x, y in points])


class Retention(unittest.TestCase):
    def curve(self):
        # 20 s Short, 100 steps of 0.2 s; 130 % start (loop rewatch), steep 10-pt drop at 1 % -> 2 %,
        # 6-pt drop at 50 % -> 51 %, and a 20-pt sign-off drop at the end
        pts, y = [], 1.30
        for i in range(1, 101):
            x = i / 100
            if i == 2: y -= 0.10
            elif i == 51: y -= 0.06
            elif i == 100: y -= 0.20
            else: y -= 0.002
            pts.append((x, round(y, 4)))
        return pts

    def test_api_rows_keep_ratios_above_one(self):
        rows, rel = rt.rows_from_api(api_resp(self.curve()))
        self.assertEqual(len(rows), 100)
        self.assertGreater(rows[0][1], 100)
        self.assertEqual(rel[1.0], 0.5)
        with self.assertRaises(ValueError):
            rt.rows_from_api(dict(columnHeaders=[dict(name='day')], rows=[]))

    def test_cutoff_end_and_lines(self):
        rows, rel = rt.rows_from_api(api_resp(self.curve()))
        r = rt.analyse(rows, 'percent', 20, cutoff_s=2.5, rel=rel, end_s=1.0)
        self.assertEqual(r['cutoff_s'], 2.5)
        self.assertAlmostEqual(r['hook_leak'], 10 + 0.2 * 11, delta=0.3)   # within the first 12.5 %
        self.assertEqual([c['at_seconds'] for c in r['cliffs']], [0.2, 10.0])
        self.assertAlmostEqual(r['end_drop'], 20.8, delta=0.1)            # last 1 s: 20-pt sign-off + 4 slow steps
        cues = [(0.0, 0.5, '첫 문장'), (0.5, 2.0, '사건 설명'), (9.0, 11.0, '반전 대사')]
        rt.attach_lines(r, cues, window=0.1)
        self.assertEqual(r['cliffs'][0]['said'], '첫 문장')
        self.assertEqual(r['cliffs'][1]['said'], '반전 대사')
        # a long-form cutoff on the same curve swallows the mid drop into the hook
        self.assertGreater(rt.analyse(rows, 'percent', 20, cutoff_s=15)['hook_leak'], r['hook_leak'] + 5)

    def test_load_cues_srt_and_whisper_json(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 's.srt'
            p.write_text(srt([(0.1, 1.9, '배달 음식 받는 곳을\n바꿨다는 이유로'), (1.9, 4.6, '[음악] 박치기를 22번')]))
            self.assertEqual(rt.load_cues(p), [(0.1, 1.9, '배달 음식 받는 곳을 바꿨다는 이유로'), (1.9, 4.6, '박치기를 22번')])
            j = Path(d) / 'a.json'
            j.write_text('{"asr": {"segments": [{"start": 0, "end": 1.5, "text": " 몇 년?"}]}}')
            self.assertEqual(rt.load_cues(j), [(0.0, 1.5, '몇 년?')])

    def test_csv_export(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'r.csv'
            p.write_text('Video position (%),Audience retention (%)\n' + '\n'.join(f'{i},{100 - i * 0.5}' for i in range(0, 101, 10)))
            rows, unit = rt.load_csv(p)
            self.assertEqual(unit, 'percent')
            self.assertEqual(len(rows), 11)

    def test_headerless_short_needs_unit(self):
        # Jakes J1: seconds 0-60 of a 60 s Short look like percent; refuse to guess, accept an explicit unit.
        rows = [(float(i), 100 - i * 1.0) for i in range(0, 61, 2)]
        with self.assertRaises(ValueError):
            rt.analyse(rows, None, 60, cutoff_s=2.5)
        sec = rt.analyse(rows, 'seconds', 60, cutoff_s=2.5)
        self.assertEqual(sec['axis'], 'seconds')
        self.assertAlmostEqual(sec['hook_leak'], 2.0)
        self.assertEqual(rt.analyse(rows, None, 600, cutoff_s=15)['axis'], 'percent')  # long video: still percent
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / 'n.csv'
            p.write_text('\n'.join(f'{x},{y}' for x, y in rows))
            self.assertIsNone(rt.load_csv(p)[1])
            self.assertEqual(rt.main([str(p), '--duration', '60', '--unit', 'seconds', '--cutoff', '2.5']), None)


SOURCE = """서울중앙지방법원
판 결
사 건 2026고단1234 상해
주 문
피고인을 벌금 4,000,000원에 처한다.
이 유
범 죄 사 실
피고인은 2025. 11. 경 기숙사에서 피해자의 얼굴을
22차례에 걸쳐 박치기하였다.
양형의 이유
피고인은 범행을 모두 인정하고 피해자와 합의하였다.
"""


class RetentionPull(unittest.TestCase):
    def test_helpers_redact_and_duration(self):
        sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'channel' / 'analytics'))
        import retention_pull as rp
        self.assertEqual(rp.iso_seconds('PT32S'), 32)
        self.assertEqual(rp.iso_seconds('PT1M5S'), 65)
        msg = rp.redact('invalid_grant token=ya29.a0AfH6SMBxyz refresh=1//0gABCdef secret GOCSPX-abc_DEF')
        self.assertNotIn('ya29.a0', msg); self.assertNotIn('1//0g', msg); self.assertNotIn('GOCSPX-abc', msg)
        self.assertIn('invalid_grant', msg)


class SourceKit(unittest.TestCase):
    def setUp(self):
        self.d = tempfile.TemporaryDirectory()
        self.p = Path(self.d.name) / 'judgment.txt'
        self.p.write_text(SOURCE)

    def tearDown(self):
        self.d.cleanup()

    def test_korean_sections(self):
        heads = sk.index(sk.read(self.p))
        titles = [h['title'] for h in heads]
        self.assertEqual(titles, ['주 문', '이 유', '범 죄 사 실', '양형의 이유'])
        self.assertEqual([h['level'] for h in heads], [0, 0, 1, 1])
        joo = next(h for h in heads if h['title'] == '주 문')
        self.assertEqual((joo['start'], joo['end']), (4, 5))
        self.assertEqual(sk.section_of(heads, 9), '이 유 / 범 죄 사 실')

    def test_find_line_numbers_and_wrap(self):
        hits = sk.find(str(self.p), '22차례')
        self.assertEqual([h['line'] for h in hits], [9])
        self.assertIn('범 죄 사 실', hits[0]['section'])
        wrapped = sk.find(str(self.p), '얼굴을 22차례')          # phrase broken across lines 8-9
        self.assertEqual([h['line'] for h in wrapped], [8])
        self.assertEqual(sk.find(str(self.p), '22 차례에걸쳐')[0:1], [])
        self.assertEqual([h['line'] for h in sk.find(str(self.p), '22 차례에걸쳐', nospace=True)], [9])

    def test_show(self):
        self.assertEqual(sk.show(str(self.p), '5-5'), ['5: 피고인을 벌금 4,000,000원에 처한다.'])
        self.assertTrue(sk.show(str(self.p), '양형의 이유')[1].startswith('11: 피고인은'))
        with self.assertRaises(LookupError):
            sk.show(str(self.p), '없는 구획')


class Chapters(unittest.TestCase):
    def cues(self):
        topics = ['해킹 해커 지갑 코인 거래소', '수사 경찰 추적 체포 영장', '재판 판사 선고 징역 형량']
        out, t = [], 0.0
        for k, words in enumerate(topics):
            for i in range(10):
                w = words.split()
                out.append((t, t + 2.5, f'{w[i % 5]} {w[(i + 1) % 5]}에 대한 이야기'))
                t += 2.6
            t += 1.5   # longer pause between sections
        return out

    def test_boundaries_follow_pauses_and_topics(self):
        c = self.cues()
        got = ch.boundaries(c, target=3)
        self.assertEqual([x['start'] for x in got], [0.0, round(c[10][0], 2), round(c[20][0], 2)])
        self.assertTrue(all(x['title'] == '' for x in got))
        self.assertEqual(ch.validate(got, c[-1][1]), [])
        self.assertEqual(got[0]['label'], '00:00')

    def test_validate_rules(self):
        self.assertIn('first chapter must start at 00:00', ch.validate([dict(start=5), dict(start=20), dict(start=40)], 60))
        self.assertTrue(any('at least 3' in e for e in ch.validate([dict(start=0), dict(start=30)], 60)))
        self.assertTrue(any('10 s' in e for e in ch.validate([dict(start=0), dict(start=5), dict(start=30)], 60)))
        self.assertTrue(any('10 s' in e for e in ch.validate([dict(start=0), dict(start=20), dict(start=55)], 60)))
        self.assertTrue(any('ascending' in e for e in ch.validate([dict(start=0), dict(start=40), dict(start=20)], 60)))
        self.assertEqual(ch.validate([dict(start=0), dict(start=20), dict(start=40)], 60), [])

    def test_description_block_needs_titles(self):
        got = ch.boundaries(self.cues(), target=3)
        with self.assertRaises(ValueError):
            ch.description_block(got)
        for x, t in zip(got, ['해킹', '추적', '판결']):
            x['title'] = t
        self.assertEqual(ch.description_block(got).splitlines()[0], '00:00 해킹')


if __name__ == '__main__':
    unittest.main()
