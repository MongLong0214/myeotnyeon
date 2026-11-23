import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0,str(Path(__file__).resolve().parent))
from recipe import LIB, options, resolve, timeline
from compose import assemble, geometry_errors
from quality import verified_reference


class OperativeRegression(unittest.TestCase):
    def test_mux_keeps_the_final_audio_sample_on_the_picture_clock(self):
        import subprocess
        from types import SimpleNamespace
        import numpy as np
        import soundfile as sf
        from PIL import Image
        with tempfile.TemporaryDirectory() as directory:
            folder=Path(directory)
            plates=folder/'plates'
            plates.mkdir()
            count=37
            for f in range(count):
                Image.new('RGB',(72,128),(72+f,45,31)).save(plates/f'{f:04}.png')
            sound=folder/'mix.wav'
            t=np.arange(count*1600)/48000
            sf.write(sound,.1*np.sin(2*np.pi*220*t),48000)
            shots=SimpleNamespace(size=(72,128),load=lambda *unused:(plates,0))
            plan=[('range',0,count,'잇몸',None,count,plates,[{'leader':None}]*count)]
            movie=assemble(folder,'cut',plan,shots,{},sound)
            probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries',
                             'stream=duration,nb_frames','-of','json',movie]))['streams']
            self.assertEqual(int(probe[0]['nb_frames']),count)
            self.assertLess(abs(float(probe[1]['duration'])-count/30),.001)

    def test_only_permitted_tuple_at_each_stage(self):
        for case in LIB['cases']:
            choices=options(case)
            legal={'steps':[rows[-1] for rows in choices]}
            rows,repairs=resolve(case,legal)
            self.assertEqual(rows,legal['steps'])
            self.assertFalse(repairs)
            for field,value in [('pmid','wrong'),('tool','new'),('caption','freeform'),('thumbnail',-1),('code','run')]:
                bad=dict(legal,steps=[dict(rows[0],**{field:value}),*rows[1:]])
                output,repairs=resolve(case,bad)
                self.assertEqual(output[0],choices[0][0])
                self.assertTrue(repairs)
            shuffled={'steps':list(reversed(rows))}
            self.assertEqual(resolve(case,shuffled)[0],[r[0] for r in choices])

    def test_last_and_first_are_contiguous(self):
        for case in LIB['cases']:
            edit=timeline(case,resolve(case,{})[0])
            first,last=edit[0],edit[-1]
            self.assertEqual(last[2],first[1])
            self.assertEqual((last[0],last[3]),(first[0],first[3]))

    def test_penetration_and_missed_contact_block(self):
        row=dict(f=3,depths=[['tool','tooth',.201]],gaps=[.1,.22],tissue_gap=None)
        self.assertEqual(len(geometry_errors('luxate',[row])),2)
        fresh=dict(f=4,depths=[],gaps=[0],tissue_gap=.201)
        self.assertTrue(geometry_errors('incise',[fresh]))

    def test_failing_audit_cannot_certify_or_be_reused_for_another_movie(self):
        import hashlib
        with tempfile.TemporaryDirectory() as d:
            movie=Path(d)/'cut.mp4'
            movie.write_bytes(b'cut A')
            path=Path(d)/'review.json'
            path.write_text(json.dumps(dict(_model='fable',stage='movie',runs=[{}],final=9.5,p0=['blocking'],
                          _md5=hashlib.md5(movie.read_bytes()).hexdigest(),**{'pass':False})))
            self.assertFalse(verified_reference(movie,path)['certified'])
            movie.write_bytes(b'cut B')
            with self.assertRaises(ValueError):
                verified_reference(movie,path)


if __name__=='__main__':
    unittest.main()
