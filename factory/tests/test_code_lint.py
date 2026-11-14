"""Code lint gate (factory/lib/code_lint.py): geometry, measured overflow, report-only video checks."""
from pathlib import Path
import subprocess,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lib import code_lint as cl
import review_gates as r

W,H,FPS=1920,1080,30
SHOTS=[dict(id='S1',start_s=0,end_s=2),dict(id='S2',start_s=2,end_s=4)]
GEO=cl.LONGFORM_CAPTION

def run(subs=(),faces=None,texts=(),geometry=GEO):
    return cl.lint(None,W,H,FPS,4,SHOTS,list(subs),faces,texts,geometry,measure_video=False)

class CodeLint(unittest.TestCase):
    def test_faces_not_measured_without_metadata(self):
        g=run()
        self.assertEqual(g['status'],'PASS')
        self.assertIn('face_cut',g['evidence']['not_measured'])
    def test_face_cut_by_frame_edge(self):
        half=[dict(frame=n,id='A',box=[1800,300,240,240]) for n in range(0,60,3)]   # 50 % visible
        g=run(faces=half)
        self.assertEqual(g['status'],'FAIL');self.assertIn('face_cut',g['evidence']['blocking'])
        # Fully visible, or fully outside (an exit), is not a cut face.
        ok=[dict(frame=n,id='A',box=[800,300,240,240]) for n in range(0,60,3)]+[dict(frame=n,id='B',box=[2000,300,200,200]) for n in range(0,60,3)]
        self.assertEqual(run(faces=ok)['status'],'PASS')
        # A face passing the edge for a few samples while the camera moves is allowed (< 1/3 of the shot).
        passing=[dict(frame=n,id='A',box=[1800 if n<9 else 800,300,240,240]) for n in range(0,60,3)]
        self.assertEqual(run(faces=passing)['evidence']['checks']['face_cut']['status'],'PASS')
    def test_shot_level_faces_and_text_over_face(self):
        shots=[dict(SHOTS[0],faces=[dict(id='A',box=[860,880,200,200])]),SHOTS[1]]  # chin in the caption band
        subs=[dict(start_s=0.5,end_s=1.5,text='자막이 얼굴 위에 있습니다')]
        g=cl.lint(None,W,H,FPS,4,shots,subs,None,(),GEO,measure_video=False)
        self.assertIn('text_on_face',g['evidence']['blocking'])
        self.assertTrue(all(0.5<=i['t']<1.5 for i in g['evidence']['checks']['text_on_face']['issues']))
        label=[dict(text='라벨',box=[700,250,700,200],start_s=2,end_s=4)]
        g=run(faces=[dict(t=3,id='B',box=[900,200,200,200])],texts=label)
        self.assertIn('text_on_face',g['evidence']['blocking'])
    def test_subtitle_overflow_measured(self):
        ok=[dict(start_s=0,end_s=2,text='검은 승용차가 은행\n지하의 길을 막았습니다.')]
        self.assertEqual(run(ok)['evidence']['checks']['subtitle_overflow']['status'],'PASS')
        three=[dict(start_s=0,end_s=2,text='첫 줄입니다\n둘째 줄입니다\n셋째 줄입니다')]
        g=run(three);self.assertEqual(g['status'],'FAIL');self.assertIn('subtitle_overflow',g['evidence']['blocking'])
        wide=[dict(start_s=0,end_s=2,text='가'*40)]   # one unbreakable word wider than 1690 px
        self.assertEqual(run(wide)['evidence']['checks']['subtitle_overflow']['issues'][0]['lines'],1)
        self.assertEqual(run(wide)['status'],'FAIL')
        self.assertEqual(run(ok,geometry=None)['evidence']['checks']['subtitle_overflow']['status'],'NOT_MEASURED')
    def test_subtitle_rules_are_report_only(self):
        g=run([dict(start_s=0,end_s=2,text='가나다라마바사아자차카타파하 가나다라')])
        self.assertEqual(g['status'],'PASS');self.assertTrue(g['report_only'])
        self.assertIn('subtitle_rules',g['evidence']['flagged_report_only'])
    def test_video_checks_report_pops_without_blocking(self):
        with tempfile.TemporaryDirectory() as tmp:
            v=Path(tmp)/'pop.mp4'
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=320x180:rate=30:duration=4',
                            '-vf',"drawbox=x=0:y=0:w=iw:h=ih:color=white:t=fill:enable='eq(n,45)'",'-pix_fmt','yuv420p',v],check=True)
            g=cl.lint(v,320,180,30,4,SHOTS,[],None,(),None)
        checks=g['evidence']['checks']
        self.assertIn(45,checks['pops']['frames'])
        self.assertEqual(g['status'],'PASS');self.assertIn('pops',g['evidence']['flagged_report_only'])
        self.assertIn(checks['static']['status'],{'ADVISORY'});self.assertIn('share',checks['repeats'])
    def test_review_gate_wiring_and_advisory(self):
        with tempfile.TemporaryDirectory() as tmp:
            c=r.Review(Path(tmp)/'v.mp4',Path(tmp),'longform',SHOTS,[dict(start_s=0,end_s=2,text='a\nb\nc')],[],'','')
            c.width,c.height,c.fps,c.duration=W,H,FPS,4;c.config['code_lint_video']=False
            with patch.object(r,'digest',lambda p:'x'):g=r.code_lint_gate(c)
            self.assertEqual(g['status'],'FAIL');self.assertTrue(Path(g['evidence']['report']).is_file())
            gates=r.apply_calibration({'CODE_LINT':g})
            self.assertFalse(gates['CODE_LINT']['advisory'])
            c.subtitles=[dict(start_s=0,end_s=2,text='짧은 자막')]
            with patch.object(r,'digest',lambda p:'x'):g=r.code_lint_gate(c)
            self.assertTrue(r.apply_calibration({'CODE_LINT':g})['CODE_LINT']['advisory'])

    def test_rhythm_flags_even_runs_and_passes_varied_cuts(self):
        def shots(lengths,acts=None):
            t,out=0.0,[]
            for i,x in enumerate(lengths):
                out.append(dict(id=f'S{i}',start_s=t,end_s=t+x,**({'act':acts[i]} if acts else {})));t+=x
            return out
        even=cl.check_rhythm(shots([3.0]*14))
        self.assertTrue(even['over_threshold']);self.assertEqual(even['longest_alike_run'],14);self.assertEqual(even['count'],2)
        varied=cl.check_rhythm(shots([1.2,4.5,0.8,2.6,6.0,1.0,3.3,0.7,5.1,2.0,1.5,7.2,0.9,2.8]))
        self.assertFalse(varied['over_threshold']);self.assertGreaterEqual(varied['cv'],0.3)
        flat=cl.check_rhythm(shots([1.0,4.0]*9,acts=['a']*6+['b']*6+['c']*6))
        self.assertTrue(any('same pace' in x for x in flat['issues']))
        self.assertEqual(cl.check_rhythm(shots([2.0]*5))['status'],'NOT_MEASURED')
        self.assertIn('rhythm',run()['evidence']['checks'])
        self.assertEqual(run()['status'],'PASS')  # report-only

if __name__=='__main__':unittest.main()
