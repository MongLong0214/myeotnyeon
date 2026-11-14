import json,re,csv,statistics
from pathlib import Path
R=Path(__file__).resolve().parent

def sino(n):
 n=int(n)
 if n==0:return '영'
 if n>=10000:return sino(n//10000)+'만'+(sino(n%10000) if n%10000 else '')
 out=''
 for base,unit in [(1000,'천'),(100,'백'),(10,'십'),(1,'')]:
  a,n=divmod(n,base)
  if a:out+=('' if a==1 and base>1 else '일이삼사오육칠팔구'[a-1])+unit
 return out
def syll(text):
 text=re.sub(r'(\d+)(명|개|살)',lambda m:({'1':'한','2':'두','3':'세','4':'네','5':'다섯','6':'여섯','7':'일곱','8':'여덟','9':'아홉','10':'열'}.get(m[1],sino(m[1]))+m[2]),text)
 text=re.sub(r'\d+',lambda m:sino(m[0]),text)
 return len(re.findall('[가-힣]',text))
def dump(n,x): (R/n).write_text(json.dumps(x,ensure_ascii=False,indent=2))

def events(rows):
 return [{'start_s':a,'end_s':b,'description':c,'coding':'manual semantic annotation, timestamp to ASR clause; not independent fact verification'} for a,b,c in rows]
SEM={
 'reference':{
 'stakes_contrast':[(5.14,17.94,'무기수의 탈옥 실행'),(23.4,28.6,'막혀 있어야 할 창살을 쉽게 제거'),(35.48,38.02,'건물 밖이어도 아직 탈옥 전'),(42.88,50.98,'높은 벽과 도구 재활용'),(69.56,77.74,'마지막 철조망 장애물'),(88.42,94.42,'탈옥에서 장기 추격전으로 규모 확대'),(133.78,147.1,'모범수 분류와 장기 탈옥 준비의 대비'),(153.68,164.18,'창살과 체격이라는 두 난제'),(175.46,187.76,'방송 소리로 절단음 은폐'),(190.92,199.3,'환풍구 크기에 맞추는 체중 변화'),(228.02,237.76,'국가적 혼란과 한 형사의 집념 대비'),(239.3,248.32,'이전 실패와 재도전'),(282.96,295.96,'체포용 가스총의 실패'),(295.96,312.64,'형사가 오히려 위협받음'),(320.62,329.44,'부상에도 도주'),(329.74,338.72,'실패가 형사 해임과 현상금 증액으로 이어짐'),(339.02,351.8,'도피 규모와 경찰 동원 규모'),(351.8,359.48,'반복 접촉에도 미체포'),(359.84,371.02,'도주범과 경찰 인사의 역설'),(371.38,383.32,'현상금을 임금·주거비와 대비'),(401.58,414.64,'평소 표정 읽기와 수리공의 무표정 대비'),(465.24,470.08,'이번 체포의 조직적 부담'),(476.88,489.1,'무반응과 진입 뒤 낮은 저항 대비'),(507.42,521.8,'범죄자 검거 뒤 소비·팬덤 현상의 역설')],
 'foreshadowing':[(14.26,17.94,'오랜 준비를 예고; 준비 내용은 뒤에서 회수'),(88.42,94.42,'장기간 도주를 예고'),(239.3,248.32,'과거 실패를 제시해 이번 체포 위험을 예고'),(401.58,411.52,'표정으로 정체 노출을 알아챈다는 설정')],
 'reveal_withholding':[(23.4,28.6,'왜 창살을 쉽게 제거했는지는 뒤로 미룸'),(28.6,35.16,'작은 환풍구를 통과한 준비 과정은 뒤로 미룸'),(88.42,94.42,'장기 도주의 종착점을 미룸'),(153.68,164.18,'두 준비 과제를 먼저 제시하고 해법은 순차 공개'),(239.3,248.32,'재도전 성공 여부를 미룸'),(395.26,399.24,'수리공이 발견한 남자의 후속 행동을 장 카드로 중단'),(411.9,414.64,'무표정의 의미를 신고까지 미룸'),(476.88,485.7,'문 뒤 반응과 체포 결과를 진입까지 미룸')],
 'humor_irony':[(244.74,248.32,'가스총 위력을 과장해 소개한 뒤 실패: 반어적 설정'),(290.28,295.96,'위력 설명을 뒤집는 가스총 실패'),(359.84,371.02,'도주범이 경찰 인사에 영향을 준다는 역설'),(507.42,521.8,'체포 의류 인기와 팬덤의 역설')],
 'quotes':[(418.3,457.02,'신고전화 기록 삽입 한 블록. 실제 발언의 ASR는 불확실; 본문에 재인용하지 않음')]
 },
 'ours_fast':{
 'stakes_contrast':[(17.36,24.2,'조치 미실시 혐의와 사망'),(60.4,64.58,'행동 인정과 학대치사 부인'),(105.36,121.78,'피해·신뢰 훼손·용서받지 못함'),(122.02,133.66,'유리한 정상으로 시선 전환'),(147.14,151.18,'중대장 1심 구형·선고 대비'),(154.2,158.34,'부중대장 1심 구형·선고 대비'),(172.22,180.64,'피해자별 행위를 기준으로 판단 변화'),(209.14,224.06,'예방 가능성과 국가의 보호 기대 배반'),(228.3,237.2,'중대장 형 증가와 부중대장 유지')],
 'foreshadowing':[(28.22,33.26,'항소심의 행위 구별 쟁점을 미리 설명')],
 'reveal_withholding':[],
 'humor_irony':[],
 'quotes':[]
 }
}
LOOPS={
 'reference':[
  {'id':'R1','question':'탈옥은 어떻게 성공하는가','raised_s':14.26,'closed_s':88.2},
  {'id':'R2','question':'창살이 왜 쉽게 떨어졌는가','raised_s':23.4,'closed_s':205.92},
  {'id':'R3','question':'작은 환풍구 통과를 어떻게 준비했는가','raised_s':28.6,'closed_s':199.3},
  {'id':'R4','question':'장기간 도주는 어떻게 끝나는가','raised_s':88.42,'closed_s':503.24},
  {'id':'R5','question':'무기징역에 이른 배경은 무엇인가','raised_s':96.86,'closed_s':128.04},
  {'id':'R6','question':'재도전하는 형사는 이번에 잡는가','raised_s':239.3,'closed_s':329.44},
  {'id':'R7','question':'무표정한 수리공은 알아챘는가','raised_s':395.26,'closed_s':418.3},
  {'id':'R8','question':'마지막 포위 작전은 성공하는가','raised_s':457.02,'closed_s':489.1}],
 'ours_fast':[
  {'id':'O1','question':'훈련과 사망의 인과관계를 인정하는가','raised_s':24.38,'closed_s':105.16,'qualification':'설명형 쟁점 예고; 적극적인 질문·위험 예고는 없음'},
  {'id':'O2','question':'피해자별 행위를 어떻게 나누는가','raised_s':28.22,'closed_s':180.64,'qualification':'설명형 쟁점 예고'}]
}
CLIFF={
 'reference':[
 {'boundary_s':95.5,'lead_start_s':88.42,'lead_end_s':94.42,'type':'규모 확대','loop':'R4','description':'탈옥 성공 직후 장기 도주를 예고하고 과거로 되감기'},
 {'boundary_s':148,'lead_start_s':141.22,'lead_end_s':147.1,'type':'해법 유예','loop':'R2/R3','description':'모범수였지만 준비 중이었다는 반전을 남기고 준비 장으로'},
 {'boundary_s':218.5,'lead_start_s':208.94,'lead_end_s':217.78,'type':'행동 중단·순환 연결','loop':'R4','description':'오프닝과 합류해 창살 제거에서 장을 닫고 도주 생활로'},
 {'boundary_s':400.5,'lead_start_s':395.26,'lead_end_s':399.24,'type':'발견 직후 중단','loop':'R7','description':'수리공이 수상한 남자를 발견한 직후 체포 작전 장 카드'}],
 'ours_fast':[]
}
BEATS={
 'reference':[
 (0,17.94,'cold open / 실행 직전','행동부터 시작; 배경 설명은 뒤로','R1'),(18.28,35.16,'장애물과 수수께끼','환풍구 통과; 창살·체격 해법 유예','R2,R3'),(35.48,68.62,'미니 장애물 연쇄','벽→땅 파기→파이프·밧줄','R1'),(69.56,94.42,'첫 보상과 확장','철조망 돌파·탈옥 성공 뒤 장기 도주 예고','R1 닫힘 / R4 열림'),(95.5,128.04,'01 무기수 / 과거로 회귀','초기 범죄 이력·무기징역의 배경','R5 열림·닫힘'),(128.46,147.1,'기대 뒤집기','모범수와 사전 계획 대비','R2,R3 유지'),(148,164.18,'02 탈옥 계획 / 해법의 목록','창살 제거와 체격 축소 두 과제','R2,R3'),(164.54,187.76,'도구·소리의 인과','톱날·밑창·방송 시간','R2 일부 회수'),(188.16,205.92,'준비 회수','체중 변화·절단·껌','R2,R3 닫힘'),(206.38,217.78,'원점 합류','오프닝 시점으로 복귀','R4 유지'),(218.5,248.32,'03 도주 생활 / 추격자 등장','국가적 혼란과 형사의 집념 대비','R6'),(248.78,290,'작전과 기대 상승','주소·인원·신문 구독 위장·가스총','R6'),(290.28,329.44,'반전·반전·탈출','가스총 실패→위협→추격→도주','R6 닫힘'),(329.74,383.32,'대가·규모 확대','해임·현상금·거리·경찰 동원·임금 대비','R4'),(383.62,399.24,'새 발견','수리공이 수상한 남자 발견','R7'),(400.5,418.3,'04 체포 작전 / 무표정 반전','정체 노출 탐지 설명 뒤 신고','R7 닫힘'),(418.3,457.02,'기록 음성 삽입','전화 기록으로 음색·시간감 변경','R4'),(457.02,485.7,'마지막 작전','포위·무반응·진입','R8'),(486.06,503.24,'최종 보상','체포·신원 확인·장기 도주 종결','R8,R4 닫힘'),(503.56,534.614,'후일담·사회적 역설','추가 형과 대중 반응, 말미 현황','새 루프 없음')],
 'ours_fast':[
 (0,13.38,'사건 소개','날짜·부대·인원·위법성 먼저 설명','없음'),(13.58,24.2,'혐의와 결과','조치 미실시 혐의와 사망','없음'),(24.38,33.26,'쟁점 예고','인과관계·피해자별 행위','O1,O2'),(33.4,60.14,'기소 설명','두 피고인의 혐의를 각각 설명','유지'),(60.4,88.44,'부인과 구형','방어 주장 한 문장 뒤 구형 재확인','유지'),(88.98,121.78,'1심 유죄·불리한 사정','인과관계 인정과 죄책','O1 닫힘'),(122.02,144.36,'유리한 사정·법률 설명','반성·교육 목적·하나의 행위','O2 유지'),(144.62,158.34,'1심 선고','두 피고인 수치와 동일 심급 비교','유지'),(158.8,193.02,'항소심 차이','행위 구별을 여러 문장으로 재설명','O2 닫힘'),(193.02,224.06,'법률 설명·재판부 비판','가중 가능성·병영문화·국가 기대','새 루프 없음'),(224.22,237.2,'2심 선고','증가·유지 결과 전달','없음'),(237.42,267.76,'확정과 요약','대법원·확정 상태·판단 재요약','없음'),(267.76,272,'출처','무성 출처 화면','없음')]
}

OBJECTS=r'환풍구|쇠창살|쇠창사|세창사|쇠파이프|밧줄|철조망|톱날|운동화|밑창|껌|가스총|식칼|시카|신문(?!\s*구독)|모자|승용차|다이너스티|수배\s*전단|니트셔츠|니트\s*셔츠|문신|방범틀|방범티|완전군장'
PLACES=r'부산교도소|서울구치소|청송교도소|대전교도소|부산교도소|전북\s*김제|서울\s*도남동|서울\s*목동|경기도\s*평택|전남\s*순천|신병교육대|춘천지법|서울고법\s*춘천재판부|대법원|강원도?\s*인[제재]|화장실|재료창고|교회\s*신축\s*공사장|빌라|아파트|현관문|베란다'
NUMBERS=r'\d[\d,.]*(?:\s*(?:년|월|일|시|분|초|동|층|호실|호|명|세|살|개|차례|만\s*명|만장|만\s*장|만원|만\s*원|원|평|달|개월|시간|cm|kg|km|m|미터))?'
def sentences(label):
 data=json.loads((R/(label+'_transcript.json')).read_text()); words=[]
 for s in data['segments']:
  if label=='reference' and s['start']>=418.3 and s['start']<457.02:continue
  words.extend(w for w in s.get('words',[]) if w['end']>w['start'])
 result=[];buf=[]
 for w in words:
  if buf and w['start']-buf[-1]['end']>5:
   result.append(buf);buf=[]
  buf.append(w)
  text=w['word'].strip().rstrip('.,!?"”')
  if re.search(r'(?:니다|였다|었다|했다|된다|이다|한다|죠|지요|요)$',text) or w['word'].rstrip().endswith('?'):
   result.append(buf);buf=[]
 if buf:result.append(buf)
 # Canonical source text prevents ASR wording errors from altering our sentence statistics.
 if label=='ours_fast':
  lines=[]
  for line in Path('episodes/v4/n18/script.md').read_text().splitlines():
   m=re.match(r'\| (N\d+) \| .*? \| (.*?) \| (.*?) \|',line)
   if m:lines.append(m[2])
  # 63 source sentences, aligned with prior validated fast-preview ASR start/end sequence.
  old=json.loads((R.parent/'ref_extol/ours_fast/whisper_words.json').read_text())['segments']
  # That ASR has one split inside N051; merge it before zipping.
  aligned=[]
  for s in old:
   if s['start']==221.98:
    aligned[-1]['end']=s['end']; aligned[-1]['text']+=s['text'];continue
   aligned.append(dict(s))
  assert len(lines)==len(aligned),(len(lines),len(aligned))
  sent=[{'id':f'O{i+1:03}','start_s':s['start'],'end_s':s['end'],'text':txt,'source':'script.md canonical; times from fast-preview ASR'} for i,(s,txt) in enumerate(zip(aligned,lines))]
 else:
  sent=[{'id':f'R{i+1:03}','start_s':b[0]['start'],'end_s':b[-1]['end'],'text':''.join(w['word'] for w in b).strip(),'source':'fresh offline mlx_whisper ASR; telephone insert excluded'} for i,b in enumerate(result)]
 return sent,words,data

def process(label,duration):
 sent,words,data=sentences(label)
 endings={'습니다_ㅂ니다_입니다':0,'죠_지요':0,'요':0,'다':0,'other':0}
 for s in sent:
  txt=s['text'].strip().rstrip('.,!?"”')
  cat='습니다_ㅂ니다_입니다' if re.search(r'니다$',txt) else '죠_지요' if re.search(r'(죠|지요)$',txt) else '요' if txt.endswith('요') else '다' if txt.endswith('다') else 'other'
  endings[cat]+=1
 ev={k:events(v) for k,v in SEM[label].items()}
 ev.update({k:[] for k in ['rhetorical_questions','direct_address','reversal_markers','specific_details']})
 for s in sent:
  if '?' in s['text']:ev['rhetorical_questions'].append({'start_s':s['start_s'],'end_s':s['end_s'],'sentence_id':s['id']})
  for m in re.finditer(r'그런데|하지만|그러나|그럼에도|었지만|했지만|였지만|있었지만',s['text']):
   # Sentence-level time interval; word alignment locates marker, no interpolation precision claimed.
   ev['reversal_markers'].append({'start_s':s['start_s'],'end_s':s['end_s'],'marker':m[0],'sentence_id':s['id']})
 # Specific-detail tokens from ASR on both versions, so numeral spellings use same representation.
 for seg in data['segments']:
  if label=='reference' and 418.3<=seg['start']<457.02:continue
  for kind,pattern in [('number',NUMBERS),('object',OBJECTS),('place',PLACES),('time',r'새벽|오전|오후|저녁|\d+\s*(?:시|분|개월|달|시간)|이틀|두\s*달')]:
   for m in re.finditer(pattern,seg['text']):
    # Deduplicate exact spans with multiple tags (number and time).
    same=next((e for e in ev['specific_details'] if e['segment_id']==seg['id'] and e['char_start']==m.start() and e['char_end']==m.end()),None)
    if same:same['tags'].append(kind)
    else:ev['specific_details'].append({'start_s':seg['start'],'end_s':seg['end'],'segment_id':seg['id'],'char_start':m.start(),'char_end':m.end(),'token':m[0],'tags':[kind]})
 # Exact requested narrow marker count, alongside broader adversatives.
 narrow=sum(e['marker'] in ['그런데','하지만'] for e in ev['reversal_markers'])
 for loop in LOOPS[label]:loop['wait_s']=round(loop['closed_s']-loop['raised_s'],2)
 speech_syll=sum(syll(s['text']) for s in sent)
 # Same 0.2s gap rule for both voices; remove telephone duration from reference narration span.
 gap=sum(b['start']-a['end'] for a,b in zip(words,words[1:]) if b['start']-a['end']>.2 and b['start']-a['end']<20)
 span=words[-1]['end']-words[0]['start']-(38.72 if label=='reference' else 0)
 stats={'sentence_count':len(sent),'ending_counts':endings,'ending_shares':{k:round(v/len(sent),4) for k,v in endings.items()},'average_sentence_hangul_syllables_normalized':round(speech_syll/len(sent),2),'average_sentence_eojeol':round(statistics.mean(len(s['text'].split()) for s in sent),2),'question_sentence_share':sum('?' in s['text'] for s in sent)/len(sent),'estimated_spoken_hangul_syllables':speech_syll,'narration_syllables_per_timeline_s':speech_syll/duration,'narration_syllables_per_phrase_s':speech_syll/(span-gap),'speech_rate_method':'Hangul blocks; Arabic numerals expanded to Korean numerals, not unit names. Phrase span minus word gaps >0.2s. Approximation; ASR and foreign-unit pronunciation uncertainty. Reference telephone insert excluded.'}
 counts={k:{'count':len(v),'per_minute':round(len(v)/(duration/60),3)} for k,v in ev.items()}
 counts['그런데_하지만_only']={'count':narrow,'per_minute':round(narrow/(duration/60),3)}
 counts['open_loops']={'count':len(LOOPS[label]),'per_minute':round(len(LOOPS[label])/(duration/60),3)}
 counts['chapter_ending_cliffhangers']={'count':len(CLIFF[label]),'per_minute':round(len(CLIFF[label])/(duration/60),3)}
 dump(label+'_sentences.json',sent)
 return {'duration_s':duration,'voice':stats,'device_counts':counts,'device_events':ev,'open_loops':LOOPS[label],'chapter_ending_cliffhangers':CLIFF[label],'beats':[{'start_s':a,'end_s':b,'type':t,'description':d,'loops':l} for a,b,t,d,l in BEATS[label]],'audio':json.loads((R/(label+'_audio_summary.json')).read_text())}

if __name__=='__main__':
 result={'method':{'network':'Only yt-dlp audio download for the supplied URL. No video downloaded in this task. Existing local ref-cuts stills/video inspected for first-minute visuals and chapter cards.','transcription':json.loads((R/'transcription_method.json').read_text()),'denominator':'All device densities use complete media duration in minutes; narrator statistics exclude telephone insert. Device categories overlap; counts are coded occurrences, not claims of statistical causation.','event_time_precision':'Semantic annotations use clause boundaries, generally ±0.5s. Lexical-detail events carry ASR segment interval, not invented point times.','music':'No isolated music stem or human listening test; mixture proxies only.','causal_limit':'One reference and one preview; no retention analytics. These measurements motivate editorial hypotheses, not proof of why 1.7M viewers watched.'},'reference':process('reference',534.614),'ours_fast':process('ours_fast',272.0)}
 dump('devices.json',result)
 for k in ['reference','ours_fast']:print(k,json.dumps({'voice':result[k]['voice'],'counts':result[k]['device_counts']},ensure_ascii=False,indent=2))
