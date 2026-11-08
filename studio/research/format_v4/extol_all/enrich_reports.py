import json,csv,sys,math,shutil
from pathlib import Path
R=Path(__file__).resolve().parent
A=json.loads((R/'all_summary.json').read_text());by={x['id']:x for x in A}
def read(p):return list(csv.DictReader(p.open()))
def csvout(p,rows):
 if not rows:return
 fields=list(dict.fromkeys(k for row in rows for k in row))
 with p.open('w',newline='') as f:
  w=csv.DictWriter(f,fieldnames=fields);w.writeheader();w.writerows({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(dict,list)) else v for k,v in row.items()} for row in rows)
def tab(headers,rows):return '| '+' | '.join(headers)+' |\n|'+'|'.join('---' for _ in headers)+'|\n'+'\n'.join('| '+' | '.join(str(x).replace('|','／') for x in row)+' |' for row in rows)
CLIFF={
'H_GaGKQp17k':[(41.433,'예고 후 되감기','해머 사용 결과를 몽타주로 먼저 남기고 이력으로 이동',False),(92.033,'설명 전환','범행 유형을 제시한 뒤 첫 현장을 설명',False),(351.867,'해법/전개 유예','경찰이 연결할 때 대상·방식 변경을 예고',False),(433.867,'발견 유예','업주가 연결을 발견했다고 말한 뒤 구체적 단서를 보여줌',False),(577.133,'행동 결과 중단','체포 뒤 탈주 상태를 남기고 재체포 장으로 이동',True)],
'w_LJ_GQObic':[(94.9,'규모 확대','탈옥 성공 뒤 장기 도주라는 더 큰 질문을 남기고 회상',False),(147.7,'해법 유예','창살과 체격의 두 과제 해결을 다음 장에 남김',False),(218.233,'행동 중단/순환 합류','창살을 떼는 오프닝 시점에 합류하고 도주로 넘김',True),(399.9,'발견 직후 중단','수리공이 수상한 남자를 발견한 직후 체포 작전 카드',True)],
'C1eXfwC7uAw':[(43,'인과 질문 유예','표적과 피해자가 달라진 이유를 남기고 준비 단계로 회귀',False),(368.9,'해석 질문 재제기','총알의 정체를 다시 의문으로 두고 이견의 자료를 제시',False)],
'OwQm8ZIZfiQ':[(129.467,'규모/시간축 전환','첫 피해자와 총 피해 규모 뒤 인물의 과거로 이동',False),(230.733,'순환 연결','파리를 다시 호출하고 사건 당일로 복귀',False),(416.1,'새 질문','범행 종결 뒤 경찰은 어디 있었는지 질문',False),(472.867,'감정 정점 후 원인 전환','경찰 부재의 대비 뒤 동기를 검토',False)],
'nMg8D0I5GXc':[(29.967,'주제 선언','무기 공식 붕괴라는 명제를 남기고 드론을 설명',False)],
'wScaIvRspYc':[(45.733,'해답 유예','두 승리의 조건 설계를 질문한 뒤 첫 전투의 조건으로 이동',False),(463.4,'해법 유예','함대 상실·남은 전력을 제시한 뒤 다른 지형의 해법으로 이동',False)],
'E_DrBRjGAQI':[(40.64,'주제 안내 뒤 회상','민감 내용 안내 뒤 최초 단서 사건으로 이동',False),(114.16,'장벽/해법','익명성 장벽 뒤 거래 경로 설명',False),(196.68,'새 수사 단계','거래소 신원정보 뒤 사이트의 허점을 찾는 단계',False),(327.28,'장소/신원 전환','IP로 주택지역을 특정한 뒤 실제 신원과 체포로 이동',False),(457.84,'규모/결과 전환','추가 하드드라이브 뒤 포렌식 규모와 형량 결과',False)],
'_qQK1LZpyJI':[(160.68,'다른 욕망의 해답 유예','성적 만남 외의 이유를 예고하고 테이블 계급으로 이동',False),(273.24,'주제 전환','과시 소비를 회수하고 공간을 채우는 사람의 이야기로 전환',False)]}
SEG={
'H_GaGKQp17k':[(0,2.6,'출소 직후의 날짜'),(2.6,5.9,'집의 개를 관찰하는 인물'),(6.2,8.8,'칼로 해치는 행동'),(9.1,11.5,'피해 결과의 서술'),(11.5,13.7,'인물이 내릴 결론을 예고'),(14,18.4,'다른 도구가 필요하다는 판단'),(18.6,21.2,'직접 도구를 만든다는 설명'),(21.7,29,'해머의 손잡이 교체 과정'),(29,34.7,'도구의 무게와 인물 정체'),(35.3,41,'도구 사용과 다음 범행 예고'),(41,43,'장 카드; 발화 없음'),(43,49.2,'출생과 배경'),(49.4,56.5,'청소년기 범죄 전력'),(56.5,60,'수감과 출소의 반복')],
'w_LJ_GQObic':[(0,5.14,'날짜·새벽 시각·교도소 위치'),(5.14,10.22,'수감자가 조용히 일어남'),(10.4,13.72,'인물과 나이 소개'),(14.26,17.94,'오랜 준비의 실행 예고'),(18.28,23.12,'환풍구를 향해 손을 뻗음'),(23.4,28.6,'창살이 쉽게 제거되는 의문'),(28.6,35.16,'작은 개구부로 몸을 통과시킴'),(35.48,38.02,'건물 밖이어도 아직 탈옥 전'),(38.36,42.52,'공사장으로 이동'),(42.88,50.98,'벽이라는 장애물과 창살 도구'),(51.4,55.16,'파낸 구멍으로 통과'),(55.16,60,'파이프·밧줄로 다음 장애물 준비')],
'C1eXfwC7uAw':[(0,3.1,'공적 기념일의 날짜와 시각'),(3.1,7.4,'지하철 개통식 설명'),(7.7,12,'홀로 앉아 있는 대통령'),(12.3,17.5,'직전 사건으로 40분 되감는 예고'),(17.9,23.2,'총격 피해와 병원 이송'),(23.4,30.2,'생존 가능성에 대한 서술자의 추정'),(30.3,32.3,'범인 현장 체포'),(32.5,38.4,'원래 표적과 실제 피해자의 차이'),(38.8,42.7,'왜 빗나간 결과가 생겼는지 질문'),(43,45,'장 카드와 과거 전환'),(44.8,48.8,'9일 전으로 되감기'),(49.1,52,'공항으로 입국'),(52.4,60,'위장 신분과 숨긴 도구')],
'OwQm8ZIZfiQ':[(0,5.4,'날짜·시각·장소'),(5.4,9.72,'작은 파리가 잠든 인물에게 앉음'),(10.1,16.8,'작은 원인과 큰 피해 규모의 대비'),(17.06,22.82,'인물의 직업과 나이'),(23.04,26.76,'당일 근무와 휴식 상황'),(26.76,33.62,'파리를 잡으려던 동거인의 행동'),(33.82,36.1,'잠에서 깬 인물'),(36.5,40.04,'폭력이 시작됨'),(40.46,43.28,'피해 결과'),(43.28,47.36,'주변 인물의 제지'),(47.76,52.22,'제지자에게도 폭력 확대'),(52.22,58.24,'위험성을 별명으로 강조'),(58.5,60,'저녁 술자리로 시간 이동')],
'nMg8D0I5GXc':[(0,3.7,'전쟁의 접전 상황'),(3.7,8.4,'드론과 전차의 가격 대비'),(8.7,13.7,'과거 무기 우위의 일반 명제'),(14.2,25.8,'무기의 발전사를 열거'),(26.2,28.8,'기존 공식 붕괴'),(29,31.5,'장 카드'),(31.5,37.6,'FPV의 뜻과 취미 기술'),(37.7,43.9,'고글과 조종 시점'),(44.3,46.6,'전쟁터로 들어온 기술'),(46.8,56.7,'시청자를 지휘관으로 놓는 질문'),(57,60,'이전 폭탄 투하 방식 설명')],
'wScaIvRspYc':[(0,7.6,'두 함대 규모의 숫자'),(8.1,11.2,'열세 함대의 승리'),(11.6,19.1,'다른 전투의 더 큰 수적 차이'),(19.5,23.3,'두 번째 승리'),(24,26.4,'같은 지휘관이라는 공통점'),(26.4,36.1,'포위와 지형이라는 서로 다른 조건'),(36.4,42.3,'이길 조건을 어떻게 설계했는지 질문'),(42.6,45.1,'계산이라는 관점 제시'),(45.73,47.57,'장 카드'),(47.3,54,'주력 선박과 평평한 바닥'),(54,60,'다른 선박의 구조와 대비')],
'E_DrBRjGAQI':[(0,3.2,'날짜·아파트 지하주차장'),(3.3,7.2,'잠복과 기다림'),(7.5,9.2,'차가 도착함'),(9.7,13.3,'차에서 내린 인물의 정체'),(14,17.2,'경찰이 따라 엘리베이터에 탑승'),(17.5,22.2,'해외 수사팀의 기다림'),(22.7,29,'범죄 사이트와 체포의 규모'),(30.2,37.1,'영상 주제 안내'),(37.3,40.3,'민감 내용 안내'),(40.64,42.56,'장 카드'),(42.5,50,'다른 국가의 선행 체포 사건'),(50.2,54.2,'선행 피의자의 배경'),(54.2,60,'온라인에서의 위장 접근')],
'_qQK1LZpyJI':[(0,4.3,'퇴폐성과 인기의 모순'),(4.3,9.7,'대상 고객과 새벽 영업'),(9.7,12.2,'일반인 인기의 원인 질문'),(12.5,16.8,'공간에서 해답을 찾겠다는 약속'),(17,20.4,'장면 전환; 발화 공백'),(20.4,25.9,'위치와 개업 시점'),(25.9,30.8,'눈에 띄지 않는 외관'),(31.1,38.4,'간판 없는 공간의 태도 의인화'),(38.6,41.8,'같은 건물의 호텔'),(42.2,49.7,'클럽과 호텔의 동선'),(50.1,53.2,'영업일과 호텔 만실의 연결'),(53.6,59.4,'입구 가드와 선별 예고')]
}
for vid,cs in CLIFF.items():
 d=R/vid;rows=[{'boundary_s':t,'cliffhanger_type_manual':typ,'lead_or_question':desc,'strict_action_interruption':flag,'status':'manual semantic classification; not retention evidence'} for t,typ,desc,flag in cs];csvout(d/'chapter_cliffhangers.csv',rows);s=by[vid];s['strict_action_cliffhanger_count_manual']=sum(x[3] for x in cs);s['chapter_cliffhangers']=rows
 story=json.loads((d/'story.json').read_text());story['chapter_cliffhangers']=rows;(d/'story.json').write_text(json.dumps(story,ensure_ascii=False,indent=2))
 report=d/'analysis.md';text=report.read_text();text=text.replace('## 내레이터·장치',tab(['카드 시각','전환 종류','직전 약속/중단','행동 절벽'],[[t,typ,desc,'예' if flag else '아니오'] for t,typ,desc,flag in cs])+'\n\n## 내레이터·장치');report.write_text(text)
 first=read(d/'first60_log.csv')
 for row in first:
  t=float(row['start_s']);pieces=[txt for a,b,txt in SEG[vid] if b>t and a<t+1];row['narrative_summary']=' → '.join(pieces) if pieces else '발화 사이 짧은 간격 / 다음 절 준비'
 csvout(d/'first60_log.csv',first)
 # Quantitative sound candidates around loop resolutions, with explicit semantic uncertainty.
 ons=read(d/'audio_onsets.csv');revs=[]
 for loop in story['open_loops']:
  t=loop['closed_or_reframed_s'];closest=min(ons,key=lambda x:abs(float(x['time_s'])-t)) if ons else None;delta=float(closest['time_s'])-t if closest else None
  revs.append({'loop_id':loop['id'],'resolution_s':t,'nearest_mix_onset_s':closest.get('time_s') if closest else None,'delta_s':delta,'onset_within_0_1s_proxy':abs(delta)<=.1 if delta is not None else None,'onset_overlaps_asr_word':closest.get('speech_overlap') if closest else None,'sfx_or_music_hit_confirmed':None,'note':'spectral flux transient; may be speech consonant, music or SFX; not perceptual confirmation'})
 csvout(d/'reveal_audio_candidates.csv',revs);s['reveal_onset_share_proxy']=sum(x['onset_within_0_1s_proxy'] or False for x in revs)/len(revs)
 s['cliffhanger_coding_note']='strict action interruption separately counted; question withholding is not automatically action cliffhanger';(d/'summary.json').write_text(json.dumps(s,ensure_ascii=False,indent=2))
# Complete the retained 12 small key crops for the two reused references.
sys.path.insert(0,str(R));import measure_all as a
for vid,times in [('w_LJ_GQObic',[3,25,45,90,110,175,199,290,320,400,430,485]),('OwQm8ZIZfiQ',[1,14,45,82,120,131,200,255,330,370,446,491])]:
 d=R/vid;cap=a.cv2.VideoCapture(str(d/'analysis_proxy.mp4'));fps=by[vid]['fps'];a.sheet_frames(cap,times,fps,d/'frames_key.jpg',4,(320,180));kd=d/'key_frames';kd.mkdir(exist_ok=True)
 for i,t in enumerate(times):a.frame(cap,t*fps,(480,270)).save(kd/f'{i+1:02}_{t:.2f}s.jpg',quality=86)
 cap.release()
# Metadata language evidence, without retaining signed media URLs.
for s in A:
 d=R/s['id'];m=json.loads((d/'metadata.json').read_text());raw=json.loads((d/'media.info.json').read_text()) if (d/'media.info.json').exists() else {};m['extractor_format_description']=raw.get('format');m['extracted_audio_language']=raw.get('language');m['format_note_caveat']='For two reused media copies, selected format in fresh metadata is not the copy format; source_media.json ffprobe is authoritative.'
 keep=['id','title','description','upload_date','timestamp','duration','view_count','like_count','comment_count','chapters','channel','channel_id','channel_follower_count','webpage_url','categories','tags','language','availability','age_limit','analysis_kind','collected_local','counts_method','extractor_format_description','extracted_audio_language','format_note_caveat'];clean={k:m.get(k) for k in keep};(d/'metadata.json').write_text(json.dumps(clean,ensure_ascii=False,indent=2));s['audio_language_metadata']=m.get('extracted_audio_language')
(R/'all_summary.json').write_text(json.dumps(A,ensure_ascii=False,indent=2));rows=[]
for s in A:
 row={k:v for k,v in s.items() if k not in ['voice','sections','first3_log']}
 row.update({'voice_'+k:v for k,v in s.get('voice',{}).items()});row['chapter_sections']=s.get('sections');row['first3_log']=s.get('first3_log');rows.append(row)
csvout(R/'metrics.csv',rows)
cols=len(list(csv.DictReader((R/'metrics.csv').open())).pop().keys());p=R.parent/'extol_formula_all.md';text=p.read_text().replace('117열 metrics.csv',f'{cols}열 metrics.csv');text=text.replace('음향은 미확정','음향은 미확정');p.write_text(text)
print('enriched',len(A),'columns',cols)
