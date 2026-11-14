"""Phone-size sheet (factory/lib/phone_check.py): frame plan and a real decode."""
from pathlib import Path
import json,subprocess,sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lib import phone_check as pc
from PIL import Image

class PhoneCheck(unittest.TestCase):
    def test_plan_first_seconds_and_every_cue_change(self):
        rows=pc.plan(30,600,[dict(start=5,end=7,text='a'),dict(from_=240,to=300,text='b')],first=3,every=.5)
        frames=[n for n,_ in rows]
        self.assertEqual(frames[:6],[0,15,30,45,60,75])
        self.assertIn(152,frames);self.assertIn(242,frames)
        self.assertEqual(len(frames),len(set(frames)))
    def test_sheet_is_360_wide_per_frame(self):
        with tempfile.TemporaryDirectory() as tmp:
            v=Path(tmp)/'v.mp4'
            subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','testsrc2=size=1920x1080:rate=30:duration=6','-pix_fmt','yuv420p',v],check=True)
            pages=pc.sheet(v,Path(tmp)/'out',[dict(start=4,end=5,text='자막 하나')],first=3,every=.5)
            meta=json.loads((Path(tmp)/'out/phone_sheet.json').read_text())
            self.assertEqual(len(meta['frames']),7)
            self.assertEqual(Image.open(Path(tmp)/'out/phone_frames/f_000122.png').size,(360,202))
            self.assertTrue(Path(pages[0]).is_file())

if __name__=='__main__':unittest.main()
