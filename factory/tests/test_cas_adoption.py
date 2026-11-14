"""Behavior tests for the MIT QA/audio ports; installed stack only."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from factory.lib import frame_qa as q, audio_mix as a
from factory import review_gates as r

class FrameTests(unittest.TestCase):
    def test_eof_freeze_and_planned_flash_cut(self):
        stats={'mean':[.5]*30};stats['mean'][2]=0;stats['mean'][3]=1
        diff=np.ones(29);diff[6]=10;diff[10:]=0
        found=q.classify(stats,diff)
        self.assertEqual(found['black'],[2]);self.assertEqual(found['white'],[3])
        self.assertIn(7,found['pops']);self.assertEqual(found['frozen'],[[10,30]])
        excluded=q.classify(stats,diff,planned={2,3,7},holds=range(10,30))
        # A planned cut must not conceal a truly black output frame.
        self.assertEqual(excluded['black'],[2])
        self.assertTrue(all(not excluded[k] for k in ('white','frozen','pops')))
    def test_our_shot_units(self):
        meta={'shots':[{'id':'s','from':30,'dur':15,'a':{'s1':3}},{'start_s':2,'end_s':3}]}
        self.assertEqual(q.shot_ranges(meta,30),[{'id':'s','a':30,'b':45},{'id':1,'a':60,'b':90}])
        cuts,_=q.exclusions(meta,30);self.assertIn(30,cuts);self.assertNotIn(35,cuts)
    def test_encoded_no_audio_clip_and_last_partial_sheet(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);v=p/'clip.mp4'
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=blue:s=96x160:r=30:d=0.5',
                            '-c:v','libx264','-pix_fmt','yuv420p',str(v)],check=True)
            report=q.analyze(v,p/'qa')
            self.assertEqual(report['frames'],15);self.assertIsNone(report['audio'])
            self.assertEqual(report['findings']['frozen'],[[0,15]])
            self.assertTrue((p/'qa'/report['sheets'][0]).exists())
            self.assertEqual(json.loads((p/'qa/report.json').read_text())['frames'],15)
    def test_advisory_survives_calibration_and_decode_errors(self):
        with tempfile.TemporaryDirectory() as tmp:
            c=r.Review(Path(tmp)/'absent.mp4',Path(tmp),'shorts',[],[],[],'','')
            gate=r.frame_qa_advisory(c)
            self.assertEqual(gate['status'],'ADVISORY');self.assertIn('error',gate['evidence'])
            gates={'FRAME_QA':gate}
            r.apply_calibration(gates)
            self.assertTrue(gates['FRAME_QA']['advisory'])
            # Exercise the real readiness boundary, including recalibration.
            sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
            from gates import finalize_review
            def baseline():
                return {**{k:r.pending({}) if k in r.SIGNED else r.result(True,{}) for k in r.ITEMS},
                        'FRAME_QA':dict(gate)}
            first=finalize_review(c,baseline())
            signs={k:dict(role='CTO',name='test reviewer',reason='fixture only',
                          input_sha256=first['input_sha256']) for k in r.SIGNED}
            final=finalize_review(c,baseline(),dict(cto_signoffs=signs))
            self.assertTrue(final['ready'])
            self.assertIn('FRAME_QA',final['advisory_gates'])
    def test_evaluate_calls_advisory_even_for_cached_measurements(self):
        with tempfile.TemporaryDirectory() as tmp:
            c=r.Review(Path(tmp)/'v.mp4',Path(tmp),'shorts',[],[],[],'','')
            with patch.object(c,'normalize'),patch.object(r,'ITEMS',{}),patch.object(r,'frame_qa_advisory',return_value={'advisory':True}) as fn:
                gates=r.evaluate(c,measure=False)
            fn.assert_called_once_with(c);self.assertTrue(gates['FRAME_QA']['advisory'])

class AudioTests(unittest.TestCase):
    def test_global_and_selected_take_supertonic_timestamps(self):
        asr={'segments':[{'words':[{'word':'판결','start':.2,'end':.5}]}]}
        self.assertEqual(a.word_spans(asr),[(.2,.5)])
        audio={'items':[{'id':'C1_1','new_start_sample':96000}]}
        self.assertEqual(a.supertonic_words(audio,{'C1_1':asr}),[{'start':2.2,'end':2.5}])
        with self.assertRaises(ValueError):a.word_spans({'items':[{'start':30,'end':60}]})
        with self.assertRaises(ValueError):a.word_spans([{'start':1,'end':.5}])
    def test_duck_follows_words_with_preroll_and_release(self):
        env=a.duck_db([{'start':1,'end':2}],4*a.SR)
        self.assertEqual(env[0],0);self.assertLess(env[int(1.5*a.SR)],-8.9)
        self.assertLess(env[int(.99*a.SR)],0)
        self.assertGreater(env[int(3.9*a.SR)],env[int(2.2*a.SR)])
        self.assertGreaterEqual(env.min(),-9);self.assertLessEqual(env.max(),0)
    def test_limiter_catches_intersample_peaks_and_preserves_stereo_link(self):
        n=12000;t=np.arange(n)/a.SR
        x=np.sin(2*np.pi*11025*t+np.pi/4)*1.8;x=np.stack([x,x*.5])
        y=a.limiter(x)
        self.assertLessEqual(a.true_peak(y),-1)
        np.testing.assert_allclose(y[1],y[0]*.5,atol=1e-12)
        self.assertEqual(y.shape,x.shape)
    def test_mix_meets_spec_and_will_not_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);t=np.arange(3*a.SR)/a.SR
            voice=np.sin(2*np.pi*220*t)*.12;voice*=.5+.5*np.sin(2*np.pi*3*t)**2
            a._write_pcm(p/'voice.wav',np.stack([voice,voice]))
            bed=np.sin(2*np.pi*330*t)*.2;a._write_pcm(p/'bed.wav',np.stack([bed,bed]))
            report=a.mix_new(p/'voice.wav',p/'new.wav',[{'start':.2,'end':2.7}],music=p/'bed.wav')
            self.assertAlmostEqual(report['integrated_lufs'],-14,delta=.2)
            self.assertLessEqual(report['true_peak_dbtp'],-1)
            with self.assertRaises(FileExistsError):a.mix_new(p/'voice.wav',p/'new.wav',[])
            self.assertEqual(a.read_pcm(p/'new.wav').shape,(2,len(t)))
    def test_silent_and_mismatched_words_do_not_publish(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp);a._write_pcm(p/'silent.wav',np.zeros((2,a.SR)))
            with self.assertRaises(ValueError):a.mix_new(p/'silent.wav',p/'out.wav',[{'start':0,'end':.8}])
            with self.assertRaises(ValueError):a.mix_new(p/'silent.wav',p/'out.wav',[{'start':0,'end':2}])
            self.assertFalse((p/'out.wav').exists())

if __name__=='__main__':unittest.main()
