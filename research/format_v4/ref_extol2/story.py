import json,re,csv,statistics,sys
from pathlib import Path
R=Path(__file__).resolve().parent
# Same sentence and syllable rules as ref_extol_story/annotate.py.
source=(R.parent/'ref_extol_story/annotate.py').read_text(); helpers=source[:source.index('def events')];exec(helpers.replace('R=Path(__file__).resolve().parent',''))
d=json.loads((R/'ref/whisper_words.json').read_text()); words=[w for s in d['segments'] for w in s.get('words',[]) if w['end']>w['start']]
# Corrections supported by the visible labels/subtitles; raw ASR is retained separately.
fix={'우범군':'우범곤','우범고는':'우범곤은','우범권':'우범곤','우번고':'우범곤','우번권':'우범곤','우봉곤':'우범곤','우승경':'우순경','무순경':'우순경','국류':'궁류','운게리':'운계리','동거네':'동거녀','동건역':'동거녀','비신한':'피신한','사륙':'살육','무기구':'무기고','오늘은 있다 있을':'오늘은 이따 있을'}
segments=[]
for s in d['segments']:
 text=s['text'].strip()
 for a,b in fix.items():text=text.replace(a,b)
 if s['id']==100: text='[장 카드: 3. 경찰 출동; ASR 오인식 제외]'
 segments.append({**s,'corrected_text':text})
(R/'transcript_corrected.txt').write_text('\n'.join(f"{s['start']:.2f}–{s['end']:.2f} {s['corrected_text']}" for s in segments))
# Exclude chapter-card ASR hallucination, merge audio words into grammatical sentences.
words=[w for s in d['segments'] if s['id']!=100 for w in s.get('words',[]) if w['end']>w['start']]
sents=[];buf=[]
for w in words:
 buf.append(w);end=w['word'].strip().rstrip('.,!?\"”')
 if re.search(r'(?:니다|였다|었다|했다|된다|이다|한다|죠|지요|요)$',end) or w['word'].rstrip().endswith('?'):
  sents.append({'start_s':buf[0]['start'],'end_s':buf[-1]['end'],'text':''.join(x['word'] for x in buf).strip()});buf=[]
if buf:sents.append({'start_s':buf[0]['start'],'end_s':buf[-1]['end'],'text':''.join(x['word'] for x in buf).strip()})
for i,s in enumerate(sents):s['id']=f'R2S{i+1:03}'
ending={'습니다_ㅂ니다_입니다':0,'죠_지요':0,'요':0,'다':0,'other':0}
for s in sents:
 txt=s['text'].rstrip('.,!?\"”');cat='습니다_ㅂ니다_입니다' if txt.endswith('니다') else '죠_지요' if txt.endswith(('죠','지요')) else '요' if txt.endswith('요') else '다' if txt.endswith('다') else 'other'; ending[cat]+=1
# Quotes are coded as blocks, not individual clauses; categories can overlap.
manual={
 'foreshadowing':[(10.1,16.8,'8시간/56명 결과 선제시'),(71.66,81.72,'악마·마을 사람 모두를 죽인다는 예고'),(112.16,115.7,'특등사수 설명→발사'),(174.08,180.1,'술만 먹으면 돌변한다는 설정→상갓집에서 회수'),(329.06,334.66,'총·수류탄을 지닌 채 술자리→대량 살상')],
 'reveal_withholding':[(10.1,16.8,'파리가 어떻게 56명의 죽음으로 연결되는가'),(74.38,81.72,'지금부터 할 행동의 규모를 먼저 예고'),(118.94,128.78,'첫 희생자→전체 전개 유예'),(365.62,369.34,'아기 울음→다음 행동 직전 중단'),(418.84,423.54,'8시간 동안 경찰은 어디 있었는가'),(481.38,487.1,'진짜 이유를 질문'),(509.08,513.18,'한 미치광이의 일인가→사회적 여운')],
 'quotes':[(63.88,67.22,'경찰이면 다냐고 간접 인용'),(144.84,157.44,'담임교사 증언 한 블록'),(174.08,180.1,'미친 호랑이라는 별명/주변 증언'),(335.08,338.2,'비상이 걸려 무장했다는 답변'),(342.42,346.96,'경찰이면 경찰이지라는 꾸짖음'),(379.04,386.42,'불을 끄라는 외침 간접 인용'),(487.34,508.8,'당시 기사 직접 인용 한 블록')],
 'humor_irony':[(193.84,199.4,'권력에 가장 가까운 곳→가장 먼 곳'),(321.1,329.06,'살상 중 문상·부의금·술자리의 역설; 웃음 유도와 구별'),(354.4,362.6,'슬픔의 장소에 또 불운'),(423.78,427.54,'경찰이 범행 종료 후 나타남'),(437.18,471.92,'보호해야 할 경찰이 반대로 도주·은신')],
 'stakes_contrast':[(10.1,16.8,'파리와 56명 대비'),(23.04,40.04,'휴식에서 폭행으로'),(47.76,52.22,'말리는 사람까지 폭행'),(71.66,81.72,'대립에서 학살로 확대'),(95.56,101.04,'막을 이들의 도주'),(104.06,111.94,'무관한 행인을 겨눔'),(118.94,128.78,'첫 희생자→전체 규모'),(166.08,173.82,'경호부대→부적격'),(193.84,199.4,'권력 근처→외진 좌천'),(199.56,212.02,'사랑·결혼의 장벽'),(243.82,255.62,'계획 범행 해석에 반론'),(261.36,267.34,'3명 사망→외부 통신 차단'),(278.68,290.02,'안전한 집→지옥; 생존→사망'),(300.28,306.76,'반상회가 피해 확대 조건'),(321.1,338.2,'문상·부의금과 무장'),(347.32,353.94,'28명 살상 사실을 몰랐다면'),(358.24,362.6,'상갓집의 이중 슬픔'),(365.62,372.58,'아기까지 피해 확대'),(379.04,389.08,'불 끈 집과 피해'),(403.94,415.32,'종결과 탄약 사용량'),(423.78,427.54,'범행 뒤 등장'),(430.64,436.94,'경찰 부재와 접대'),(437.18,447.74,'신고를 듣고 반대로 숨음'),(447.74,471.92,'30여명 출동과 추가 26명 살상 대비'),(475,487.1,'죽은 범인과 동기 미해결'),(489.72,505.5,'침착한 실행과 무목적성 대비'),(509.08,521.5,'개인 광기와 사회 분위기')]
}
ev={k:[{'start_s':a,'end_s':b,'description':c,'coding':'manual semantic; clause alignment; ±0.5s'} for a,b,c in v] for k,v in manual.items()}
ev.update({k:[] for k in ['rhetorical_questions','direct_address','reversal_markers','specific_details']})
for s in sents:
 if '?' in s['text']:ev['rhetorical_questions'].append({'start_s':s['start_s'],'end_s':s['end_s'],'sentence_id':s['id'],'text':s['text']})
 for m in re.finditer(r'그런데|하지만|그러나|그럼에도|었지만|했지만|였지만|있었지만',s['text']):ev['reversal_markers'].append({'start_s':s['start_s'],'end_s':s['end_s'],'marker':m[0]})
# Same token-span rule and numbers/time expressions; objects/places adapted to this story.
NUMBERS=r'\d[\d,.]*(?:\s*(?:년|월|일|시|분|초|동|층|호실|호|명|세|살|개|차례|만\s*명|만장|만\s*장|만원|만\s*원|원|평|달|개월|시간|cm|kg|km|m|미터))?'
OBJECTS=r'파리|가슴|카빈총|총기|실탄|수류탄|무기고|방아쇠|부의금|술|코드|전화|울음소리|불이?\s*켜진\s*집|뇌세포'
PLACES=r'경상남도|의령군|의령경찰서|궁류면|궁류지서|국류|부산|청와대|해병대|우체국|경찰서|압곡리|앞공리|운계리|평촌리|상갓집|다리\s*밑|온천|무기고'
for s in segments:
 if s['id']==100:continue
 text=s['corrected_text']
 for kind,pat in [('number',NUMBERS),('object',OBJECTS),('place',PLACES),('time',r'새벽|오전|오후|저녁|\d+\s*(?:시|분|개월|달|시간)|이틀|두\s*달')]:
  for m in re.finditer(pat,text):
   same=next((e for e in ev['specific_details'] if e['segment_id']==s['id'] and e['char_start']==m.start() and e['char_end']==m.end()),None)
   if same:same['tags'].append(kind)
   else:ev['specific_details'].append({'start_s':s['start'],'end_s':s['end'],'segment_id':s['id'],'char_start':m.start(),'char_end':m.end(),'token':m[0],'tags':[kind]})
loops=[('L1','파리 한 마리가 어떻게 학살로 이어지는가',10.1,118.94,'초기 살상까지 인과 회수'),('L2','8시간의 범행은 어떻게 끝나는가',10.1,407.22,'자폭·종결'),('L3','특등사수 이력은 어디서 왔는가',112.16,161.02,'회상으로 회수'),('L4','왜 폭력적이 되었는가',131.52,230.1,'서술자의 배경 해석; 확정 원인 아님'),('L5','아기 울음을 듣고 어떻게 하는가',365.62,372.58,'즉시 회수'),('L6','경찰은 어디 있었는가',418.84,471.92,'은신 공개'),('L7','진짜 범행 이유는 무엇인가',481.38,521.5,'기사+사회 분위기 제안; 단일 해답은 열어둠')]
beats=[(0,17.06,'cold open','시간·장소→파리→56명 결과→사소한 원인으로 복귀','L1,L2'),(17.06,58.5,'가정 내 폭력','소개·가슴을 침→폭행→호랑이 비유','L1'),(58.5,81.72,'위협 확대','술·항의→악마→마을 전체 예고','L1'),(81.72,118.94,'도구와 첫 실행','무기 수량→도주한 주변인→조준→첫 발사','L1 닫힘/L3'),(118.94,129.4666666667,'첫 보상·규모','56명/35명·사건명','L2'),(129.4666666667,158,'01 인물 회상','신문·사진·담임 증언','L4'),(158,199.56,'경력 반전','특등사수→청와대→부적격→외진 좌천','L3 닫힘'),(199.56,230.7333333333,'인과 고리 복귀','일·사랑 좌절→파리·폭행 장면 재호출','L4 제안/L1 재현'),(230.7333333333,267.62,'02 사건 당일·고립','우체국·전화 교환 구조·3명 사망·통신 단절','L2'),(267.62,317.3,'피해 누적','마을 지도↔현장 재연; 집·반상회·총·수류탄','L2'),(317.3,353.94,'상갓집의 거짓 평온','부의금·술·무장 질문·꾸짖음→가정법 질문','L2'),(354.4,389.34,'피해 확대','상갓집·아기·불 켜진 집; 택시기사 경고','L5 열림/닫힘'),(389.34,416.1,'범행 종결','가족집·수류탄·자폭·탄약 회수','L2 닫힘'),(416.1,472.8666666667,'03 경찰 출동','늦은 도착·접대·반대 방향 은신·30여명도 다리 밑','L6 열림/닫힘'),(472.8666666667,521.8,'04 범행 목적','뇌세포 분석·무목적 범행 기사·사회적 폭력 여운','L7 열림/부분 회수')]
cliffs=[{'boundary_s':130,'description':'첫 희생자와 총 피해 규모를 남긴 채 인물 회상','classification':'시간축 전환/규모 루프 지속'}, {'boundary_s':230.7,'description':'호랑이와 파리를 재호출하고 사건 당일 복귀','classification':'순환 연결; 새 결과 유예는 약함'}, {'boundary_s':416.6,'description':'탄약 회수로 학살 종결→경찰 부재라는 새 질문','classification':'주제 전환; 직전 문장 절벽형 아님'}, {'boundary_s':473,'description':'26명 살해 동안 경찰 은신이라는 분노의 정점→원인','classification':'대비 정점; 다음 행동 중단 아님'}]
sy=sum(syll(s['text']) for s in sents);gaps=[b['start']-a['end'] for a,b in zip(words,words[1:]) if .2<b['start']-a['end']<20];dur=521.8
voice={'sentence_count':len(sents),'ending_counts':ending,'ending_shares':{k:round(v/len(sents),4) for k,v in ending.items()},'average_sentence_hangul_syllables_normalized':sy/len(sents),'average_sentence_eojeol':statistics.mean(len(s['text'].split()) for s in sents),'question_sentence_share':sum('?' in s['text'] for s in sents)/len(sents),'estimated_spoken_hangul_syllables':sy,'narration_syllables_per_timeline_s':sy/dur,'narration_syllables_per_phrase_s':sy/(words[-1]['end']-words[0]['start']-sum(gaps)),'note':'Same ref1 rule; quotes included here; chapter-card hallucination excluded. Numeral reading approximate.'}
result={'duration_s':dur,'voice':voice,'device_counts':{k:{'count':len(v),'per_minute':len(v)/(dur/60)} for k,v in ev.items()},'device_events':ev,'open_loops':[{'id':i,'question':q,'raised_s':a,'closed_or_reframed_s':b,'wait_s':b-a,'resolution':c} for i,q,a,b,c in loops],'chapter_ending_cliffhangers':cliffs,'beats':[dict(zip(['start_s','end_s','type','description','loops'],b)) for b in beats],'method':'Device definitions follow ref_extol_story/annotate.py. Direct address excludes reported dialogue. Specific detail dictionary is story-specific; categories overlap. No retention data or history fact-check.'}
result['device_counts']['open_loops']={'count':len(loops),'per_minute':len(loops)/(dur/60)}
result['device_counts']['strict_action_cliffhangers']={'count':0,'per_minute':0}
(R/'devices.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));(R/'sentences.json').write_text(json.dumps(sents,ensure_ascii=False,indent=2));print(json.dumps({'voice':voice,'devices':result['device_counts']},ensure_ascii=False,indent=2))
rows=[]
for a in range(0,522,60):
 row={'start_s':a,'end_s':min(a+60,dur)}
 for k,v in ev.items():row[k]=sum(a<=e['start_s']<a+60 for e in v)
 rows.append(row)
with (R/'devices_per_minute.csv').open('w') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
