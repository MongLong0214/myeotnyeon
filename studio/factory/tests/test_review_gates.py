"""Behavior checks for media defects and review/input binding; no external calls."""
from pathlib import Path
import copy,io,json,subprocess,sys,tempfile,unittest
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import review_gates as r
from gates import apply_cto_signoffs,finalize_review

class ReviewHarness(unittest.TestCase):
    """Review context on a temp dir; holds no tests itself."""
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.out=Path(self.tmp.name);self.video=self.out/'video.mp4';self.video.write_bytes(b'encoded input')
        self.c=r.Review(self.video,self.out,'longform',[],[],[],'','')
        self.c.duration=10;self.c.fps=30;self.c.frames=300
        self.c.media=dict(ocr_korean=True,ocr_complete=True,ocr_engine='test Korean OCR',ocr=[],shot_coverage=True,moving_shots=[0],decoded_frames=300,static_spans=[])
        # Agreed source fixtures, not a production policy override. The real
        # documents currently omit speech windows in STYLE / H14.
        style=self.out/'STYLE_VIDEO.md';checklist=self.out/'REVIEW_CHECKLIST.md'
        clauses='숏츠 7.5음절/s 이상, 문장 끝 쉼 0.12s 이하, 문장 안 쉼 0.15s 이하; 롱폼 6.2–6.6음절/s, 문장 끝 쉼 0.2s 이하, 문장 안 쉼 0.2s 이하'
        style.write_text(clauses);checklist.write_text('| H14 | owner | '+clauses+' |')
        self.pace_sources=(style,checklist)
        self.addCleanup(patch.stopall);patch.object(r,'PACE_SOURCES',self.pace_sources).start()
    def words(self,rows):
        self.c.words=[dict(text=t,start=a,end=b) for t,a,b in rows]
        self.c.asr=dict(text=' '.join(t for t,_,_ in rows))
class ReviewTests(ReviewHarness):
    def test_pace_is_format_specific(self):
        self.words([('가'*49,0,6)])
        self.assertFalse(r.c1(self.c)['evidence']['pace_pass'])
        self.c.format='shorts';self.assertTrue(r.c1(self.c)['evidence']['pace_pass'])
        self.words([('가'*38,0,6)])
        self.c.format='longform';self.assertEqual(r.c1(self.c)['status'],'PASS')
        self.c.format='shorts';self.assertEqual(r.c1(self.c)['status'],'FAIL')
    def test_sentence_and_internal_pause_limits(self):
        self.words([('가'*13+'.',0,2),('나'*13,2.2,4)])
        self.assertTrue(r.c1(self.c)['evidence']['pause_pass'])
        self.c.words[1]['start']=2.21
        self.assertFalse(r.c1(self.c)['evidence']['pause_pass'])
        self.words([('가'*13,0,2),('나'*13,2.21,4)])
        self.assertFalse(r.c1(self.c)['evidence']['pause_pass'])
    def test_updated_pace_window_still_rejects_fast_and_slow_speech(self):
        for syllables,expected in [(64,'PASS'),(70,'FAIL'),(61,'FAIL')]:
            self.words([('가'*syllables,0,10)])
            self.assertEqual(r.c1(self.c)['status'],expected)
        # Short sentence pauses have no invented minimum; >0.2s still fails.
        for gap,expected in [(.1,'PASS'),(.21,'FAIL')]:
            self.words([('가'*32+'.',0,5),('나'*32,5+gap,10)])
            self.assertEqual(r.c1(self.c)['status'],expected)
    def test_pace_sources_must_agree_and_are_bound(self):
        self.words([('가'*64,0,10)])
        self.assertEqual(r.c1(self.c)['status'],'PASS')
        self.assertTrue(all(str(p.resolve()) in self.c.inputs for p in self.pace_sources))
        checklist=self.pace_sources[1]
        checklist.write_text(checklist.read_text().replace('6.2–6.6','6.8–7.2'))
        gate=r.c1(self.c)
        self.assertEqual(gate['status'],'INPUT_MISSING');self.assertIsNone(gate['evidence']['window'])
        self.assertTrue(any('!=' in s for s in gate['evidence']['pace_policy']['issues']))
    def test_missing_owner_windows_never_fall_back_to_legacy_c1(self):
        self.pace_sources[0].write_text('Editing rhythm: base shot 2–3 s; cut only at line boundaries.')
        self.pace_sources[1].write_text('| C1 | old | 숏츠 7.5음절/s 이상. 롱폼 6.8–7.2음절/s |\n| H14 | 너무 편집감이 빨라 | 숏츠 기본 샷 2–3초 |')
        gate=r.c1(self.c)
        self.assertEqual(gate['status'],'INPUT_MISSING')
        self.assertTrue(gate['evidence']['pace_policy']['issues'])
        self.assertIsNone(gate['evidence']['window'])
    def test_end_card_padding_cannot_hide_fast_tts(self):
        text='가'*48;self.words([(text,0,6)]);self.c.duration=7
        self.c.narration=[dict(text=text,tts_text=text,start_s=0,end_s=6)]
        gate=r.c1(self.c)
        self.assertTrue(gate['evidence']['tts_pronunciation_used'])
        self.assertEqual(gate['evidence']['syllables_per_second'],8)
        self.assertFalse(gate['evidence']['pace_pass'])
    def test_shorts_verified_pronunciation_counts_asr_digits(self):
        text='가'*13+'22';self.words([(text,0,2)]);self.c.format='shorts';self.c.duration=2
        self.c.narration=[dict(text=text,tts_text='가'*13+'스물두',start_s=0,end_s=2)]
        self.c.media.update(tts_pronunciation_verified=True,final_asr_reference_agreement=1)
        self.assertEqual(r.c1(self.c)['evidence']['syllables_per_second'],8)
        self.assertTrue(r.c1(self.c)['evidence']['pace_pass'])
    def test_word_dates_and_invented_day(self):
        self.c.subtitles=[dict(text='이천십일 년 십이월',start_s=0,end_s=1)]
        self.c.facts='| F01 | 2011년 12월 기록이다. | [기사 2011-12-25](url) |'
        self.assertTrue(r.e1(self.c)['evidence']['korean_word_dates'])
        self.c.subtitles[0]['text']='2011년 12월 25일'
        self.assertTrue(r.e1(self.c)['evidence']['dates_not_in_facts'])
        self.c.subtitles[0]['text']='2011년 12월'
        self.assertEqual(r.e1(self.c)['status'],'PASS')
        self.c.subtitles[0]['text']='2011-12'
        self.assertEqual(r.e1(self.c)['status'],'FAIL')
    def test_numeric_dates_with_korean_units_are_required(self):
        self.c.facts='| F01 | 2001-12-21 |'
        for text in ['2001년 12월 21일','12월 21일','2001년 12월']:
            self.c.subtitles=[dict(text=text,start_s=0,end_s=1)]
            self.assertEqual(r.e1(self.c)['status'],'PASS',text)
        self.c.narration=[dict(text='2001년 12월 21일')]
        self.c.subtitles=[dict(text='2001-12-21',start_s=0,end_s=1)]
        self.assertEqual(r.e1(self.c)['status'],'FAIL')
        self.c.subtitles[0]['text']='2001년 12월 21일'
        self.c.media['ocr']=[dict(frame=5,boxes=[dict(text='2001-12-21')])]
        self.assertEqual(r.e1(self.c)['status'],'FAIL')
    def test_facts_files_keep_duplicate_ids_in_their_own_scope(self):
        self.c.config['fact_texts']=['| F01 | 2024-05-25 |','| F01 | 2024-08-27 |']
        self.c.subtitles=[dict(text='2024-05-25 / 2024-08-27',start_s=0,end_s=1)]
        self.assertEqual(r.e1(self.c)['evidence']['dates_not_in_facts'],[])
    def test_tts_pronunciation_uses_speech_intervals_without_sentence_pads(self):
        self.words([('가'*10+'3',0,2),('나'*10,2.25,3)])
        self.c.narration=[dict(text='가'*10+'3',tts_text='가'*10+'삼',start_s=0,end_s=2),dict(text='나'*10,tts_text='나'*10,start_s=2.25,end_s=3)]
        self.c.duration=3
        self.c.media['final_asr_reference_agreement']=1
        ev=r.c1(self.c)['evidence']
        self.assertEqual(ev['syllables'],21);self.assertEqual(ev['seconds'],2.75)
        self.assertEqual(ev['syllables_per_second_including_sentence_pauses'],7)
        self.c.media['final_asr_reference_agreement']=.98
        self.assertTrue(r.c1(self.c)['evidence']['tts_pronunciation_used'])
    def test_fact_date_columns_and_clarification_exclude_article_dates(self):
        self.c.config['fact_texts']=['| ID | 항목·심급 | 날짜·법원 | 채택 사실 | 교차 근거 |\n| C03 | 구형 | 2024-11-12 | 검찰의 구형. | 기사 2024-11-13 |\n날짜 구분: 사망일은 2024-05-25다.']
        self.c.subtitles=[dict(text='2024-11-12 / 2024-05-25',start_s=0,end_s=1)]
        self.assertEqual(r.e1(self.c)['evidence']['dates_not_in_facts'],[])
        self.c.subtitles[0]['text']='2024-11-13'
        self.assertTrue(r.e1(self.c)['evidence']['dates_not_in_facts'])
    def test_iso_and_korean_fact_forms_keep_source_dates_out(self):
        for date in ['2024-05-23','2024년 5월 23일','이천이십사년 오월 이십삼일']:
            self.c.facts=f'| ID | 채택 사실 | 근거 |\n| F01 | 군기훈련. | 기사 2024-05-24 |\n### enrich:E01\n군기훈련은 {date}에 이뤄졌다.\n귀속/범위: 보도 사실\n- [기사 2024-05-24](url)\n'
            for text,expected in [('2024년 5월 23일','PASS'),('2024년 5월 24일','FAIL')]:
                self.c.subtitles=[dict(text=text,start_s=0,end_s=1)]
                self.assertEqual(r.e1(self.c)['status'],expected,(date,text))
    def test_code_like_subtitle_dates_fail_even_when_factually_correct(self):
        self.c.facts='| F01 | 2024-05-23 |'
        for text in ['2024-05-23','2024/05/23','2024.05.23','2024_05_23','20240523']:
            self.c.subtitles=[dict(text=text,start_s=0,end_s=1)]
            gate=r.e1(self.c)
            self.assertEqual(gate['status'],'FAIL',text)
            self.assertTrue(gate['evidence']['code_like_subtitle_dates'],text)
        self.c.subtitles=[dict(text='2024년 5월 23일',start_s=0,end_s=1)]
        self.assertEqual(r.e1(self.c)['status'],'PASS')
        self.c.subtitles[0]['text']='벌금 10000000원'
        self.assertEqual(r.e1(self.c)['status'],'PASS')
        self.c.subtitles[0]['text']='2024년 5월 23일'
        self.c.media['ocr']=[dict(frame=5,boxes=[dict(text='2024-05-23',y=.85,h=.05)])]
        self.assertEqual(r.e1(self.c)['status'],'FAIL')
    def test_code_date_split_across_cues_is_still_rejected(self):
        self.c.facts='| F01 | 2024-05-23 |'
        self.c.subtitles=[dict(text='2024-05-',start_s=0,end_s=1),dict(text='23',start_s=1,end_s=2)]
        self.assertTrue(r.e1(self.c)['evidence']['code_like_subtitle_dates'])
    def test_actor_fields_and_unknown_are_not_zero_percent_fail(self):
        self.assertTrue(r.acting(dict(staging=dict(actors=[dict(role='victim',motion='fall')]))))
        self.assertFalse(r.acting(dict(staging=dict(actors=[]))))
        self.c.shots=[dict(id='S1',start_s=0,end_s=1,action='unfamiliar')]
        with patch.object(r,'character_observations',return_value=[dict(shot='S1',character_present=None,action_observed=None)]):
            gate=r.c3(self.c)
        self.assertIsNone(gate['evidence']['character_share'])
        self.assertEqual(gate['status'],'NEEDS_REVIEW')
    def test_missing_reference_is_not_a_defect(self):
        for fn in [r.a1,r.a2,r.a3,r.b1,r.b3]:
            self.assertEqual(fn(self.c)['status'],'INPUT_MISSING')
    def test_date_split_across_subtitles_and_ocr(self):
        self.c.subtitles=[dict(text='이천십일',start_s=0,end_s=1),dict(text='년 십이월',start_s=1,end_s=2)]
        self.assertTrue(r.e1(self.c)['evidence']['korean_word_dates'])
        self.c.subtitles=[dict(text='사건',start_s=0,end_s=1)]
        self.c.media['ocr']=[dict(frame=5,boxes=[dict(text='오월 이십삼일',x=.1,y=.1,w=.5,h=.1)])]
        self.assertEqual(r.e1(self.c)['status'],'FAIL')
    def test_prop_cards_cannot_count_as_characters(self):
        self.c.shots=[dict(id='S1',start_s=0,end_s=3,view='books',narrator_visible=True,motion=['parallax'])]
        # A prop view/narrator flag proves neither presence nor absence.
        with patch.object(r,'character_observations',return_value=[dict(shot='S1',character_present=None,action_observed=None)]):
            g=r.c3(self.c)
        self.assertIsNone(g['evidence']['character_share'])
        self.assertFalse(g['evidence']['character_share_pass'])
        self.assertTrue(g['evidence']['oversize_inserts'])
    def test_motion_and_non_subtitle_box(self):
        self.c.shots=[dict(id='S1',start_s=0,end_s=1,character_acting=True,subject='actor',action='run')]
        self.assertEqual(r.c3(self.c)['status'],'PASS')
        self.c.media['moving_shots']=[]
        self.assertEqual(r.c3(self.c)['status'],'FAIL')
        self.c.media['moving_shots']=[0];self.c.media['ocr']=[dict(frame=10,boxes=[dict(text='paragraph',x=.1,y=.2,w=.5,h=.1)])]
        self.assertTrue(r.c3(self.c)['evidence']['non_subtitle_text'])
    def test_structured_action_generates_c3_evidence_without_hiding_defects(self):
        self.c.shots=[dict(id='S1',start_s=0,end_s=3,action=dict(verb='달린다',**{'class':'physical_action'}),
                           staging=dict(actors=[dict(role='trainee',motion='run')]))]
        self.assertEqual(r.c3(self.c)['status'],'PASS')
        self.c.media['moving_shots']=[]
        self.assertEqual(r.c3(self.c)['status'],'FAIL')
        self.c.media['moving_shots']=[0]
        self.c.shots[0]['action']={'class':'books'}
        gate=r.c3(self.c)
        self.assertEqual(gate['status'],'FAIL');self.assertTrue(gate['evidence']['oversize_inserts'])
    def test_cold_open_question_markers_and_cadence(self):
        self.c.duration=90
        self.c.script='[COLD_OPEN @ 0]\n[CENTRAL_QUESTION @ 4]\n[CLIFFHANGER @ 35]\n[CLIFFHANGER @ 70]'
        self.words([('말',t,t+.1) for t in [0,4,35,70]])
        with patch.object(r,'sheet',return_value=[]):
            g=r.c2(self.c);self.assertEqual(g['review_state'],'NEEDS_REVIEW')
            self.c.script=self.c.script.replace('@ 4','@ 11')
            self.assertFalse(r.c2(self.c)['evidence']['central_question_pass'])
            self.c.script=self.c.script.replace('@ 11','@ 4');self.c.media['static_spans']=[[1,3]]
            self.assertEqual(r.c2(self.c)['review_state'],'DECIDED')
    def test_cut_must_be_at_clause_not_arbitrary_word_end(self):
        self.c.shots=[dict(id='S1'),dict(id='S2')]
        self.words([('달렸지만',0,.95),('아직',1,1.5),('끝났습니다.',1.5,2)])
        with patch.object(r,'cut_sheet',return_value=dict(all_cut_frames=[30],required_matches=['S1','S2'])):
            self.assertEqual(r.d2(self.c)['review_state'],'NEEDS_REVIEW')
        with patch.object(r,'cut_sheet',return_value=dict(all_cut_frames=[45],required_matches=['S1','S2'])):
            self.assertEqual(r.d2(self.c)['review_state'],'DECIDED')
    def test_cut_inside_clause_pause_has_zero_distance(self):
        self.c.shots=[dict(id='S1'),dict(id='S2')]
        self.words([('끝났습니다.',0,1.56),('다음',1.95,2.5)])
        with patch.object(r,'cut_sheet',return_value=dict(all_cut_frames=[57],required_matches=['S1','S2'])):
            gate=r.d2(self.c)
        self.assertEqual(gate['evidence']['cuts'][0]['nearest_clause_delta_s'],0)
        self.assertEqual(gate['status'],'NEEDS_REVIEW')
    def test_advisory_fail_does_not_decide_ready(self):
        policy=self.out/'gate_calibration.json';r.write_json(policy,dict(false_fail_counts={'C1':1,'D2':1}))
        with patch.object(r,'HERE',self.out):
            baseline=self.baseline();baseline['C1']=r.result(False,{})
            first=finalize_review(self.c,baseline)
            signs={k:self.signature(first['input_sha256']) for k in r.SIGNED if k!='D2'}
            signed=finalize_review(self.c,self.baseline() | {'C1':r.result(False,{})},dict(cto_signoffs=signs))
        self.assertTrue(signed['ready']);self.assertTrue(signed['gates']['C1']['advisory'])
    def test_jump_direction_establishing_and_unknown(self):
        base=dict(subject='A',set='room',type='wide',screen_direction='right',axis_side='left')
        self.c.shots=[dict(base,id='S1',start_s=0,end_s=1),dict(base,id='S2',start_s=1,end_s=2)]
        self.assertTrue(r.d3(self.c)['evidence']['jump_cuts'])
        self.c.shots[1].update(subject='B',type='close-up',axis_side='right')
        self.assertTrue(r.d3(self.c)['evidence']['screen_direction_violations'])
        self.c.shots[0]['type']='close-up'
        self.assertTrue(r.d3(self.c)['evidence']['missing_establishing'])
        del self.c.shots[1]['screen_direction']
        self.assertTrue(r.d3(self.c)['evidence']['missing_metadata'])
    def test_high_ssim_catches_jump_even_with_different_metadata(self):
        self.c.shots=[dict(id='A',start_s=0,end_s=1,set='room',type='wide',subject='A',screen_direction='right',axis_side='left'),
                      dict(id='B',start_s=1,end_s=2,set='room',type='close-up',subject='B',screen_direction='right',axis_side='left')]
        self.c.media['cut_ssim']={'30':.99}
        self.assertTrue(r.d3(self.c)['evidence']['jump_cuts'])
    def test_structured_set_does_not_crash_or_hide_jump_direction_or_unknown(self):
        base=dict(set=dict(description='연병장',actual_layout_reconstructed=False),screen_direction='right',axis_side='left')
        self.c.shots=[dict(base,id='S1',start_s=0,end_s=1,type='wide',subject='A'),
                      dict(base,id='S2',start_s=1,end_s=2,type='close-up',subject='B')]
        self.assertEqual(r.d3(self.c)['status'],'PASS')
        self.c.shots[1].update(type='wide',subject='A')
        gate=r.d3(self.c)
        self.assertEqual(gate['status'],'FAIL');self.assertTrue(gate['evidence']['jump_cuts'])
        self.c.shots[1].update(type='close-up',subject='B',axis_side='right')
        gate=r.d3(self.c)
        self.assertEqual(gate['status'],'FAIL');self.assertTrue(gate['evidence']['screen_direction_violations'])
        self.c.shots[0]['set']={}
        gate=r.d3(self.c)
        self.assertEqual(gate['status'],'FAIL');self.assertTrue(gate['evidence']['missing_metadata'])
    def test_incomplete_ocr_cannot_pass_dates(self):
        self.c.subtitles=[dict(text='2011년 12월',start_s=0,end_s=1)]
        self.c.facts='| F01 | 2011년 12월이다. |'
        self.c.media['ocr_complete']=False
        self.assertEqual(r.e1(self.c)['status'],'FAIL')
    def signature(self,h):return dict(role='CTO',name='reviewer',reason='reviewed each image',input_sha256=h)
    def test_signatures_cannot_override_auto_or_producer_match(self):
        g={'C1':r.result(False,{}),'D2':r.pending(dict(required_matches=['S1','S2']))}
        sign=self.signature('hash')
        apply_cto_signoffs(g,'hash',dict(C1=sign,D2=dict(sign,matches={'S1':'MATCH'})))
        self.assertEqual(g['C1']['status'],'FAIL');self.assertEqual(g['D2']['review_state'],'NEEDS_REVIEW')
        apply_cto_signoffs(g,'hash',dict(D2=dict(sign,matches={'S1':'MATCH','S2':'MATCH'})))
        self.assertEqual(g['D2']['review_state'],'CTO_SIGNED')
    def test_reads_as_mismatch_blocks_signature(self):
        g={'B4':r.pending(dict(required_reads_as={'S1':'군장'}))};sign=self.signature('hash')
        apply_cto_signoffs(g,'hash',dict(B4=dict(sign,reads_as={'S1':'가방'})))
        self.assertEqual(g['B4']['review_state'],'NEEDS_REVIEW')
    def baseline(self):
        return {k:r.pending({}) if k in r.SIGNED else r.result(True,{}) for k in r.ITEMS}
    def test_input_and_evidence_change_revoke_signoff(self):
        self.c.bind(self.video);image=self.out/'evidence.jpg';image.write_bytes(b'frame');self.c.artifacts[str(image)]=r.digest(image)
        first=finalize_review(self.c,self.baseline())
        signs={k:self.signature(first['input_sha256']) for k in r.SIGNED}
        signed=finalize_review(self.c,self.baseline(),dict(cto_signoffs=signs))
        self.assertTrue(signed['ready']);self.assertIn(r.LIMIT,signed['limits'])
        image.write_bytes(b'other frame')
        after=finalize_review(self.c,self.baseline(),dict(cto_signoffs=signs))
        self.assertFalse(after['ready']);self.assertNotEqual(after['input_sha256'],first['input_sha256'])
        self.assertEqual(after['gates']['D2']['review_state'],'NEEDS_REVIEW')
        self.assertEqual(after['gates']['input_integrity']['status'],'FAIL')
    def test_final_encoded_static_span_measurement(self):
        self.video.unlink()
        subprocess.run(['ffmpeg','-v','error','-f','lavfi','-i','color=c=blue:s=160x90:r=10:d=2','-c:v','libx264','-y',str(self.video)],check=True)
        self.c.shots=[dict(id='S1',start=0,end=20)]
        self.c.normalize();r.scan_frames(self.c)
        self.assertEqual(self.c.media['decoded_frames'],20)
        self.assertTrue(self.c.media['static_spans']);self.assertEqual(self.c.media['moving_shots'],[])
        self.assertTrue(self.c.media['frame_pages'])
    @unittest.skipUnless(sys.platform=='darwin' and (r.HERE/'.ocr_vision').exists(),'Local Korean Vision required')
    def test_one_frame_korean_date_outside_subtitles_is_caught(self):
        from PIL import Image,ImageDraw,ImageFont
        import numpy as np
        frames=[]
        for n in range(10):
            im=Image.new('RGB',(640,360),(25,30,40))
            if n==5:ImageDraw.Draw(im).text((35,55),'이천십일 년 십이월',font=ImageFont.truetype(r.FONT,32),fill='white')
            frames.append(np.asarray(im))
        self.video.unlink()
        subprocess.run(['ffmpeg','-v','error','-f','rawvideo','-pix_fmt','rgb24','-s','640x360','-r','10','-i','-','-c:v','libx264','-pix_fmt','yuv420p','-y',str(self.video)],input=np.stack(frames).tobytes(),check=True)
        self.c.shots=[dict(id='S1',start=0,end=10)];self.c.subtitles=[dict(text='사건',start_s=0,end_s=1)]
        self.c.normalize();r.scan_frames(self.c,False);r.ocr_frames(self.c)
        self.assertTrue(self.c.media['ocr_complete'])
        hits=r.e1(self.c)['evidence']['korean_word_dates']
        self.assertTrue(any(x['source']=='OCR' and x['time']==.5 for x in hits),hits)

if __name__=='__main__':unittest.main()
