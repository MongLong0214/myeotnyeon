"""Integration: review gates on the preserved N18 production build.

Needs production/lf_toon/v2/n18/{fact_trace.md,shots_v2.json} and the encoded frames under
factory/review_runs/n18_v2_1080p_001/frames/. Those are production outputs kept outside git;
without them these tests fail.
"""
from pathlib import Path
import copy, io, json, sys, unittest
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tests'))
import review_gates as r
from test_review_gates import ReviewHarness


class ReviewN18Production(ReviewHarness):
    def test_n18_heading_fact_date_and_absent_date(self):
        self.c.facts=(r.ROOT/'production/lf_toon/v2/n18/fact_trace.md').read_text()
        self.assertIn('2024-05-23',self.c.facts.splitlines()[440])
        for text,expected in [('2024년 5월 23일','PASS'),('2024년 5월 24일','FAIL')]:
            self.c.subtitles=[dict(text=text,start_s=0,end_s=1)]
            gate=r.e1(self.c)
            self.assertEqual(gate['status'],expected)
            self.assertEqual(bool(gate['evidence']['dates_not_in_facts']),expected=='FAIL')
    def test_n18_in_shot_motion_and_real_unlisted_hard_cut(self):
        from PIL import Image
        shots=r.read_json(r.ROOT/'production/lf_toon/v2/n18/shots_v2.json')['shots'][:2]
        frames=r.HERE/'review_runs/n18_v2_1080p_001/frames'
        # Read preserved final-encode frames; do not render or encode any video.
        rgb=r.np.stack([r.np.asarray(Image.open(frames/f'{n:06}.jpg').convert('RGB')) for n in range(80)])
        for count,expected in [(79,'PASS'),(80,'FAIL')]:
            with self.subTest(decoded_frames=count):
                self.c.shots=copy.deepcopy(shots)
                # Removing SH003 from the list must not hide its real cut at f79.
                if count==80:self.c.shots[-1]['end_frame']=80
                probe=dict(streams=[dict(codec_type='video',avg_frame_rate='30/1',duration=str(count/30),width=640,height=360,nb_frames=str(count))],format=dict(duration=str(count/30)))
                with patch.object(r,'run') as run:
                    run.return_value.stdout=json.dumps(probe).encode();self.c.normalize()
                self.assertEqual([round(s['start_s']*30) for s in self.c.shots],[0,47])
                self.assertEqual(r.sec(dict(start=30),'start',30),1) # legacy frames
                with patch.object(r.subprocess,'Popen') as popen:
                    popen.return_value.stdout=io.BytesIO(rgb[:count].tobytes())
                    popen.return_value.stderr=io.BytesIO();popen.return_value.wait.return_value=0;popen.return_value.poll.return_value=0
                    r.scan_frames(self.c,exhaustive=False,write_frames=False)
                self.words([('달렸습니다.',0,47/30),('끝났습니다.',47/30,79/30)])
                self.c.media.pop('cut_sheet',None)
                with patch.object(self.c,'frame',return_value=self.out/'frame.jpg'),patch.object(r,'sheet',return_value=[]):
                    gate=r.d2(self.c)
                self.assertTrue(all(n not in gate['evidence']['all_cut_frames'] for n in [2,3,5,10]))
                self.assertEqual(gate['evidence']['unlisted_cut_frames'],[79] if count==80 else [])
                if count==80:self.assertEqual(gate['evidence']['cuts'][-1]['nearest_clause_delta_s'],0)
                # Preserve D2's required CTO MATCH step; only the good case signs.
                signs=dict(D2=dict(self.signature('hash'),matches={s['id']:'MATCH' for s in self.c.shots}))
                apply_cto_signoffs({'D2':gate},'hash',signs)
                self.assertEqual(gate['status'],expected)


if __name__ == '__main__':
    unittest.main()
