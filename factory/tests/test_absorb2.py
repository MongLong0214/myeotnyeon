"""Absorption pass 2 (11-08): scene loudness, variety, audio evidence, voice treat, sfx bank, caption speed,
upload rules, thumbnail sheet."""
from pathlib import Path
import json,subprocess,sys,tempfile,unittest
import numpy as np,soundfile as sf
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lib import code_lint as cl,captions as cap,audio_evidence as ae,voice_treat as vt,sfx_bank as sb,upload_rules as ur,thumb_check as tc

def ff(*a):subprocess.run(['ffmpeg','-v','error','-y',*a],check=True)
def tone(path,sr=48000,dur=2.0,f=440,amp=0.3,rumble=0.0):
    t=np.arange(int(sr*dur))/sr;x=amp*np.sin(2*np.pi*f*t)+rumble*np.sin(2*np.pi*50*t);sf.write(path,x,sr);return x
def band(x,sr,f):
    s=np.abs(np.fft.rfft(x));fr=np.fft.rfftfreq(len(x),1/sr);return s[(fr>f-3)&(fr<f+3)].max()

class Absorb2(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory();cls.d=Path(cls.tmp.name)
    @classmethod
    def tearDownClass(cls):cls.tmp.cleanup()

    def test_scene_loudness_flags_8db_jump(self):
        v=self.d/'jump.mp4'
        ff('-f','lavfi','-i','color=c=gray:s=320x180:r=30:d=8','-f','lavfi','-i','sine=f=440:d=8:sample_rate=48000',
           '-filter_complex',"[1:a]volume='if(lt(t,4),0.1,0.1*2.5119)':eval=frame[a]",'-map','0:v','-map','[a]','-c:v','libx264','-c:a','aac','-shortest',str(v))
        shots=[dict(id='A',start_s=0,end_s=4),dict(id='B',start_s=4,end_s=8)]
        g=cl.check_scene_loudness(v,shots)
        self.assertEqual(g['status'],'ADVISORY');self.assertTrue(g['over_threshold']);self.assertEqual(g['threshold'],3.0)
        self.assertTrue(g['jumps']);print('scene loudness jumps',[(j['scene'],j['lu']) for j in g['jumps']])
        # opt-in: absent by default, present when asked
        self.assertNotIn('scene_loudness',cl.lint(v,320,180,30,8,shots,[],measure_video=False)['evidence']['checks'])
        self.assertIn('scene_loudness',cl.lint(v,320,180,30,8,shots,[],measure_video=False,scene_loudness=True)['evidence']['checks'])

    def test_variety(self):
        sh=lambda sizes:[dict(id=str(i),start_s=i,end_s=i+1,size=s) for i,s in enumerate(sizes)]
        g=cl.check_variety(sh(['wide','close','close','close','medium']))
        self.assertTrue(g['over_threshold']);self.assertEqual(g['runs'][0]['shots'],['1','2','3'])
        self.assertFalse(cl.check_variety(sh(['wide','close','close','medium']))['over_threshold'])
        self.assertEqual(cl.check_variety(sh(['wide',None,None,None,'close']))['status'],'NOT_MEASURED')
        self.assertNotIn('variety',cl.lint(None,1920,1080,30,5,sh(['close']*5),[],measure_video=False)['evidence']['checks'])
        self.assertTrue(cl.lint(None,1920,1080,30,5,sh(['close']*5),[],measure_video=False,variety=True)['evidence']['checks']['variety']['over_threshold'])

    def test_audio_evidence(self):
        w=self.d/'t.wav';tone(w,dur=3)
        r=ae.render(w,self.d/'ev',start=0.5,end=2.5)
        for k in ('waveform','spectrum','json'):self.assertTrue(Path(r[k]).stat().st_size>0)
        self.assertAlmostEqual(r['integrated_lufs'],-13.6,delta=1.5)   # 0.3 sine ~ -13.5 LUFS
        self.assertLess(r['true_peak_dbtp'],-9)
        self.assertEqual(json.loads(Path(r['json']).read_text())['integrated_lufs'],r['integrated_lufs'])

    def test_voice_treat_reduces_rumble(self):
        i,o=self.d/'v_in.wav',self.d/'v_out.wav';x=tone(i,dur=2,f=1000,amp=0.2,rumble=0.2)
        vt.treat(i,o)
        y,sr=sf.read(o);y=y if y.ndim==1 else y[:,0]
        self.assertLessEqual(abs(len(y)/sr-len(x)/48000),0.02)
        drop=20*np.log10(band(y,sr,50)/band(y,sr,1000))-20*np.log10(band(x,48000,50)/band(x,48000,1000))
        self.assertLess(drop,-6);print(f'voice_treat 50 Hz vs 1 kHz change {drop:.1f} dB')

    def test_sfx_peak_sync(self):
        f=self.d/'click.wav';x=np.zeros(4800);x[1234]=0.9;x[1200:1300]+=0.1;sf.write(f,x,48000)
        cut=1.5;at=sb.whoosh_before_cut(cut)
        self.assertAlmostEqual(at,cut-2/30)
        try:
            rep=sb.place([dict(id='cut_hit/punch',at=0.8,gain_db=-3),dict(file=str(f),at=at)],2.0,self.d/'sfx.wav')
        except FileNotFoundError as e:self.skipTest(str(e))
        for r in rep:self.assertLessEqual(abs(r['error_ms']),1.0,r)
        print('sfx placement error ms',[r['error_ms'] for r in rep])
        self.assertAlmostEqual(sf.info(str(self.d/'sfx.wav')).duration,2.0,places=3)

    def test_caption_reading_speed(self):
        cues=[dict(text='가나다라마바사아자차카타파하',start=0,end=1),dict(text='짧게',start=1,end=1.2),dict(text='보통 속도',start=2,end=4)]
        self.assertEqual(cap.lint(cues),cap.lint([dict(text=c['text']) for c in cues]))   # default unchanged
        codes=[(i['cue'],i['code']) for i in cap.lint(cues,cps_max=12)]
        self.assertIn((0,'reading_speed'),codes);self.assertIn((1,'hold_too_short'),codes)
        self.assertNotIn(2,[c for c,_ in codes])

    def test_upload_rules(self):
        self.assertEqual(ur.check('제목','설명 #a #b #c'),[])
        codes=lambda **k:[i['code'] for i in ur.check(**k)]
        self.assertIn('title_too_long',codes(title='x'*101,description=''))
        self.assertIn('description_too_long',codes(title='t',description='가'*1700))   # 5100 bytes
        self.assertIn('hashtags_over_three',codes(title='t',description='#a #b #c #d'))
        self.assertEqual(codes(title='t',description=' '.join(f'#t{i}' for i in range(61))),['hashtags_all_ignored'])
        self.assertIn('shorts_music_over_60s',codes(title='t',description='',duration_s=75,has_music=True,shorts=True))
        self.assertEqual(codes(title='t',description='',duration_s=55,has_music=True,shorts=True),[])

    def test_thumb_check(self):
        from PIL import Image
        p=self.d/'th.png';Image.new('RGB',(1280,720),'red').save(p)
        r=tc.check(p,self.d/'th',text_px=80)
        with Image.open(r['sheet']) as im:self.assertEqual(im.size,(160+320+48,180+32))
        self.assertEqual(r['text_px']['160'],10.0);self.assertTrue(r['warnings'])
        self.assertFalse(tc.check(p,self.d/'th',text_px=120)['warnings'])

if __name__=='__main__':unittest.main()
