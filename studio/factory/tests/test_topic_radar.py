"""Offline checks for topic_radar's filters and scoring (no network, no keychain)."""
import importlib.util
from pathlib import Path
import unittest

spec = importlib.util.spec_from_file_location('topic_radar', Path(__file__).parents[1] / 'topic_radar.py')
tr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tr)


class HardFilterTests(unittest.TestCase):
    def test_sex_crime_or_child_victim_is_excluded(self):
        c = dict(keyword='아동 성범죄 가해자 징역', verdict_date='2026-01-01')
        self.assertEqual(tr.hard_exclude(c, []), 'sex_crime_or_child_victim_excluded')

    def test_no_verdict_or_trial_stage_is_excluded(self):
        c = dict(keyword='음주운전 뺑소니')
        self.assertEqual(tr.hard_exclude(c, []), 'no_confirmed_verdict_or_trial_stage')

    def test_candidate_with_verdict_date_passes(self):
        c = dict(keyword='보이스피싱 조직원 구속', verdict_date='2026-01-01')
        self.assertIsNone(tr.hard_exclude(c, []))

    def test_already_published_title_overlap_is_excluded(self):
        c = dict(keyword='지하철 방화 160명 살인미수', case_id='v2-14', verdict_date='2026-01-01')
        titles = [tr.norm('지하철에 휘발유 방화…160명 살인미수 혐의, 몇 년?')]
        self.assertEqual(tr.hard_exclude(c, titles), 'already_published_on_own_channel')

    def test_single_short_token_overlap_does_not_exclude(self):
        c = dict(keyword='살인 사건 전과자 재판', verdict_date='2026-01-01')
        titles = [tr.norm('450원 초코파이가 형사재판…1,050원의 결말은?')]
        self.assertIsNone(tr.hard_exclude(c, titles))

    def test_stalking_is_not_blocked(self):
        c = dict(keyword='스토킹 가해자 항소심', verdict_date='2026-01-01')
        self.assertIsNone(tr.hard_exclude(c, []))


class ScoringTests(unittest.TestCase):
    def test_minmax_handles_missing_values(self):
        out = tr.minmax([1.0, None, 3.0])
        self.assertIsNone(out[1])
        self.assertAlmostEqual(out[0], 0.0)
        self.assertAlmostEqual(out[2], 1.0)

    def test_score_batch_renormalizes_when_signals_missing(self):
        rows = [
            dict(raw=dict(datalab=1.0, yt_demand=10.0, recency=0.5, news_total=100, autocomplete=1.0)),
            dict(raw=dict(datalab=2.0, yt_demand=None, recency=None, news_total=None, autocomplete=None)),
        ]
        tr.score_batch(rows)
        self.assertIsNotNone(rows[0]['score'])
        self.assertIsNotNone(rows[1]['score'])  # only datalab present, still scored on renormalized weight
        self.assertGreater(rows[0]['score'], 0)

    def test_score_batch_is_null_when_nothing_measured(self):
        rows = [dict(raw=dict(datalab=None, yt_demand=None, recency=None, news_total=None, autocomplete=None))]
        tr.score_batch(rows)
        self.assertIsNone(rows[0]['score'])

    def test_recency_decays_and_rejects_missing_or_future_dates(self):
        self.assertIsNone(tr.recency_raw(None))
        import datetime as dt
        today = dt.date.today().isoformat()
        self.assertAlmostEqual(tr.recency_raw(today), 1.0, places=2)
        future = (dt.date.today() + dt.timedelta(days=5)).isoformat()
        self.assertIsNone(tr.recency_raw(future))


if __name__ == '__main__':
    unittest.main()
