"""CEO N18 regressions from real encoded frames; no rendering or network.

The text-only repository stores JPEG frame thumbnails in JSON. Source image and
video SHA-256, exact times, real shot specs and source calls accompany the pixels.
"""
import base64
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import review_gates as r
import visual_gates as v
from gates import apply_cto_signoffs, finalize_review

FIXTURE = Path(__file__).parent/'fixtures/n18_ceo_fix2.json'


class VisualGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(FIXTURE.read_text())

    def frame(self, key):
        return np.asarray(Image.open(io.BytesIO(base64.b64decode(
            self.fixture['frames'][key]['jpeg_base64']))).convert('RGB'))

    def context(self, out):
        c = r.Review(out/'video.mp4', out, 'longform', copy.deepcopy(self.fixture['shots']), [], [], '', '')
        c.video.write_bytes(b'fixture identity; frames are decoded CEO extracts')
        c.fps = 30; c.frames = 9942; c.width = 1920; c.height = 1080
        for s in c.shots:
            s.update(start_s=s['start_frame']/30, end_s=s['end_frame']/30)
        # Use the genuine decoded frames in the visual-sheet path. Additional
        # phase frames use the midpoint here; production extracts each exact PTS.
        def frame_at(t):
            shot = next(s for s in c.shots if s['start_s'] <= t < s['end_s'])
            p = out/(shot['id']+'.png')
            if not p.exists(): Image.fromarray(self.frame(shot['id'])).save(p)
            return p
        c.frame = frame_at
        return c

    def test_real_edge_positives_and_clean_negatives(self):
        for key in ['SH052', 'SH062', 'SH073']:
            with self.subTest(positive=key):
                self.assertIn('right', [h['edge'] for h in v.edge_bands(self.frame(key))])
        for key in ['SH003', 'SH034', 'SH037']:
            with self.subTest(negative=key):
                self.assertEqual(v.edge_bands(self.frame(key)), [])

    def test_entire_ceo_growth_sequence_is_detected(self):
        widths = [next(h['width_px'] for h in v.edge_bands(self.frame('growth_'+str(i)))
                       if h['edge'] == 'right') for i in range(8)]
        self.assertTrue(all(a < b for a, b in zip(widths, widths[1:])), widths)

    def test_four_edges_and_nonblack_fill(self):
        positive = self.frame('SH052')
        for k, edge in enumerate(['right', 'top', 'left', 'bottom']):
            self.assertIn(edge, [h['edge'] for h in v.edge_bands(np.rot90(positive, k))])
        # Invert a real frame to prove the check is independent of black RGB.
        self.assertTrue(v.edge_bands(255-positive))

    def test_real_lf2_exposed_edge_and_authored_scene_boundaries(self):
        self.assertIn('right', [h['edge'] for h in v.edge_bands(self.frame('lf2_12'))])
        # Real painted parking line, ceiling beam, desk edge, roof and wall panel.
        for n in [222,1488,2250,10746,12444]:
            with self.subTest(frame=n):
                self.assertEqual(v.edge_bands(self.frame('lf2_'+str(n))), [])

    def test_pts_sampling_includes_first_and_final_encoded_frames(self):
        clean=self.frame('SH003');bad=self.frame('SH052')
        frames=[clean]*8+[bad]
        meta=dict(streams=[dict(width=640,height=360)],frames=[dict(best_effort_timestamp_time=str(i/30)) for i in range(9)])
        proc=SimpleNamespace(stdout=io.BytesIO(b''.join(im.tobytes() for im in frames)),stderr=io.BytesIO(),
                             wait=lambda:0,poll=lambda:0)
        with patch.object(v.subprocess,'run',return_value=SimpleNamespace(stdout=json.dumps(meta))),patch.object(v.subprocess,'Popen',return_value=proc):
            report=v.measure_edges('existing.mp4')
        self.assertTrue(report['complete'])
        self.assertEqual((report['decoded_frames'],report['sampled_frames']),(9,3))
        self.assertEqual((report['first_frame'],report['last_frame']),(0,8))
        self.assertLessEqual(report['max_sample_gap_s'],.2)
        self.assertTrue(any(h['frame']==8 for h in report['hits']))

    def test_real_salute_shots_require_start_and_peak_review(self):
        with tempfile.TemporaryDirectory() as tmp:
            c = self.context(Path(tmp)); c.shots = [s for s in c.shots if s['id'] != 'SH036']
            gate = r.e4(c)
            self.assertEqual(gate['status'], 'NEEDS_REVIEW')
            self.assertEqual(gate['evidence']['required_handedness'], {'SH034':'right', 'SH037':'right'})
            by_id = {row['shot']: row['samples'] for row in gate['evidence']['shots']}
            for shot, start, peak in [('SH034',3957,4003),('SH037',4215,4279)]:
                self.assertIn(start, [s['frame'] for s in by_id[shot]])
                self.assertIn(peak, [s['frame'] for s in by_id[shot]])
            self.assertTrue(gate['evidence']['pages'])
            sig = dict(role='CTO',name='test reviewer',reason='test only',input_sha256='binding')
            apply_cto_signoffs({'E4':gate}, 'binding', {'E4':sig})
            self.assertEqual(gate['status'], 'NEEDS_REVIEW')
            sig['handedness'] = {'SH034':dict(hand='left',peak_frame=4003), 'SH037':dict(hand='right',peak_frame=4279)}
            apply_cto_signoffs({'E4':gate}, 'binding', {'E4':sig})
            self.assertEqual(gate['status'], 'NEEDS_REVIEW')
            sig['handedness']['SH034']['hand'] = 'right'
            apply_cto_signoffs({'E4':gate}, 'binding', {'E4':sig})
            self.assertEqual(gate['review_state'], 'CTO_SIGNED')

    def test_real_noncanonical_shot_passes_without_signature(self):
        with tempfile.TemporaryDirectory() as tmp:
            c = self.context(Path(tmp)); c.shots = c.shots[:1]
            gate = r.e4(c)
            self.assertEqual(gate['status'], 'PASS')
            self.assertTrue(gate['evidence']['not_applicable'])
            gates = {k:r.pending({}) if k in r.SIGNED else r.result(True,{}) for k in r.ITEMS}
            gates['E4'] = gate
            first = finalize_review(c, copy.deepcopy(gates))
            signs = {k:dict(role='CTO',name='test',reason='fixture',input_sha256=first['input_sha256'])
                     for k in r.SIGNED if k != 'E4'}
            self.assertTrue(finalize_review(c, gates, dict(cto_signoffs=signs))['ready'])

    def test_linked_script_only_and_timed_script_actions(self):
        with tempfile.TemporaryDirectory() as tmp:
            c = self.context(Path(tmp))
            for s in c.shots:
                for key in ['scene_mode','action','continuity','action_phases']:
                    s.pop(key, None)
            c.shots = c.shots[:1]
            c.script = 'SH003: 오른손으로 경례한다.'
            self.assertEqual([s['id'] for s in v.canonical_actions(c)], ['SH003'])
            c.script = '[00:02.63–00:05.46] 오른손으로 경례한다.'
            self.assertTrue(v.canonical_actions(c))
            c.script = 'SH999 [10:00–10:03] 경례한다.'
            c.shots.append(dict(c.shots[0],id='SH004',start_s=10,end_s=12))
            self.assertEqual(v.canonical_actions(c), [])
            self.assertEqual(r.e4(c)['status'], 'FAIL')

    def test_real_left_rig_fails_and_real_right_rig_is_not_flagged(self):
        left = self.fixture['left_call']['text']; right = self.fixture['right_call']['text']
        self.assertTrue(v.toon_salute_calls(left))
        self.assertEqual(v.toon_salute_calls(right), [])
        with tempfile.TemporaryDirectory() as tmp:
            c = self.context(Path(tmp)); c.shots = [s for s in c.shots if s['id']=='SH034']
            source = Path(tmp)/'Animatic.tsx'; source.write_text(left)
            c.config.update(salute_source=str(source),salute_geometry=str(r.ROOT/'production/lf_toon/src/ToonRig.tsx'))
            gate = r.e4(c)
            self.assertEqual(gate['status'], 'FAIL')
            self.assertTrue(gate['evidence']['static_left_arm_calls'])
            apply_cto_signoffs({'E4':gate}, 'binding', {'E4':dict(role='CTO',name='test',reason='test',input_sha256='binding')})
            self.assertEqual(gate['status'], 'FAIL')
            source.write_text(right)
            self.assertEqual(r.e4(c)['status'], 'NEEDS_REVIEW')
        self.assertTrue(v.left_salute_calls(dict(id='salute',rig='salute',arm='left')))
        self.assertFalse(v.left_salute_calls(dict(id='salute',rig='salute',arm='right')))

    def test_decode_or_coverage_failure_cannot_pass_edge_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            c = self.context(Path(tmp))
            with patch.object(v,'measure_edges',return_value=dict(complete=False,hits=[])):
                self.assertEqual(r.b6(c)['status'], 'FAIL')
            with patch.object(v,'measure_edges',return_value=dict(complete=True,hits=[])):
                self.assertEqual(r.b6(c)['status'], 'PASS')
            with patch.object(v,'measure_edges',return_value=dict(complete=True,hits=[dict(frame=6065,time_s=202.166667,**v.edge_bands(self.frame('SH052'))[0])])):
                self.assertEqual(r.b6(c)['status'], 'FAIL')


if __name__ == '__main__':
    unittest.main()
