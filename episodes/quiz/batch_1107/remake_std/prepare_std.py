"""Case-specific remake using the shipped std_v3 audio, caption and gate path."""
from pathlib import Path
import json,hashlib,math,re,subprocess,sys
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly
W=Path(__file__).resolve().parents[4];D=Path(__file__).parent
sys.path.insert(0,str(W/'factory'))
from fresh import trim
def dump(p,x):Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
SPECS={
'q004':dict(kind='snack',candidate='V2-11',rank=None,title='450원 초코파이가 형사재판…1,050원의 결말은?',headline='450원 간식이 법정에',question='최종 판결은?',choices=['벌금 5만 원','선고유예','무죄'],correct=2,answer='무죄',answer_label='항소심 선고 · 확정',answer_detail='검찰 상고 포기',court='전주지법 항소심 2025년 11월 27일 · 검찰 상고 포기로 무죄 확정 보도 2025년 12월 2일',date='2025년 11월 27일',next='q005',reason='소액 간식이 형사재판으로 이어진 공분. owner 11-07의 명시적 재제작 대상. 기존 사용으로 RANKED 제외됐지만 새 소재 선택이 아닌 승인된 교체 작업. YouTube·네이버 수요 원본을 보존.',lines=[
('snack','사백오십 원짜리 초코파이가 형사재판까지 갔습니다.','450원짜리 초코파이가\n형사재판까지 갔습니다.'),
('amount','커스터드 육백 원까지, 합쳐서 천오십 원어치입니다.','커스터드 600원까지,\n합쳐서 1,050원어치입니다.'),
('first','일심은 절도죄로 벌금 오만 원을 선고했습니다.','1심은 절도죄로\n벌금 5만 원을 선고했습니다.'),
('claim','피고인은 먹어도 된다는 말을 들었다고 했습니다.','피고인은 먹어도 된다는\n말을 들었다고 했습니다.'),
('evidence','동료들도 간식을 나눠 먹던 관행을 진술했습니다.','동료들도 간식을 나눠 먹던\n관행을 진술했습니다.'),
('factor','항소심 쟁점은 훔칠 고의가 있었냐는 겁니다.','항소심 쟁점은\n훔칠 고의가 있었냐는 겁니다.'),
('choices','최종 판결은 벌금일까요, 선고유예일까요, 무죄일까요? 댓글로 골라보세요.','최종 판결은 벌금일까요,\n선고유예일까요, 무죄일까요? 댓글로 골라보세요.'),
('answer','항소심 무죄. 검찰 상고 포기로 확정됐습니다.','항소심 무죄. 검찰\n상고 포기로 확정됐습니다.'),
('next','다음 판결도 맞혀보세요. 구독.','다음 판결도 맞혀보세요.\n구독.')]),
'q005':dict(kind='forklift',candidate='V2-01',rank=None,title='일 못한다며 사람 묶어 지게차로 10m…징역 몇 년?',headline='사람 묶어 지게차로',question='1심 형량은?',choices=['벌금형','집행유예','징역 실형'],correct=1,answer='징역 1년',answer_label='1심 선고',answer_detail='집행유예 2년 · 사회봉사 180시간',court='광주지법 형사4단독 1심 · 2026년 5월 27일. 후속 항소심·확정 결과 미확인',date='2026년 5월 27일',next='q004',reason='노동자를 화물처럼 결박해 들어 올린 행위와 1심 집행유예 사이의 공분. owner 11-07 명시적 재제작 대상. 부유함·매수·합의금·정치 개입 등 미확인 원인을 암시하지 않음. 기존 사용으로 RANKED 제외된 교체 사례이며 수요 원본 보존.',lines=[
('lift','노동자를 묶어 지게차로 들어 올렸습니다.','노동자를 묶어 지게차로\n들어 올렸습니다.'),
('move','스리랑카 출신 동료를 약 십 미터 끌고 다녔습니다.','스리랑카 출신 동료를\n약 10m 끌고 다녔습니다.'),
('reason','벽돌 포장 업무가 서툴다는 이유였습니다.','벽돌 포장 업무가\n서툴다는 이유였습니다.'),
('harm','법원은 모멸감과 정신적 고통을 지적했습니다.','법원은 모멸감과 정신적\n고통을 지적했습니다.'),
('recovery','반성, 합의, 처벌을 원치 않는 점도 참작했습니다.','반성, 합의, 처벌을 원치 않는\n점도 참작했습니다.'),
('factor','합의했다고 형량이 자동으로 정해지는 건 아닙니다.','합의했다고 형량이\n자동으로 정해지는 건 아닙니다.'),
('choices','일심 선고는 벌금일까요, 집행유예일까요, 실형일까요? 댓글로 골라보세요.','1심 선고는 벌금일까요,\n집행유예일까요, 실형일까요? 댓글로 골라보세요.'),
('answer','일심 선고. 징역 일 년, 집행유예 이 년, 사회봉사 백팔십 시간.','1심 선고. 징역 1년,\n집행유예 2년, 사회봉사 180시간.'),
('next','다음 판결도 맞혀보세요. 구독.','다음 판결도 맞혀보세요.\n구독.')])}

def main(q):
 from supertonic import TTS
 c=dict(SPECS[q],qid=q,number=None);p=W/'upload/pkg'/f'{q}_std';p.mkdir(exist_ok=True);(p/'audio').mkdir(exist_ok=True)
 src=[s for s in json.loads((D/'sources.json').read_text()) if s['id'].startswith(q.upper())]
 assert len(src)>=2;dump(p/'research.json',dict(sources=src,checked_at='2026년 11월 7일',stage=c['court']))
 tts=TTS(auto_download=False,intra_op_num_threads=1,inter_op_num_threads=1);voice=tts.get_voice_style('M1');utterances=[];waves=[];at=0
 for i,(mode,text,shown) in enumerate(c['lines']):
  f=p/'audio'/f'{i:02}.wav';key=f.with_suffix('.text');syll=len(re.findall('[가-힣]',text))
  if not f.exists() or not key.exists() or key.read_text()!=text:
   speed=1.35
   for take in range(8):
    raw,_=tts.synthesize(text,voice_style=voice,lang='ko',speed=speed,total_steps=16,silence_duration=.20)
    x=resample_poly(trim(np.asarray(raw,np.float32).reshape(-1),44100),160,147).astype(np.float32);rate=syll/(len(x)/48000)
    if 7.8<=rate<=8.6:break
    speed=min(2.,max(.7,speed*math.sqrt(8.2/rate)))
   assert rate>=7.5,(q,i,rate);sf.write(f,x,48000,subtype='PCM_24');key.write_text(text)
  x,sr=sf.read(f,dtype='float32');assert sr==48000;frames=math.ceil(len(x)/1600)
  # Complete lines define every cut; selection is the longest deliberate hold.
  frames=114 if mode=='choices' else 45 if mode=='next' else max(frames,63)
  if len(x)>frames*1600 or mode=='choices':
   fixed=f.with_name(f.stem+'_fit.wav');target=(frames-1)*1600 if mode=='choices' else frames*1600
   subprocess.run(['ffmpeg','-v','error','-y','-i',str(f),'-af',f'atempo={len(x)/target}',str(fixed)],check=True);x,_=sf.read(fixed,dtype='float32')
  active=min(len(x),frames*1600)/48000;x=np.pad(x[:frames*1600],(0,max(0,frames*1600-len(x))))
  utterances.append(dict(id=f'S{i+1}',mode=mode,text=text,tts_text=text,shown=shown,from_frame=at,dur=frames,start_s=at/30,end_s=(at+frames)/30,syllables=syll,sps=syll/active,active_seconds=active,file=str(f.relative_to(W)),sha256=sha(f)));waves.append(x);at+=frames
  print(q,mode,frames,round(syll/active,2),flush=True)
 assert 600<=at<=900,(q,at)
 c.update(n=at,duration=at/30,utterances=utterances,answer_frame=utterances[-2]['from_frame'],choice_frame=utterances[-3]['from_frame'],cta_frame=utterances[-1]['from_frame'])
 sf.write(p/'raw.wav',np.concatenate(waves),48000,subtype='PCM_24');subprocess.run(['ffmpeg','-v','error','-y','-i',str(p/'raw.wav'),'-af','loudnorm=I=-14:TP=-1.5:LRA=11','-ar','48000','-ac','2',str(p/'mix_master.wav')],check=True)
 dump(p/'case.json',c);dump(p/'audio.json',dict(items=utterances,reference=' '.join(u['text'] for u in utterances),engine='Supertonic 3 M1'));dump(p/'recipe.json',dict(qid=q,number=None,from_scratch=True,template='q013 v3 / std_v3 11-07',no_upload=True))
 mappings={
 'q004':[['Q004_JOONGANG','Q004_KHAN_FINAL','Q004_KOOKMIN_FINAL'],['Q004_JOONGANG','Q004_KHAN_FINAL','Q004_KOOKMIN_FINAL'],['Q004_JOONGANG','Q004_KBS_FINAL','Q004_KHAN_FINAL'],['Q004_JOONGANG','Q004_KHAN_FINAL'],['Q004_JOONGANG','Q004_KOOKMIN_FINAL'],['Q004_JOONGANG','Q004_KHAN_FINAL'],[],['Q004_KHAN_FINAL','Q004_KOOKMIN_FINAL','Q004_KBS_FINAL']],
 'q005':[['Q005_HANI','Q005_HANKOOK','Q005_NOCUT'],['Q005_HANI','Q005_HANKOOK'],['Q005_HANI','Q005_HANKOOK'],['Q005_HANI','Q005_NOCUT','Q005_HANKOOK'],['Q005_HANI','Q005_HANKOOK','Q005_NOCUT'],[],[],['Q005_HANI','Q005_HANKOOK','Q005_NOCUT']]}
 facts=f'# {q} 사실표\n\n채택 심급: '+c['court']+'\n\n'
 for i,u in enumerate(utterances[:-1]):
  facts+=f'- F{i+1}: {u["shown"].replace(chr(10)," ")} — sources: '+(', '.join(mappings[q][i]) or '시청자 질문 / 일반적인 비기계성 설명; 이 사건의 추가 인정 사실 아님')+'\n'
 facts+='\n## 수치·법적 의미\n'
 if q=='q004':
  facts+='450원 초코파이 1개 + 600원 커스터드 1개 = 총 1,050원. 중앙일보 항소심 현장 취재, 경향신문 상고 포기 보도, 국민일보 독자 기사 모두 일치. 400원·650원 보도 변형은 채택하지 않음. 1심 벌금 5만 원은 과거 판결, 검찰의 초기 약식기소 벌금 50만 원과 다르다. 영상에는 약식기소 금액을 쓰지 않는다. 검찰 항소심 선고유예 구형은 요청이며 법원 판결 아님. 최종 질문은 항소심 무죄 및 검찰 상고 포기로 확인된 확정 결과를 답한다. 대법원 무죄 선고라고 표현하지 않는다. 원심 피고인 직종 표현 차이는 쓰지 않는다. 간식이 소액이면 언제나 무죄라는 법칙이 아니라 절도 고의 입증에 관한 사건 판단이다.\n'
 else:
  facts+='2025년 2월 26일 행위, 2026년 5월 27일 광주지법 형사4단독 1심. 스리랑카 국적 성인 동료, 벽돌 더미와 산업용 비닐로 결박·지게차로 들어 올림·약 10m 이동. 추락 위험은 법원 판단이며 실제 추락·중상·사망을 묘사하지 않는다. 1심 선고 징역 1년·집행유예 2년·사회봉사 180시간. 법인 벌금 500만 원은 별도이고 영상에서는 묻지 않는다. 2026년 4월 29일 검찰 징역 1년 구형은 선고와 다르다(구형은 원자료 참조, 영상 비사용). 이번 검색에서 후속 항소심·확정 결과를 찾지 못했으며 최종 확정형으로 주장하지 않는다. 합의·처벌불원 외 반성·정신적 고통·추락 위험을 함께 제시. 돈·국적이 판결을 좌우했다는 사실 주장, 합의금 액수·부유함·매수 암시 없음. 피부색은 국적의 증거가 아니며 외모는 사실 인물의 재현이 아닌 별도 원작 캐릭터. q013 B 디자인과 다른 머리·얼굴·작업복.\n'
 facts+='\n원문 판결문 전체 미확보. 서로 다른 언론사 원문 스냅샷 교차 확인까지 수행했고 CTO의 사실 의미·출처 독립성 서명을 기다린다.\n'
 (p/'facts.md').write_text(facts)
 (p/'script.md').write_text('[COLD_OPEN @ 0.000]\n[CENTRAL_QUESTION @ 0.000]\n'+'\n'.join(f'## {u["id"]} · {u["start_s"]:.3f}–{u["end_s"]:.3f}s · {u["mode"]}\n{u["text"]}\n화면: 완결 대사 경계의 한 샷, 구도 안 연기' for u in utterances)+'\n')
 dump(p/'episode.json',dict(qid=q,answerHead=c['answer'],cues=[[u['id'],'reveal' if u['mode']=='answer' else 'incident',[u['text']],[],0,dict(lines=u['shown'].split('\n'))] for u in utterances]))
 disclosure='판결 보도를 바탕으로 만든 독창 캐릭터의 2D 애니메이션 각색·재구성입니다. 실제 현장·법정 영상이 아닙니다. 동작과 시간은 압축했으며 표정·몸짓·망치·도장·저울은 극화와 시각적 비유입니다. 법정의 표정·행동을 실제 당사자의 행동으로 주장하지 않습니다. 실제 인물의 외모·신상을 재현하지 않으며 피해·통증을 웃음 소재로 삼지 않습니다. 내레이션은 Supertonic 3 M1 AI 합성입니다.'
 desc='댓글로 A/B/C부터 골라보고 마지막 판결과 비교해 보세요.\n'+c['court']+'을 다룹니다.\n'+('450원 초코파이와 600원 커스터드, 합계 1,050원 사건입니다. 1심 벌금 5만 원과 항소심 무죄를 구분합니다. 검찰의 선고유예 구형은 선고가 아닙니다. 대법원 판결이 아니라 검찰 상고 포기로 무죄가 확정된 사건입니다.' if q=='q004' else '질문은 가해 노동자 개인의 1심 형량입니다. 징역 1년·집행유예 2년·사회봉사 180시간이며 법인의 벌금 500만 원과 다릅니다. 후속 항소심·확정 결과는 확인하지 못했습니다. 반성·합의·처벌불원과 범행의 위험을 함께 보며, 합의가 형량을 자동 결정한다는 뜻이 아닙니다. 피해자는 보도된 스리랑카 국적 성인 노동자로 설정한 별도 원작 캐릭터입니다.')
 (p/'meta.txt').write_text('[제목]\n'+c['title']+'\n\n[설명]\n'+desc+'\n'+disclosure+'\n#몇년나옴 #판결 #shorts\n\n[출처]\n'+'\n'.join(s['publisher']+' | '+s['url'] for s in src)+'\n');assert len(c['title'])<=40
 print('PREPARED',q,at/30,flush=True)
if __name__=='__main__':main(sys.argv[1])
