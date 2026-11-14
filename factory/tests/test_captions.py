"""Shared subtitle splitter rules (factory/lib/captions.py); no audio or network."""
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lib import captions as cap

def words(text,start=0.0,step=0.3,gaps=None):
    """One token per space-separated word; gaps={index: extra seconds after that word}."""
    out=[];t=start
    for i,w in enumerate(text.split()):
        out.append(dict(text=w,start=t,end=t+step*.9));t+=step+(gaps or {}).get(i,0)
    return out

class Splitter(unittest.TestCase):
    def test_sentence_end_breaks_cue(self):
        cues=cap.split(words('범인은 도망쳤습니다. 경찰이 쫓았습니다.'))
        self.assertEqual([c['text'] for c in cues],['범인은 도망쳤습니다.','경찰이 쫓았습니다.'])
    def test_pause_breaks_only_at_phrase_end(self):
        # 0.4 s pause after a case-marked phrase: new cue.
        cues=cap.split(words('현장에서 권총이 발사됐고 과장이 숨졌습니다.',gaps={2:.4}))
        self.assertEqual(cues[0]['text'],'현장에서 권총이 발사됐고')
        # Same pause after a modifier (검은 | 그랜저가) does not start a cue.
        cues=cap.split(words('순간 검은 그랜저가 막았습니다.',gaps={1:.4}))
        self.assertEqual(len(cues),1)
    def test_silencedetect_pause_counts_even_when_words_touch(self):
        ws=words('경찰은 추적했고 범인은 달아났습니다.',step=.3)
        for a,b in zip(ws,ws[1:]):a['end']=b['start']  # Whisper stretches words over the pause
        cues=cap.split(ws,silences=[(0.5,0.8)])
        self.assertEqual(cues[0]['text'],'경찰은 추적했고')
        self.assertEqual(len(cap.split(ws)),1)
    def test_number_and_unit_never_split(self):
        text='빼앗긴 가방 하나에는 정확히 3억 원이 들어 있었다고 수사기관은 밝혔습니다.'
        for line_max in range(8,19):
            cues=cap.split(words(text),line_max=line_max)
            for c in cues:
                for line in c['lines']:
                    self.assertFalse(line.endswith('3억'),(line_max,c['lines']))
            self.assertEqual(cap.lint(cues,99),[])
    def test_date_stays_in_one_cue(self):
        cues=cap.split(words('은행 사건보다 앞선 2001년 10월 15일 자정 무렵으로 돌아갑니다.'))
        self.assertTrue(any('2001년' in c['text'] and '15일' in c['text'] for c in cues),[c['text'] for c in cues])
    def test_never_starts_with_particle(self):
        ws=words('공범 B 가 범행을 인정했고 C 는 부인했습니다.')
        cues=cap.split(ws,line_max=6)
        self.assertEqual([i for i in cap.lint(cues,99) if i['code']=='starts_with_particle'],[])
        self.assertTrue(all(not cap.is_particle(c['tokens'][0]) for c in cues))
    def test_two_lines_max_and_line_length(self):
        text='그래서 여기서는 총성과 섬광을 세어 횟수를 만들어내지 않고 확인된 사실만 차례대로 설명하겠습니다.'
        cues=cap.split(words(text),line_max=18)
        self.assertGreater(len(cues),1)
        for c in cues:
            self.assertLessEqual(len(c['lines']),2)
            self.assertTrue(all(len(l)<=18 for l in c['lines']),c['lines'])
    def test_balanced_wrap_and_orphan_pull(self):
        lines=[' '.join(t['text'] for t in l) for l in cap.wrap(words('법원은 학대치사를 인정했습니다.'),16)]
        self.assertEqual(lines,['법원은 학대치사를','인정했습니다.'])
        lines=[' '.join(t['text'] for t in l) for l in cap.wrap(words('가장 오래 걸린 수사 끝에 잡힌 범인 B'),16)]
        self.assertNotEqual(len(lines[-1].split()),1,lines)
    def test_hold_rule(self):
        cues=cap.split(words('짧다. 다음 문장입니다.',step=.3,gaps={0:3}))
        self.assertAlmostEqual(cues[0]['end']-cues[0]['start'],1.8)      # max(1.8, speech+0.6)
        cues=cap.split(words('짧다. 다음 문장입니다.',step=.3,gaps={0:.5}))
        self.assertAlmostEqual(cues[0]['end'],cues[1]['start'])         # next cue starts first
        long=cap.split(words('이 문장은 꽤 길게 읽히는 한 줄짜리 설명입니다.',step=.4))
        self.assertAlmostEqual(long[0]['end'],long[0]['speech_end']+.6)
    def test_whisper_continuations_merge_and_output_shapes(self):
        raw={'segments':[{'words':[dict(word=' 3',start=0,end=.2),dict(word='억',start=.2,end=.4),dict(word=' 원이',start=.4,end=.7),dict(word=' 사라졌다.',start=.7,end=1.2)]}]}
        words=cap.load_words(raw,offset=10)
        self.assertEqual([t['text'] for t in words],['3억','원이','사라졌다.'])
        self.assertEqual(words[0]['start'],10)
        cues=cap.split(words)
        self.assertEqual(cap.to_longform(cues),[dict(start=10,end=11.8,text='3억 원이 사라졌다.')])
        self.assertEqual(cap.to_shorts(cues,30),[dict(from_=300,to=354,text='3억 원이 사라졌다.')])

class KoreanBreaks(unittest.TestCase):
    """Line and cue breaks never split a Korean grammatical unit (LF3 owner review, v7e subtitles)."""
    BAD=[  # (sentence, word before a forbidden break, word after it)
     ('그 컴퓨터에 계속 숨어 있었다는 증거는 없어요. 실제로 돈이 빠져나가기 시작한 건, 10월 30일 새벽입니다.','시작한','건,'),
     ('그 컴퓨터에 계속 숨어 있었다는 증거는 없어요.','숨어','있었다는'),
     ('표적은 바이낸스 지갑 관리팀의 한 엔지니어.','지갑','관리팀의'),
     ('정상 구직 플랫폼이었고, B의 프로필엔 바이낸스 경력이 적혀 있었어요.','바이낸스','경력이'),
     ('상대는 자신을 프로젝트 책임자라고 소개합니다.','프로젝트','책임자라고'),
     ('1차 면접엔 인사 담당자, 2차 면접엔 회사 대표라는 사람이 나옵니다.','대표라는','사람이'),
     ('1차 화상 면접에선 사진과 영상이 올라간 SNS 계정까지 보여 주며 믿음을 쌓죠.','영상이','올라간'),
     ('1차 화상 면접에선 사진과 영상이 올라간 SNS 계정까지 보여 주며 믿음을 쌓죠.','올라간','SNS'),
     ('채팅 앱으로 한 2차 면접 끝, 과제가 옵니다.','면접','끝,'),
     ('10월 20일. 회사 조사로는, 공격자가 B의 컴퓨터와 회사 내부 AI 도구를 발판으로 삼습니다.','내부','AI'),
     ('A의 컴퓨터엔, 회사 시스템에 프로그램을 배포할 수 있는 권한이 들어 있었어요.','배포할','수'),
     ('회사 보고서로는, 공격자가 C의 컴퓨터에 접속해, A에게서 훔친 로그인 정보를 씁니다.','로그인','정보를'),
     ('공격자는 정상 출금 절차 밖에서 거래를 만듭니다.','절차','밖에서'),
     ('보도 환산액을 20분으로 단순히 나누면 1초에 70억원꼴. 실제 초당 유출 속도는 아닌, 규모 비유예요.','속도는','아닌,'),
     ('출금을 막았는데, 왜 바로 끝나지 않았을까요?','왜','바로'),
     ("회사 설명으로는, 이더리움의 '대리 권한' 기능으로 공격자 프로그램에 권한이 넘어가 있었어요.",'공격자','프로그램에'),
     ('그 권한은 이미 블록체인 위에 있었습니다.','블록체인','위에'),
     ('이제 돈을 쫓는 추적이 시작됩니다.','쫓는','추적이'),
     ('비트코인과 이더리움엔, 같은 방식으로 동결할 발행사가 없어요.','같은','방식으로'),
     ('블록체인 분석업체 분석으론, 대부분이 약 20분 안에 움직였죠.','20분','안에'),
     ('설치가 시작되는 순간, 숨은 악성코드가 실행됩니다. 회사 보안 프로그램은 잡지 못했어요.','잡지','못했어요.'),
    ]
    def breaks(self,cues):
        """All (left word, right word) pairs split by a line break or a cue break."""
        out=[];flat=[]
        for c in cues:
            lines=[l.split() for l in c['text'].split('\n')]
            for a,b in zip(lines,lines[1:]):out.append((a[-1],b[0]))
            flat.append(lines)
        for a,b in zip(flat,flat[1:]):out.append((a[-1][-1],b[0][0]))
        return out
    def test_owner_examples_never_split(self):
        for text,a,b in self.BAD:
            for lm in (20,22):  # long-form lines (Captions full layout fits ~28 Korean chars)
                cues=cap.split(words(text),line_max=lm)
                self.assertNotIn((a,b),self.breaks(cues),(lm,[c['text'] for c in cues]))
    def test_owner_examples_with_pauses(self):
        # a 0.3 s breath right at the forbidden point must not start a new cue there either
        for text,a,b in self.BAD:
            ws=text.split();i=next(k for k in range(len(ws)-1) if ws[k]==a and ws[k+1]==b)
            cues=cap.split(words(text,gaps={i:.3}),line_max=22)
            self.assertNotIn((a,b),self.breaks(cues),[c['text'] for c in cues])
    def test_choppy_cues_merge(self):
        text='바이낸스는 동결하거나 가로막은 자산을 합쳐 약 28억5000만 달러라고 밝혔습니다.'
        cues=cap.split(words(text,gaps={1:.3,3:.3}),line_max=22)
        self.assertTrue(all(len(c['tokens'])>1 for c in cues),[c['text'] for c in cues])
        self.assertNotIn(('가로막은','자산을'),self.breaks(cues))
        self.assertNotIn(('동결하거나','가로막은'),self.breaks(cues))
    def test_no_scrap_cue_for_short_adverb_clause(self):
        cues=cap.split(words('그렇다고 영원히 처벌할 수 없다는 뜻은 아니에요.'))
        self.assertTrue(all(len(c['text'].replace(chr(10),' '))>=6 for c in cues),[c['text'] for c in cues])
    def test_review_round2_rules(self):
        # date, coordination at a cue end, subject + relative clause (CTO review of v8)
        self.assertEqual(cap.bond('10월','20일까지의'),3)
        self.assertEqual(cap.bond('대부분이','움직인'),3)
        self.assertGreaterEqual(cap.bond('직무와','동료'),2)
        for c in cap.split(words('회사는 컴퓨터와 로그인 정보를 바꿨지만, A의 직무와 동료 정보는 이미 노출됐다고 설명합니다.'),line_max=22):
            self.assertFalse(c['text'].endswith(('와','과')),c['text'])
    def test_prefers_comma_break(self):
        lines=[' '.join(t['text'] for t in l) for l in cap.wrap(words('회사 설명으로는, 채팅 앱으로 한 2차 면접 끝에 과제가 옵니다.'),18)]
        self.assertEqual(lines[0],'회사 설명으로는,')
    def test_bond_unit(self):
        self.assertEqual(cap.bond('시작한','건,'),3);self.assertEqual(cap.bond('있었다는','증거는'),3)
        self.assertEqual(cap.bond('없어요.','실제로'),0);self.assertEqual(cap.bond('끝,','과제가'),0)
        self.assertEqual(cap.bond('주며','믿음을'),0)

class Wiring(unittest.TestCase):
    ASR=[dict(text=t,start=a,end=b) for t,a,b in [('삼억',0,.4),('원이',.4,.7),('사라졌다.',.7,1.3),('범인은',2,2.4),('도망쳤다.',2.4,3.0)]]
    def test_align_text_keeps_script_words_and_digits(self):
        toks=cap.align_text('3억 원이 사라졌다.',self.ASR[:3],(0,1.3))
        self.assertEqual([t['text'] for t in toks],['3억','원이','사라졌다.'])
        self.assertAlmostEqual(toks[0]['start'],0);self.assertLessEqual(toks[0]['end'],toks[1]['start']+1e-9)
    def test_longform_cues_stay_inside_their_sentence(self):
        caps=cap.longform_from_sentences([dict(id='L1',start=0,end=1.3,display_text='3억 원이 사라졌다'),
                                          dict(id='L2',start=2,end=3,display_text='범인은 도망쳤다.')],self.ASR)
        self.assertEqual([(c['sentence_id'],c['text']) for c in caps],[('L1','3억 원이 사라졌다'),('L2','범인은 도망쳤다.')])
        self.assertAlmostEqual(caps[0]['end'],1.9)   # max(1.8, speech 1.3 + 0.6), before the next cue at 2.0
    def test_shorts_resplit_keeps_every_word(self):
        rows=[dict(from_=0,to=39,text='3억 원이'),dict(from_=39,to=60,text='사라졌다.'),dict(from_=60,to=90,text='범인은 도망쳤다.')]
        new=cap.shorts_from_subtitles(rows,self.ASR,fps=30)
        self.assertEqual(' '.join(r['text'] for r in new).split(),' '.join(r['text'] for r in rows).split())
        self.assertEqual(new[0],dict(from_=0,to=60,text='3억 원이 사라졌다.'))
    def test_prepare_scripts_use_shared_splitter_with_legacy_escape(self):
        root=Path(__file__).resolve().parents[2]
        for f,call in [(root/'factory'/'prepare_v52.py','shorts_from_subtitles'),(root/'production/lf_toon/prepare_lf2_full.py','longform_from_sentences')]:
            src=f.read_text();self.assertIn(call,src);self.assertIn("CAPTION_SPLITTER','shared')!='legacy'",src)
        # prepare_v52 never writes into an existing output (packaged Shorts stay byte-identical).
        self.assertIn('mkdir(exist_ok=False)',(root/'factory'/'prepare_v52.py').read_text())

if __name__=='__main__':unittest.main()
