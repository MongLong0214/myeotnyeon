"""Behavioral regression checks for release-blocking mistakes."""
import copy,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import numpy as np
from gates import number_gate,title_gate,empty_panel_gate,demand_gate
from short import W,load,episode,new_dir,seal

class Gates(unittest.TestCase):
    def test_versioned_package_and_failed_run_has_no_ready(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);(root/'upload').mkdir()
            with patch('short.W',root):
                first=new_dir('q013',16);(first/'keep').write_text('original')
                second=new_dir('q013',16)
                self.assertNotEqual(first,second)
                self.assertEqual((first/'keep').read_text(),'original')
                (second/'READY').write_text('stale')
                seal(second,dict(ready=False,gates={'build':dict(status='FAIL')}))
                self.assertFalse((second/'READY').exists())
    def test_reservation_owner_and_published_video_identity(self):
        # Reservation semantics must not depend on today's mutable upload ledger.
        ledger=dict(entries=[dict(no=13,qid='q013',state='published',video_id='old13'),
                             dict(no=15,qid='q014',state='published',video_id='old15'),
                             dict(no=16,qid='q013',state='reserved')])
        for n,q in [(13,'q013'),(15,'q014'),(16,'q014')]:
            self.assertEqual(number_gate(n,q,dict(badge=n,endCard=n,cover=n),ledger=ledger)['status'],'FAIL')
        self.assertEqual(number_gate(16,'q013',dict(badge=16,endCard=16,cover=16),ledger=ledger)['status'],'PASS')
        for state in ('published','scheduled'):
            ledger=dict(entries=[dict(no=15,qid='q014',state=state,video_id='same')])
            for identity,expected in [(None,'FAIL'),('other','FAIL'),('same','PASS')]:
                self.assertEqual(number_gate(15,'q014',dict(badge=15,endCard=15,cover=15),ledger,identity)['status'],expected)
    def test_number_props_must_agree(self):
        unused=dict(entries=[])
        self.assertEqual(number_gate(20,'q013',dict(badge=20,endCard=21,cover=20),unused)['status'],'FAIL')
        self.assertEqual(number_gate(20,'q013',dict(badge=20,endCard=20,cover=20),unused)['status'],'PASS')
    def test_fresh_numeric_units_normalize_without_changing_words(self):
        from fresh import normalizer
        norm=normalizer(episode('q011'))
        self.assertEqual(norm('약 1만 1천 미터 상공'),norm('약 11,000m 상공'))
        self.assertEqual(norm('약 1만 1천 미터 상공'),norm('약11000m상공'))
        self.assertNotEqual(norm('징역 4개월'),norm('징역 5개월'))
        self.assertNotEqual(norm('문은 열리지 않았습니다'),norm('문이 열렸습니다'))
    def test_title_prefix_and_wrong_suffix_or_length(self):
        good='[제목]\n사건, 몇 년 나왔을까? #몇년나옴\n'
        self.assertEqual(title_gate(good)['status'],'PASS')
        for title in [good.replace('사건','형량 퀴즈 #16 · 사건'),good.replace('#몇년나옴','#shorts'),good.replace('사건','가'*100)]:
            self.assertEqual(title_gate(title)['status'],'FAIL')
    def test_stamp_only_paper_is_not_illustration(self):
        doc=dict(cues=[dict(id='C2',scene='incident',from_=61,fromX=61,dur=3,p=dict(set='paper'))]);doc['cues'][0]['from']=doc['cues'][0].pop('from_')
        paper=np.full((3,480,270,3),230,np.uint8);paper[:,160:200,160:220]=25
        with patch('gates.decode',side_effect=[paper,paper]),patch('gates.sha',return_value='template'):
            self.assertEqual(empty_panel_gate('v','empty',doc)['status'],'FAIL')
        art=paper.copy();art[:,220:300,40:120]=60
        with patch('gates.decode',side_effect=[art,paper]),patch('gates.sha',return_value='template'):
            self.assertEqual(empty_panel_gate('v','empty',doc)['status'],'PASS')
    def test_swapped_demand_and_sentence(self):
        ep=episode('q013');doc=load(W/'episodes/quiz/q013/v52_n16/render_n16.json');audio=load(W/'episodes/quiz/q013/v52/audio.json')
        self.assertEqual(demand_gate(ep,doc,audio,'q013')['status'],'PASS')
        bad=copy.deepcopy(doc);reveal=next(c for c in bad['cues'] if c['scene']=='reveal');reveal['p']['lines']=['징역 1년']
        self.assertEqual(demand_gate(ep,bad,audio,'q013')['status'],'FAIL')
        bad=copy.deepcopy(audio)
        for line in bad['items']:
            if line['cue']=='C5':line['text']=line['text'].replace('벌금 400만 원','징역 1년').replace('구형','선고')
        self.assertEqual(demand_gate(ep,doc,bad,'q013')['status'],'FAIL')

if __name__=='__main__':unittest.main()
