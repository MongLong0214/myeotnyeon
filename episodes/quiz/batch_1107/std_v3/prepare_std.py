"""Prepare the three requested q013-v3-template Shorts. Never uploads."""
from pathlib import Path
import json, hashlib, math, re, shutil, subprocess, sys
import numpy as np
import soundfile as sf
from scipy.signal import resample_poly

W=Path(__file__).resolve().parents[4]; D=Path(__file__).parent
sys.path.insert(0,str(W/'factory'))
from fresh import trim
def dump(p,x): Path(p).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

SPECS={
 'q020':dict(kind='train',candidate='V2-14',title='지하철에 휘발유 방화…160명 살인미수 혐의, 몇 년?',headline='달리는 지하철에 불',question='징역 몇 년?',choices=['징역 5년','징역 12년','징역 20년'],correct=1,answer='항소심 징역 12년',answer_detail='보호관찰 3년',court='서울고법 항소심 · 1심 유지',date='2026-01-15',rank=3,next='q018',reason='운행 중 객차 방화와 승객 대피가 첫 순간에 읽힌다. RANKED Shorts #3.',lines=[
  ('pour','달리는 지하철에 휘발유를 붓고 불을 질렀습니다.','달리는 지하철에 휘발유를 붓고\n불을 질렀습니다.'),
  ('evacuate','오호선 승객들이 대피했고, 연기를 마신 사람도 나왔습니다.','5호선 승객들이 대피했고,\n연기를 마신 사람도 나왔습니다.'),
  ('charge','검찰이 적용한 살인미수 혐의는 승객 백육십 명입니다.','검찰이 적용한 살인미수 혐의는\n승객 160명입니다.'),
  ('passenger','사망자 수가 아닙니다. 징역 몇 년일까요?','사망자 수가 아닙니다.\n징역 몇 년일까요?'),
  ('demand','일심에서 검찰은 징역 이십 년을 구형했습니다.','1심에서 검찰은\n징역 20년을 구형했습니다.'),
  ('recovery','재판부는 피해 회복도 대부분 이뤄지지 않았다고 봤습니다.','재판부는 피해 회복도 대부분\n이뤄지지 않았다고 봤습니다.'),
  ('trust','대중교통의 안전에 대한 신뢰도 해쳤다고 지적했습니다.','대중교통의 안전에 대한 신뢰도\n해쳤다고 지적했습니다.'),
  ('choices','항소심이 유지한 형량은 몇 년일까요? 댓글로 골라보세요.','항소심이 유지한 형량은 몇 년일까요?\n댓글로 골라보세요.'),
  ('answer','항소심 선고, 징역 십이 년. 보호관찰 삼 년입니다.','항소심 선고, 징역 12년.\n보호관찰 3년입니다.'),
  ('next','다음 판결도 맞혀보세요. 구독.','다음 판결도 맞혀보세요.\n구독.'),
 ]),
 'q018':dict(kind='parking',candidate='N06',title='차 빼달랬더니 갈비뼈 골절…1억 공탁, 몇 년?',headline='차 빼달랬더니 폭행',question='징역 몇 년?',choices=['징역 6개월','징역 2년','징역 5년'],correct=1,answer='항소심 징역 2년',answer_detail='1심과 같은 실형',court='인천지법 항소심 · 1심 유지',date='2024-09-27',rank=1,next='q022',reason='일상적인 주차 요청에 대한 폭력, 갈비뼈 골절과 1억 원 공탁 후 판단. RANKED Shorts #1.',lines=[
  ('assault','차를 빼 달랬더니, 전직 보디빌더가 여성을 때렸습니다.','차를 빼 달랬더니, 전직\n보디빌더가 여성을 때렸습니다.'),
  ('hurt','주먹과 발로 폭행해 갈비뼈가 부러졌습니다.','주먹과 발로 폭행해\n갈비뼈가 부러졌습니다.'),
  ('injury','전치 육 주 진단을 받았습니다. 징역 몇 년일까요?','전치 6주 진단을 받았습니다.\n징역 몇 년일까요?'),
  ('deposit','피고인은 일억 원을 법원에 공탁했습니다.','피고인은 1억 원을\n법원에 공탁했습니다.'),
  ('victim','하지만 피해자는 여전히 엄벌을 원했습니다.','하지만 피해자는 여전히\n엄벌을 원했습니다.'),
  ('recovery','법원은 합의에 준할 피해 회복으로 보기 어렵다고 했습니다.','법원은 합의에 준할 피해 회복으로\n보기 어렵다고 했습니다.'),
  ('factor','공탁만으로 형량이 정해지는 건 아닙니다.','공탁만으로 형량이\n정해지는 건 아닙니다.'),
  ('choices','항소심도 유지한 실형은 몇 년일까요? 댓글로 골라보세요.','항소심도 유지한 실형은 몇 년일까요?\n댓글로 골라보세요.'),
  ('answer','항소심 선고는 징역 이 년. 일심과 같은 형입니다.','항소심 선고는 징역 2년.\n1심과 같은 형입니다.'),
  ('next','다음 판결도 맞혀보세요. 구독.','다음 판결도 맞혀보세요.\n구독.'),
 ]),
 'q022':dict(kind='kick',candidate='N13',title='대리기사 사커킥, 전치 3주…남편 몇 개월?',headline='대리기사에게 사커킥',question='남편 몇 개월?',choices=['징역 4개월','징역 1년','징역 3년'],correct=0,answer='항소심 남편 징역 4개월',answer_detail='법정 구속 · 이후 상고',court='서울서부지법 항소심 · 1심 유지, 이후 상고',date='2025-04-03',rank=6,next='q020',reason='부부의 연속 폭행과 누범 중 재범, 서로 다른 항소심 형량. RANKED Shorts #6.',lines=[
  ('trip','남편이 대리기사의 다리를 걸어 넘어뜨렸습니다.','남편이 대리기사의 다리를 걸어\n넘어뜨렸습니다.'),
  ('kick','아내는 넘어진 기사의 머리를 발로 찼습니다.','아내는 넘어진 기사의 머리를\n발로 찼습니다.'),
  ('injury','기사는 뇌진탕 등 전치 삼 주의 상해를 입었습니다.','기사는 뇌진탕 등 전치 3주의\n상해를 입었습니다.'),
  ('claim','부부는 기사가 아이를 밀었다고 주장했습니다.','부부는 기사가 아이를\n밀었다고 주장했습니다.'),
  ('evidence','영상 확인 결과, 아이가 먼저 기사에게 부딪쳤습니다.','영상 확인 결과, 아이가 먼저\n기사에게 부딪쳤습니다.'),
  ('factor','법원은 공동 폭행으로 죄질이 좋지 않다고 봤습니다.','법원은 공동 폭행으로\n죄질이 좋지 않다고 봤습니다.'),
  ('choices','남편은 누범 기간이었습니다. 댓글로 선고를 골라보세요.','남편은 누범 기간이었습니다.\n댓글로 선고를 골라보세요.'),
  ('answer','항소심 선고는 남편 징역 사 개월, 법정 구속입니다.','항소심 선고는 남편 징역 4개월,\n법정 구속입니다.'),
  ('wife','아내는 징역 사 개월에 집행유예 일 년. 이후 상고했습니다.','아내는 징역 4개월에 집행유예 1년.\n이후 상고했습니다.'),
  ('next','다음 판결도 맞혀보세요. 구독.','다음 판결도 맞혀보세요.\n구독.'),
 ])
}

def main(q):
 from supertonic import TTS
 c=dict(SPECS[q],qid=q,number=None)
 p=W/'upload/pkg'/f'{q}_std';p.mkdir(exist_ok=True);(p/'audio').mkdir(exist_ok=True)
 old=W/'upload/pkg'/f'{q}_batch1107'
 for name in ['research.json','topic_evidence.json']:shutil.copy2(old/name,p/name)
 if q=='q022':
  research=json.loads((p/'research.json').read_text())
  for sid,pub,name,url in [('N13_FN','파이낸셜뉴스','N13_FN_body.txt','https://news.nate.com/view/20250404n02506'),('N13_DAILY','데일리한국','N13_DAILY_body.txt','https://daily.hankooki.com/news/articleView.html?idxno=1202920'),('N13_SIDAE','시대','N13_SIDAE_body.txt','https://www.sidae.com/article/2025041114274810557')]:
   f=D/name;research['sources'].append(dict(id=sid,publisher=pub,file=str(f.relative_to(W)),url=url,sha256=sha(f)))
  dump(p/'research.json',research)
 tts=TTS(auto_download=False,intra_op_num_threads=1,inter_op_num_threads=1);voice=tts.get_voice_style('M1')
 utterances=[];waves=[];at=0
 for i,(mode,text,shown) in enumerate(c['lines']):
  f=p/'audio'/f'{i:02}.wav';key=f.with_suffix('.text');syll=len(re.findall('[가-힣]',text))
  if not f.exists() or not key.exists() or key.read_text()!=text:
   speed=1.35
   for take in range(8):
    raw,_=tts.synthesize(text,voice_style=voice,lang='ko',speed=speed,total_steps=16,silence_duration=.20)
    x=resample_poly(trim(np.asarray(raw,np.float32).reshape(-1),44100),160,147).astype(np.float32)
    rate=syll/(len(x)/48000)
    if 7.8<=rate<=8.8:break
    speed=min(2.,max(.7,speed*math.sqrt(8.3/rate)))
   assert rate>=7.5,(q,i,rate)
   sf.write(f,x,48000,subtype='PCM_24');key.write_text(text)
  x,sr=sf.read(f,dtype='float32');assert sr==48000
  frames=math.ceil(len(x)/1600)
  # Sustained line-level staging. No rapid reaction cutting inside a line.
  if mode=='choices':frames=90
  elif mode=='next':frames=45
  else:frames=max(frames,63)
  if len(x)>frames*1600 or mode=='choices':
   fixed=f.with_name(f.stem+'_fit.wav')
   target=(frames-1)*1600 if mode=='choices' else frames*1600
   subprocess.run(['ffmpeg','-v','error','-y','-i',str(f),'-af',f'atempo={len(x)/target}',str(fixed)],check=True)
   x,_=sf.read(fixed,dtype='float32')
  active=min(len(x),frames*1600)/48000
  x=np.pad(x[:frames*1600],(0,max(0,frames*1600-len(x))))
  utterances.append(dict(id=f'S{i+1}',mode=mode,text=text,tts_text=text,shown=shown,from_frame=at,dur=frames,start_s=at/30,end_s=(at+frames)/30,syllables=syll,sps=syll/active,active_seconds=active,file=str(f.relative_to(W)),sha256=sha(f)))
  waves.append(x);at+=frames
  print(q,mode,frames,round(syll/active,2),flush=True)
 assert 600<=at<=900,(q,at)
 c.update(n=at,duration=at/30,utterances=utterances,answer_frame=next(u['from_frame'] for u in utterances if u['mode']=='answer'),choice_frame=next(u['from_frame'] for u in utterances if u['mode']=='choices'),cta_frame=utterances[-1]['from_frame'])
 sf.write(p/'raw.wav',np.concatenate(waves),48000,subtype='PCM_24')
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(p/'raw.wav'),'-af','loudnorm=I=-14:TP=-1.5:LRA=11','-ar','48000','-ac','2',str(p/'mix_master.wav')],check=True)
 dump(p/'case.json',c);dump(p/'audio.json',dict(items=utterances,reference=' '.join(u['text'] for u in utterances),engine='Supertonic 3 M1'))
 dump(p/'recipe.json',dict(qid=q,number=None,from_scratch=True,template='q013 v3',no_upload=True))
 # These are complete factual sentences; pictorial attitude beats are dramatization.
 src=json.loads((p/'research.json').read_text())['sources']
 facts='# '+c['headline']+'\n\n채택 심급: '+c['court']+'; '+c['date']+'.\n\n'
 claim_sources={0:['N13_HANKOOK','N13_FN'],1:['N13_HANKOOK','N13_FN'],2:['N13_HANKOOK','N13_FN'],3:['N13_KBS','N13_YTN'],4:['N13_KBS','N13_YTN'],5:['N13_KBS','N13_YTN'],6:['N13_YTN','N13_FN'],7:['N13_KBS','N13_YTN'],8:['N13_KBS','N13_YTN','N13_DAILY','N13_SIDAE']} if q=='q022' else {}
 facts+='\n'.join(f'- F{i+1}: {u["text"]} — sources: '+', '.join(claim_sources.get(i,[s['id'] for s in src])) for i,u in enumerate(utterances) if u['mode']!='next')
 facts+='\n\n구형은 검찰의 요청이고 선고가 아니다. 공탁·합의가 형량을 기계적으로 결정하지 않는다. 횟수·무기·새 피해·실제 법정 대사를 추가하지 않는다.\n'
 facts+=('1심 검찰 구형 20년 / 항소심 선고 12년·보호관찰 3년. 승객 160명 살인미수 혐의, 사망자 수 아님. 최종 확정 여부는 주장하지 않음.\n' if q=='q020' else '이 영상은 2024-09-27 항소심만 묻는다. 배우자 별도 재판의 형을 합치지 않는다.\n' if q=='q018' else '2025-04-03 항소심만 묻는다. 이후 상고 보도, 최종 확정 미확인. 아이는 피해자로 묘사하지 않고 아동 인물도 화면에 쓰지 않는다. 행위 순서는 한국일보, 항소심 결과는 KBS·YTN.\n')
 (p/'facts.md').write_text(facts)
 (p/'script.md').write_text('[COLD_OPEN @ 0.000]\n[CENTRAL_QUESTION @ 0.000]\n'+'\n'.join(f'## {u["id"]} · {u["start_s"]:.3f}–{u["end_s"]:.3f}s · {u["mode"]}\n{u["text"]}\n화면: 한 문장 한 샷, 구도 안 연기' for u in utterances)+'\n')
 dump(p/'episode.json',dict(qid=q,answerHead=c['answer'],cues=[[u['id'],'reveal' if u['mode']=='answer' else 'incident',[u['text']],[],0,dict(lines=u['shown'].split('\n'))] for u in utterances]))
 disclosure='판결 보도를 바탕으로 만든 독창 캐릭터의 2D 애니메이션 각색·재구성입니다. 실제 현장·법정 영상이 아닙니다. 동작과 시간은 압축했고, 표정·몸짓·망치·도장·기울어지는 저울은 이해를 위한 극화와 시각적 비유입니다. 법정의 표정과 행동을 실제 피고인의 행동으로 주장하지 않습니다. 피해자의 외모·신상은 재현하지 않으며 피해·통증을 웃음 소재로 삼지 않습니다. 내레이션: Supertonic 3 M1 AI 합성.'
 desc='댓글로 예상 형량부터 골라보세요. 마지막 선고와 비교해 보세요.\n'+c['court']+' 판결을 묻습니다. '+('1심 검찰 구형 20년은 요청이며, 항소심 선고와 구분합니다. 160명은 살인미수 혐의 대상 승객 수로 사망자 수가 아닙니다.' if q=='q020' else '1억 원 공탁과 피해 회복 판단은 구분됩니다. 공탁이 형량을 기계적으로 정하지 않습니다.' if q=='q018' else '남편과 아내의 선고를 구분합니다. 이후 상고 보도가 있어 최종 확정형이라고 표현하지 않습니다. 아동 피해 사건으로 묘사하지 않습니다.')
 (p/'meta.txt').write_text('[제목]\n'+c['title']+'\n\n[설명]\n'+desc+'\n'+disclosure+'\n다음 판결도 함께 맞혀보세요.\n#몇년나옴 #판결 #shorts\n\n[출처]\n'+'\n'.join(s['publisher']+' | '+s['url'] for s in src)+'\n\n번호 미배정. 업로드·예약 없음.\n')
 assert len(c['title'])<=40
 print('PREPARED',q,at/30,flush=True)
if __name__=='__main__': main(sys.argv[1])
