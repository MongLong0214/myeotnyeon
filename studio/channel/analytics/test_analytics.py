"""Behavior tests for actual snapshot, lossless missing data and offline joins."""
import copy
import json
from pathlib import Path
import unittest

from collect_parse import parse
from analyze import analyze

HERE = Path(__file__).resolve().parent
CANONICAL = '''[collection]
date = 2026-11-07
observed_at = 2026-11-07T10:00:00+09:00
[channel]
views = 1,234
subscribers_net = -1
subscribers_total = 9
[video -g-ubPCtVGw]
title = 일본도 살인
publish_date = 2026-11-04
metric_period = first_7d
views = 1,300
average_view_duration_seconds = 0:31
average_percentage_viewed = 136.6%
viewed_pct = 50.1%
swiped_away_pct = 49.9%
subscribers_net = 0
traffic.Shorts 피드 = 1,200 | 92.3%
traffic.기타 = null | null
'''


class AnalyticsTests(unittest.TestCase):
    def snapshot(self):
        p = HERE/'snapshot_2026-11-06.md'
        return parse(p.read_text(), str(p))

    def test_real_snapshot_missing_is_not_zero(self):
        d = self.snapshot()
        self.assertEqual(len(d['videos']), 15)
        self.assertEqual(d['channel']['views'], 15092)
        sword = next(v for v in d['videos'] if v['video_id'] == '-g-ubPCtVGw')
        self.assertEqual(sword['average_percentage_viewed'], 136.6)
        self.assertIsNone(sword['subscribers_net'])
        self.assertIsNone(sword['traffic_sources'])
        self.assertEqual(sword['metric_period'], 'unknown')
        self.assertIn('136.6%', sword['sources']['average_percentage_viewed']['raw'])

    def test_normalized_text_handles_traffic_zero_and_negative_net(self):
        d = parse(CANONICAL, 'local.txt')
        self.assertEqual(d['channel']['subscribers_net'], -1)
        v = d['videos'][0]
        self.assertEqual(v['subscribers_net'], 0)
        self.assertEqual(v['average_view_duration_seconds'], 31)
        self.assertEqual(v['traffic_sources'][0]['name'], 'Shorts 피드')
        self.assertEqual(v['traffic_sources'][0]['views'], 1200)
        self.assertIsNone(v['traffic_sources'][1]['views'])
        self.assertEqual(v['metric_period'], 'first_7d')

    def test_unknown_period_and_swiped_not_imputed(self):
        text = CANONICAL.replace('first_7d', 'unknown').replace('swiped_away_pct = 49.9%\n', '').replace('2026-11-07T10:00:00+09:00','null')
        v = parse(text, 'local.txt')['videos'][0]
        self.assertEqual(v['metric_period'], 'unknown')
        self.assertIsNone(v['swiped_away_pct'])

    def test_reject_invalid_counts_ranges_duration_and_fields(self):
        for old, new in [('views = 1,300', 'views = 1.3천'), ('viewed_pct = 50.1%', 'viewed_pct = 136.6%'),
                         ('0:31','0:61'), ('traffic.Shorts 피드 = 1,200 | 92.3%','traffic.Shorts 피드 = 1,200 | 192.3%'),
                         ('views = 1,300','vievs = 1,300')]:
            with self.subTest(new=new), self.assertRaises(ValueError):
                parse(CANONICAL.replace(old,new), 'local.txt')

    def test_join_does_not_fill_today_from_history_or_private_original(self):
        d = self.snapshot()
        features = json.loads((HERE/'features.json').read_text())
        before = copy.deepcopy(d)
        result = analyze(d, features, HERE/'daily/2026-11-06.json', HERE.parents[1]/'research/metrics/2026-10-30.json')
        self.assertEqual(d, before)
        self.assertEqual(result['missing_metrics']['subscribers_net'], 14)
        h2 = next(h for h in result['hypotheses'] if h['id']=='H2')
        self.assertIn('oxZUrYF8Chg', h2['comparisons'][0]['video'])
        self.assertNotIn('S-eU5rbP9yg', json.dumps(h2))
        self.assertEqual(len(result['experiments']),7)

    def test_metric_periods_do_not_pool_and_unknown_ids_reported(self):
        d = self.snapshot()
        d['videos'][0]['metric_period'] = 'first_48h'
        d['videos'][0]['video_id'] = 'ABCDEFGHIJK'
        features = json.loads((HERE/'features.json').read_text())
        result = analyze(d,features,Path('daily.json'),Path('/nonexistent/history.json'))
        self.assertEqual(result['unmatched_video_ids'], ['ABCDEFGHIJK'])
        d['videos'][0]['video_id'] = 'ozKvg2XFA0Y'
        result = analyze(d,features,Path('daily.json'),Path('/nonexistent/history.json'))
        self.assertTrue(any(g['metric_period']=='first_48h' for g in result['group_results']))


if __name__ == '__main__':
    unittest.main()
