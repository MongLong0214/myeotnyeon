import datetime as dt
import importlib.util
import json
import os
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent


def load(tmp):
    os.environ.update(FACTORY_REGISTRY=str(tmp / 'registry.json'), FACTORY_LEDGER=str(tmp / 'ledger.json'), FACTORY_PKG=str(tmp / 'pkg'))
    spec = importlib.util.spec_from_file_location('factory_queue', HERE / 'queue.py')
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


class QueueTests(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / 'registry.json').write_text(json.dumps({'channels': [
            dict(key='a', name='A', channel_id='UCaaa', package_prefix='q', publish_slots_kst=['12:00', '19:00']),
            dict(key='b', name='B', channel_id='UCbbb', package_prefix='en', publish_slots_kst=['09:00'])]}))
        for n in ('q1_B', 'q2_B', 'q3_B', 'en1_B', 'q4_B'):
            (self.tmp / 'pkg' / n).mkdir(parents=True)
            if n != 'q4_B':
                (self.tmp / 'pkg' / n / 'READY.txt').write_text('x')
        (self.tmp / 'pkg/q2_B/CTO_PASS.txt').write_text('ok')
        self.q = load(self.tmp)

    def test_states_and_record(self):
        self.q.main(['record', '--pkg', 'q3_B', '--video', 'v3', '--publish-at', '2999-01-01T12:00', '--channel', 'a'])
        rows = {r['pkg']: r['state'] for r in self.q.package_states(self.q.registry(), self.q.ledger())}
        self.assertEqual(rows, {'q1_B': 'built', 'q2_B': 'approved', 'q3_B': 'scheduled', 'en1_B': 'built'})
        self.assertEqual(self.q.ledger()['entries'][0]['publish_at'], '2999-01-01T12:00:00+09:00')
        with self.assertRaises(SystemExit):
            self.q.main(['record', '--pkg', 'q1_B', '--video', 'v1', '--publish-at', '2999-01-01T12:00+09:00', '--channel', 'a'])
        self.q.main(['record', '--pkg', 'q1_B', '--video', 'v1', '--publish-at', '2999-01-01T19:00+09:00', '--channel', 'a'])
        self.assertTrue(any((self.tmp / 'ledger_bak').iterdir()))

    def test_next_slots_skip_taken_and_other_channels(self):
        now = dt.datetime(2026, 11, 13, 10, 0, tzinfo=self.q.KST)
        self.q.write_ledger({'entries': [
            dict(qid='q1', channel='a', video_id='x', state='scheduled', publish_at='2026-11-13T12:00:00+09:00'),
            dict(qid='q2', channel='a', video_id='y', state='deleted', publish_at='2026-11-13T19:00:00+09:00'),
            dict(qid='en1', channel='b', video_id='z', state='scheduled', publish_at='2026-11-14T09:00:00+09:00')]})
        got = [t.isoformat() for t in self.q.next_slots(self.q.registry(), self.q.ledger(), 'a', 3, now)]
        self.assertEqual(got, ['2026-11-13T19:00:00+09:00', '2026-11-14T12:00:00+09:00', '2026-11-14T19:00:00+09:00'])
        got = [t.isoformat() for t in self.q.next_slots(self.q.registry(), self.q.ledger(), 'b', 1, now)]
        self.assertEqual(got, ['2026-11-15T09:00:00+09:00'])

    def test_verify_rows(self):
        reg = self.q.registry()
        entries = [dict(video_id='s', channel='a', state='scheduled', publish_at='2999-01-01T12:00:00+09:00'),
                   dict(video_id='w', channel='a', state='scheduled', publish_at='2999-01-01T12:00:00+09:00'),
                   dict(video_id='g', channel='a', state='deleted'),
                   dict(video_id='m', channel='a', state='published'),
                   dict(video_id='r', channel='a', state='replaced'),
                   dict(video_id='p', channel='a', state='replaced')]
        items = [dict(id='s', status=dict(privacyStatus='private', publishAt='2999-01-01T03:00:00Z'), snippet=dict(channelId='UCaaa')),
                 dict(id='w', status=dict(privacyStatus='private', publishAt='2999-01-01T03:00:00Z'), snippet=dict(channelId='UCbbb')),
                 dict(id='r', status=dict(privacyStatus='private'), snippet=dict(channelId='UCaaa')),
                 dict(id='p', status=dict(privacyStatus='public'), snippet=dict(channelId='UCaaa'))]
        got = [v for _, v in self.q.verify_rows(entries, items, reg)]
        self.assertEqual(got, ['ok', 'BAD channel', 'ok-gone', 'MISSING', 'ok-private', 'BAD replaced-but-public'])


    def test_judge_kill_rule(self):
        rule = dict(first_uploads=3, views_48h_below=500, engaged_share_below=0.30, rejudge_every_days=7, action='stop')
        now = dt.datetime(2026, 11, 20, tzinfo=self.q.KST)
        low = lambda v, e: dict(views_48h=v, engaged_views_48h=e)
        self.assertEqual(self.q.judge(rule, [low(100, 10)] * 2, now=now)['verdict'], 'pending')
        self.assertEqual(self.q.judge(rule, [low(499, 149)] * 3, now=now)['verdict'], 'stop')
        # one upload over 500 views keeps the channel alive
        self.assertEqual(self.q.judge(rule, [low(100, 10), low(500, 10), low(100, 10)], now=now)['verdict'], 'continue')
        # low views but a strong engaged share (>= 30%) also keeps it alive
        got = self.q.judge(rule, [low(100, 10), low(100, 30), low(100, 10)], [low(1000, 500)] * 3, now=now)
        self.assertEqual((got['verdict'], got['next_review'], got['ratio_to_baseline']), ('continue', '2026-11-27', 0.1))
        # zero views counts as share 0, not a crash
        self.assertEqual(self.q.judge(rule, [low(0, 0)] * 3, now=now)['verdict'], 'stop')


if __name__ == '__main__':
    unittest.main()
