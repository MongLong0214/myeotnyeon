"""N18 picture-only correction. Reviewed picture/audio/script and engine are read-only."""
import json,re
from pathlib import Path
W=Path(__file__).resolve().parents[5]
E=W/'episodes/v4/n18/cartoon_v6'
data=json.loads((E/'episode_data.json').read_text())
original=data['shots']
# Keep original boundary positions where coverage adds information; remove redundant
# changes in scale. No new boundary is introduced inside a clause.
coverage=[
 (1,1,'collapse','wide','recruit'),
 (2,3,'court_wide','wide','judge_and_defendants'),
 (4,5,'ground_wide','wide','recruits'),
 (6,6,'barracks','wide','recruits_and_officer'),
 (7,7,'report','medium','deputy'),(8,10,'approve','medium','commander'),
 (11,12,'unchecked','wide','officer_and_unchecked_gauge'),(13,13,'order','medium','commander'),
 (14,14,'packing_wide','wide','six_recruits'),(15,18,'packing_side','medium','recruit_packing_books'),
 (19,21,'march','wide','marching_recruits'),(22,22,'race','medium','commander'),(23,23,'push','wide','recruits'),
 (24,25,'run','wide','running_recruits'),(26,26,'rule_ground','medium','officer_and_recruits'),
 (27,27,'collapse','wide','recruit'),(28,30,'fallen','wide','fallen_recruit_and_peers'),
 (31,32,'delay','medium','officer_and_fallen_recruit'),
 (33,34,'medical_care','wide','medics_and_patient'),(35,35,'medical_transfer','wide','sokcho_transfer'),
 (36,36,'medical_transfer','wide','gangneung_transfer'),(37,38,'medical_results','medium','medic_reviewing_results'),
 (39,39,'medical_report','medium','doctor_reviewing_record'),(40,43,'medical_review','wide','doctor_and_patient_record'),
 (44,45,'loss','wide','medics_and_patient'),(46,46,'record','wide','record_reader'),(47,49,'letter','wide','letter_reader'),
 (50,53,'witness_wide','wide','four_witnesses'),(54,55,'witness_books','medium','witness'),
 (56,57,'rebuke','wide','commander_and_fallen_recruit'),(58,58,'patient_reverse','medium','fallen_recruit_and_peer'),
 (59,61,'witness_reaction','medium','witness_reaction'),(62,63,'prosecution','wide','prosecutor_reviewing_evidence'),
 (64,65,'court_indict_wide','wide','two_defendants_and_prosecutor'),(66,67,'court_counsel','medium','defense_counsel'),
 (68,70,'court_judge','medium','judge_answering_defense'),(71,73,'court_defendants','medium','two_defendants_reacting'),
 (74,74,'court_page','medium','judge_turning_page'),(75,75,'court_reaction','medium','two_defendants_reacting'),
 (76,78,'court_judge','medium','judge_reading_sentencing_reasons'),(79,82,'court_defendants','medium','two_defendants_awaiting_sentence'),
 (83,84,'court_distinguish','medium','judge_distinguishing_findings'),(85,89,'court_prosecutor','medium','prosecutor_requesting_sentence'),
 (90,92,'court_wide','wide','judge_delivering_sentence'),(93,94,'court_commander','medium','commander_reaction'),
 (95,97,'appeal_wide','wide','appeal_judge_and_defendants'),(98,100,'appeal_files','medium','counsel_reviewing_individual_records'),
 (101,104,'court_judge_reverse','medium','appeal_judge_reviewing_records'),(105,106,'court_commander','medium','commander_reaction'),
 (107,108,'court_deputy','medium','deputy_reaction'),(109,113,'court_judge_reverse','medium','appeal_judge_delivering_reasons'),
 (114,115,'court_defendants','medium','two_defendants_reacting'),(116,116,'supreme_wide','wide','supreme_court'),
 (117,117,'court_commander','medium','commander_final_status'),(118,118,'court_deputy','medium','deputy_final_status'),
 (119,119,'court_records','medium','clerk_separating_case_records'),
 (120,122,'policy_wide','wide','briefing_speaker_and_listeners'),(123,123,'policy_speaker','medium','briefing_speaker'),
 (124,125,'policy_listen','wide','recruit_and_listening_officer'),(126,126,'policy_authorize','medium','approval_authority'),
 (127,134,'policy_checks','wide','officer_recruit_medic'),(135,136,'policy_calendar','medium','speaker_reviewing_annual_schedule'),
 (137,137,'policy_measure','medium','officer_reading_gauge'),(138,139,'policy_field','wide','officer_looking_from_plan_to_recruit'),
 (140,141,'memorial_wide','wide','mourner_looking_at_empty_chair_and_certificate'),
 (142,143,'memorial_flowers','medium','mourner_placing_flower'),(144,145,'memorial_letter','wide','mourner_empty_chair_and_letter'),
 (146,146,'farewell','wide','recruit_and_parents_letter_memory'),(147,148,'yongsan','wide','parents_receiving_mourner'),
 (149,150,'closing','wide','parents_and_mourner_held'),
]

descriptions={'collapse': '달리던 비식별 훈련병이 몸의 균형을 잃고 지면에 쓰러진다. 주변 인물은 쓰러진 쪽을 바라본다.', 'court_wide': '법정 설정 숏. 판사가 작은 판결문에서 고개를 들어 두 피고인을 향한다. 설명판 없음.', 'ground_wide': '연병장과 비식별 훈련병들을 함께 보여 주고 간부의 명령 손짓을 연결한다.', 'barracks': '생활관에서 마주한 훈련병들이 간부 쪽으로 고개를 돌린다. 간부는 대화하던 쪽을 가리킨다.', 'report': '실제 측면 그림의 부중대장이 중대장을 향해 보고하는 손을 펼친다. 상대는 뒷모습으로 듣는다.', 'approve': '역방향 구도의 중대장이 손을 펼쳐 승인한다. 작은 책상 문서와 절차를 거치지 않은 명령을 함께 둔다.', 'unchecked': '훈련병과 온도지수계를 한 공간에 둔다. 간부는 확인 대상으로 시선을 두지 않고 명령 쪽으로 손을 향한다.', 'order': '측면의 중대장이 훈련병들을 향해 팔을 편다. 훈련병은 뒷모습으로 명령 쪽을 본다.', 'packing_wide': '보급품 보관 공간 안 여섯 비식별 훈련병과 결속할 군장을 한 설정 숏에 둔다.', 'packing_side': '별도로 그린 측면의 훈련병이 책 더미를 들어 군장 입구로 옮기고 넣는다. 빈 선반과 군장을 같은 공간에 둔다.', 'march': '완전군장과 총기를 휴대한 여섯 훈련병이 오른쪽으로 걸어간다. 걸음은 내레이션의 훈련 동작이다.', 'run': '완전군장 훈련병들이 오른쪽으로 달린다. 정면 도형 확대 대신 달리는 동작을 유지한다.', 'race': '측면 중대장이 팔을 펴 달리는 방향을 지시하고 훈련병들이 오른쪽으로 이동한다.', 'push': '측면으로 그린 훈련병들의 팔굽혀펴기 동작. 얼굴과 신원을 드러내지 않는다.', 'rule_ground': '간부의 뒷모습과 군장 훈련병들을 함께 둬 규정 위반이라는 논평의 대상을 유지한다.', 'fallen': '쓰러진 훈련병 곁 동료가 고개를 낮춰 상태를 바라본다. 특정 응급 시술은 추가하지 않는다.', 'delay': '쓰러진 훈련병과 바라보는 간부를 함께 유지한다. 응급처치 지체를 설명하는 동안 구조 행동을 꾸며 넣지 않는다.', 'medical_care': '얼굴을 식별할 수 없는 환자와 의료진. 의료진의 손과 시선이 환자를 향하고 구급가방을 연다. 특정 시술 없음.', 'medical_transfer': '서로 다른 병원 공간에서 침상과 의료진이 오른쪽으로 이동한다. 의료진은 이동에 맞춰 걷는다.', 'medical_report':'별도 측면의 의료 관계자가 작은 검사 기록을 읽고 시선을 든다. 관계자의 설명으로 전달하며 실제 장기 손상이나 확정 진단을 그리지 않는다.', 'medical_results': '의료진이 환자 곁 작은 검사 기록을 살피고 고개를 든다. 장기 손상이나 고어를 확대하지 않는다.', 'medical_review': '의료진이 침상 옆 기록을 읽은 뒤 환자를 향해 시선을 올린다. 병원 사이 전체 경과라는 내레이션을 한 숏으로 받는다.', 'loss': '중환자실의 의료진이 환자를 향한 손을 내리고 정지한다. 사망 사실 뒤의 침묵과 환자 비식별 상태를 유지한다.', 'record': '익명의 기록 검토자가 사인 보도를 읽는다. 어머니나 실제 관계자의 행동을 재현하지 않는다.', 'letter': '익명의 기록 독자가 편지의 행을 짚고 잠시 고개를 든다. 전화기는 책상 소품이며 수신 재연을 하지 않는다. H049 자막은 편지에 기록된 통화라고 명시한다.', 'witness_wide': '법정 설정 숏에 비식별 동료 증인 네 명을 보여 준다. 가운데 증인이 재판부 쪽으로 고개와 손을 향한다.', 'witness_books': '측면 증인이 책과 군장에 대한 증언을 손으로 설명한다. 군장 소품은 작게 두며 실제 무게를 제시하지 않는다.', 'rebuke': '동료 증언의 재구성. 쓰러진 비식별 훈련병을 향해 중대장이 팔과 상체를 기울여 질책한다. 창작 대사와 추가 타격 없음.', 'patient_reverse': '동료의 뒤 어깨 너머에서 쓰러진 훈련병을 바라보는 역방향 구도. 고통의 얼굴을 확대하지 않는다.', 'witness_reaction': '측면 증인이 손을 낮추고 고개를 숙인 뒤 재판부 쪽으로 조금 든다. 진단과 아쉬움은 해당 증인의 진술로 유지한다.', 'prosecution': '검사가 책상 위 자료를 차례로 짚고 읽은 뒤 시선을 올린다. 방식·경과·신체조건의 종합 판단을 인물의 검토로 연결한다.', 'court_indict_wide': '검사의 발언과 두 피고인, 판사를 한 설정 숏에 둔다. 설명판 대신 기소를 듣는 구도와 손짓을 보여 준다.', 'court_counsel': '진짜 측면 그림의 변호인이 재판부를 향해 손바닥을 편다. 피고인의 뒷모습이 반응의 대상으로 연결된다.', 'court_judge': '피고인 어깨 너머 실제 측면 판사가 판결문에서 고개를 들어 답한다. 작은 종이는 책상 위 소품이며 인물을 가리지 않는다.', 'court_defendants': '3/4 중대장과 측면 부중대장이 재판부를 향하다 고개를 낮춘다. 유죄·책임·용서 및 양형을 듣는 반응 숏.', 'court_page': '측면 판사가 작은 문서의 다음 장으로 손을 옮긴다. 다음 양형 이유라는 발화에 동기를 둔 컷.', 'court_reaction': '같은 재판을 듣는 두 피고인의 별도 3/4·측면 반응. 반성 태도 참작은 자막으로 전달하며 속마음을 창작하지 않는다.', 'court_distinguish': '판사가 두 작은 문서 옆에서 손을 멈추고 피고인을 향한다. 판단과 양형의 구별은 자막으로 전달하며 도해를 쓰지 않는다.', 'court_prosecutor': '측면 검사가 재판부를 향해 구형 의견을 제시한다. 10년·7년과 요청/선고의 구별은 자막으로 이어진다.', 'court_commander': '3/4 중대장 단독 반응과 변호인의 뒤 어깨. 선고·항소·확정 수치는 자막만 사용한다.', 'court_deputy': '중대장 숏과 다르게 그린 측면 부중대장 단독 반응. 독립된 항소·확정 상태를 전달한다.', 'appeal_wide': '항소심 설정 숏. 판사가 작은 기록을 살핀 뒤 두 피고인 쪽을 본다. 상상적 경합 설명은 자막에 둔다.', 'appeal_files': '측면 법률 검토자가 사람별 기록을 별도로 펼치고 차례로 짚는다. 여섯 사람을 범죄 여섯 개로 계산하지 않으며 도해를 쓰지 않는다.', 'court_judge_reverse': '별도 3/4 판사가 개인별 기록에서 시선을 들어 판단을 전달한다. 생명 보호 책임이라는 발화 뒤 시선을 유지한다.', 'supreme_wide': '대법원 상고심을 설명하는 법정 설정 숏. 판사와 피고인의 거리를 두고 결정을 듣는 시선을 연결한다.', 'court_records': '기록 검토자가 서로 떨어진 두 작은 사건 기록을 정리한다. 같은 날 본안 판단을 받은 장면으로 재현하지 않는다.', 'policy_wide': '브리핑 설정 숏. 발표자의 시선·손짓과 듣는 관계자의 뒷모습을 연결한다. 설명판 없음.', 'policy_speaker': '별도로 그린 측면 발표자가 작은 발표문에서 손을 들어 대책을 전달한다. 체력단련 종목 제외 내용은 자막에 둔다.', 'policy_listen': '발표된 대책의 개념 재구성. 훈련병의 소명을 간부가 마주 보고 듣는다. 사건 당시 실제로 이행됐다고 표현하지 않는다.', 'policy_authorize': '상급 간부가 작은 승인 자료로 손과 시선을 옮긴다. 승인권자 상향 내용은 자막으로 전달한다.', 'policy_checks': '발표된 절차의 개념 재구성. 간부가 훈련병의 상태를 살피고 온도지수계로 몸과 시선을 돌린다. 의료진은 응급가방을 연다. 세 항목을 말하는 동안 하나의 공간을 유지한다.', 'policy_calendar': '발표자가 작은 연간 일정 자료를 넘겨 읽는다. 제도상 반복 기간은 연도를 임의로 채우지 않은 숫자 월일 자막으로 표시한다.', 'policy_measure': '측면 간부가 온도지수계를 읽고 작은 기록지 쪽에 손을 옮긴다. 당일 기온 수치는 만들지 않는다.', 'policy_field': '간부가 계획 자료를 읽다가 훈련병 쪽으로 시선을 든다. 발표와 실제 안전의 간극을 인물의 시선으로 연결한다.', 'memorial_wide': '추모객의 뒷모습 너머 빈 의자와 작은 명예수료증을 함께 보여 준다. 빈자리를 바라보는 시선을 의도적으로 유지한다.', 'memorial_flowers': '측면 추모객이 몸을 숙여 국화를 놓고 손을 거둔다. 이후 조문 자세를 유지한다.', 'memorial_letter': '빈 의자와 추모객, 작은 편지를 같은 장면에 둔다. 어머니의 실제 현장 행동을 추가하지 않고 편지 속 부재를 받아낸다.', 'farewell': '편지에 기록된 입영 날 기억. 비식별 아들이 부모 손을 잡고 등을 한 차례 다독인다. 추가 대사·행동 없음.', 'yongsan': '용산역 분향소에서 비식별 부모가 다가온 조문객을 맞고 고개를 숙인다. 걸음은 접근 행동에만 사용한다.', 'closing': '같은 조문 공간에서 유족과 조문객의 숙인 시선을 유지한다. 마지막 책임에 대한 발화를 새 패널이나 확대 없이 받는다.'}
shots=[]
for a,b,drawing,size,subject in coverage:
 rows=original[a-1:b];s=dict(rows[0]);s.update(end=rows[-1]['end'],end_s=rows[-1]['end_s'],source_ids=[r['id'] for r in rows],drawing=drawing,shot_size=size,size=size,subject=subject,text=' '.join(r['text'] for r in rows),character_acting=True,review='PENDING_EXTERNAL_REVIEW',review_note='No producer MATCH or acceptance claim.',angle_note='N18-local separately drawn profile, quarter and rear views; no crop angle claim.',camera_zoom=1,shows=drawing.replace('_',' ')+' — '+subject.replace('_',' '),index=len(shots))
 s.pop('angle_deg',None)
 s['shows']=descriptions[drawing]
 s['facts']=list(dict.fromkeys(v for r in rows for v in r.get('facts',[])))
 shots.append(s)
assert shots[0]['start']==0 and shots[-1]['end']==data['durationInFrames']
assert all(a['end']==b['start'] for a,b in zip(shots,shots[1:]))
assert all(s['start'] in {r['start'] for r in original} for s in shots)
for c in data['captions']:
 c['text']=re.sub(r'(\d{4})년\s*(\d{1,2})월\s*(\d{1,2})일',lambda m:f'{int(m[1]):04d}-{int(m[2]):02d}-{int(m[3]):02d}',c['text'])
 c['text']=c['text'].replace('5월 23일','2024-05-23').replace('7월 1일','07-01').replace('6월 1일','06-01').replace('8월 31일','08-31')
 if c['shotId']=='H144' and c['start']==11240:c['text']='[어머니 편지] '+c['text']
 if c['shotId']=='H049':c['text']='[어머니 편지에 기록된] 아들이 쓰러졌다는 전화.'
 if c['shotId']=='H124' and c['start']==9784:c['text']='[발표된 대책의 개념 재구성] '+c['text']
 if c['shotId']=='H056' and c['start']==4036:c['text']='[동료 법정 증언] '+c['text']
 if c['shotId']=='H146' and c['start']==11419:c['text']='[편지 속 기억] '+c['text']
 if c['shotId']=='H135' and '07-01' in c['text']:c['text']=c['text'].replace('혹서기 관리는','매년 혹서기 관리는')
 if c['shotId']=='H136':c['text']=c['text'].replace('끝은 같은','종료일은 같은')
for n in data['narration']:
 n['start_s']=n['start'];n['end_s']=n['end']
data['shots']=shots
(E/'episode_data_v6fix.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
(E/'shots_v6fix.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
print(f'{len(original)} original shots -> {len(shots)} motivated coverage shots; {len(original)-len(shots)} redundant cuts removed; no new cut times.')
