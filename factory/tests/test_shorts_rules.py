"""Shorts format rules (shorts_rules.py) and SHORTS_RULES gate wiring; synthetic media only."""
from pathlib import Path
import copy,subprocess,sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import shorts_rules as sr
import review_gates as r

GOOD=dict(opening_template='B',hook_question=dict(text='층간소음에 망치 들면 몇 년 나왔을까요?',end_s=3.3),
          expectation=dict(text='징역 1년은 나올 것 같지만',at_s=4.4),twist=dict(text='실제 판결은 벌금형',at_s=6.1),
          subscribe_gag=dict(at_s=7.4,dur_s=.8,gag='판사가 구독 버튼을 의사봉으로 두드림'),
          loop=dict(last_line='그날 밤 망치를 들고 올라간',first_shot='S1'),
          number_pops=[dict(at_s=9+i,value=f'벌금 {300+i}만 원',source='판결문 p.3',life_unit='치킨',basis='1마리 2만 원') for i in range(5)])

class Spec(unittest.TestCase):
    def test_good_spec_passes(self):self.assertEqual(sr.check_spec(GOOD),[])
    def test_each_rule_fires(self):
        for path,value,field in [(('hook_question','end_s'),4.0,'hook_question'),(('expectation','at_s'),5.6,'expectation'),
                                 (('twist','at_s'),7.0,'twist'),(('subscribe_gag','dur_s'),1.5,'subscribe_gag'),
                                 (('loop','last_line'),'끝났습니다.','loop')]:
            s=copy.deepcopy(GOOD);s[path[0]][path[1]]=value
            self.assertIn(field,[i['field'] for i in sr.check_spec(s)],path)
        s=copy.deepcopy(GOOD);s['subscribe_gag']['gag']='댓글 남겨주세요 카드';self.assertTrue(sr.check_spec(s))
        s=copy.deepcopy(GOOD);s['number_pops']=s['number_pops'][:3];self.assertTrue(sr.check_spec(s))
        s=copy.deepcopy(GOOD);del s['number_pops'][0]['basis'];self.assertIn('number_pops[0]',[i['field'] for i in sr.check_spec(s)])
        s=copy.deepcopy(GOOD);s['number_pops'][1]['source']='';self.assertIn('number_pops[1]',[i['field'] for i in sr.check_spec(s)])

class Title(unittest.TestCase):
    def test_title_rules(self):
        t=sr.make_title('층간소음에','망치','들면 몇 년 나옴?')
        self.assertEqual(t,"층간소음에 '망치' 들면 몇 년 나옴?");self.assertEqual(sr.check_title(t),[])
        self.assertTrue(sr.check_title("층간소음에 '망치' 들면 몇 년 나옴"))
        self.assertTrue(sr.check_title("'층간소음' '망치' 들면 몇 년 나옴?"))
        self.assertTrue(sr.check_title("'망치' 몇 년?"))

class Pair(unittest.TestCase):
    def test_particles(self):
        for w,stem in [('노동자에','노동자'),('관리자의','관리자'),('손님을','손님'),('밖으로','밖'),('판결은','판결'),
                       ('나이','나이'),('22번,','22번'),('벌금만','벌금'),('친구와','친구'),('이','이')]:
            self.assertEqual(sr.strip_particle(w),stem,w)
    def test_repeat_after_particles(self):
        r=sr.check_pair('외국인 노동자에 박치기 22번, 공장 관리자의 최후 #형량퀴즈','노동자는 박치기를')
        self.assertEqual(r['repeated'],['노동자','박치기']);self.assertTrue(r['report_only'])
        self.assertEqual(sr.check_pair('외국인 노동자에 박치기 22번','벌금 400만?')['repeated'],[])
        self.assertEqual(sr.check_pair('#형량퀴즈 박치기','형량퀴즈')['repeated'],[])   # hashtags are not title words
    def test_eojeol_and_preview(self):
        r=sr.check_pair("층간소음에 '망치' 들면 몇 년 나옴?",'징역 몇 년\n나왔을까')
        self.assertEqual(r['thumb_eojeol'],4);self.assertTrue(any('eojeol' in i for i in r['issues']))
        self.assertFalse(r['truncated']);self.assertEqual(r['mobile_preview'],"층간소음에 '망치' 들면 몇 년 나옴?")
        long_title='전세보증금 760억 가로채고 게임에 13억 쓴 임대인, 피해자 500명… 몇 년 나왔을까? #몇년나옴'
        r=sr.check_pair(long_title,'징역 몇 년?')
        self.assertTrue(r['truncated']);self.assertEqual(r['mobile_preview'],long_title[:40])
        self.assertEqual(sr.check_pair("층간소음에 '망치' 들면 몇 년 나옴?",'벌금 300만?')['issues'],[])

class Measure(unittest.TestCase):
    def make(self,d,vf,af='sine=f=440:d=4'):
        v=Path(d)/'v.mp4'
        subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=red:size=360x640:rate=30:d=4','-f','lavfi','-i',af,
                        '-vf',vf,'-shortest','-pix_fmt','yuv420p','-c:a','aac',v],check=True);return v
    def test_setting_changes_and_loop(self):
        with tempfile.TemporaryDirectory() as d:
            # red / blue / green settings switching every 1 s, ending on red = loop seam
            v=self.make(d,"drawbox=c=blue:t=fill:enable='between(t,1,2)',drawbox=c=green:t=fill:enable='between(t,2,3)'")
            st=sr.setting_changes(v);self.assertEqual(st['n'],4);self.assertLessEqual(st['max_len'],1.25)
            self.assertLess(sr.loop_diff(v)['last'],5)
    def test_pauses_and_onset(self):
        with tempfile.TemporaryDirectory() as d:
            v=self.make(d,'null',af="sine=f=440:d=4,volume=enable='between(t,0,0.3)+between(t,1.5,2.4)':volume=0")
            self.assertAlmostEqual(sr.audio_onset(v),0.3,delta=.05)
            words=[dict(text='a',start=.3,end=1.0),dict(text='b',start=2.5,end=3.5)]
            self.assertEqual(len(sr.pauses(v,words)),1)
    def test_gate_is_report_only_and_shorts_only(self):
        with tempfile.TemporaryDirectory() as d:
            v=self.make(d,'null')
            c=r.Review(v,Path(d)/'out','shorts',[],[],[],'','',config=dict(shorts_spec=GOOD));c.out.mkdir()
            c.words=[dict(text='a',start=0,end=1)]
            g=r.shorts_rules_gate(c)
            self.assertEqual(g['status'],'ADVISORY');self.assertEqual(g['evidence']['spec_issues'],[])
            self.assertIn('loop',g['evidence']['checks'])
            self.assertTrue(r.apply_calibration({'SHORTS_RULES':g})['SHORTS_RULES']['advisory'])

if __name__=='__main__':unittest.main()
