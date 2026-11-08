"""Narration-first staging. Each entry is a sentence; | separates clause cuts."""
import re
from audio import script

# location, action, visible subject, staging. No generic narrator substitutes facts.
P={
'N001':[('ground','collapse','recruit','군장 훈련 중 달리던 비식별 훈련병이 균형을 잃고 지면에 쓰러진다.')],
'N002':[('court','judge','judgment','법정 전경과 판사, 학대치사 유죄 판결문.'),('court','purpose','judgment','판사가 교육 목적을 양형 이유로 짚는 판결문을 읽는다.')],
'N003':[('ground','date','training_base','2024-05-23 사건 날짜와 연병장 전경.'),('ground','establish','training_base','2024-05-23 날짜와 강원 인제 육군 12사단 신병교육대 연병장 전경.')],
'N004':[('barracks','talk','recruits','경찰 수사결과 표기. 취침점호 뒤 생활관에서 이야기하던 비식별 훈련병들을 간부가 적발한다.')],
'N005':[('command','report','deputy','부중대장이 중대장을 향해 구두 보고한다.'),('command','approve','commander','같은 책상 반대편 중대장이 보고를 승인한다.')],
'N006':[('command','missing','documents','책상 위 미작성 확인서와 빠진 소명 절차, 승인된 훈련 명령을 함께 보여 준다.'),('command','rule','documents','중대장의 손 옆 규정집과 미확인 절차를 강조한다.')],
'N007':[('ground','unchecked','health_weather','훈련병과 훈련장 온도지수 확인표의 빈 칸. 실제 기온 수치는 만들지 않는다.')],
'N008':[('ground','basic','health_weather','훈련병 상태 확인표를 앞에 놓고 기본 점검 항목을 짚는다.'),('ground','order','commander','논평 표기. 확인표를 건너뛴 간부의 명령 손짓.')],
'N009':[('packing','six','six_recruits','장비실 전경. 비식별 훈련 대상 여섯 명을 한 화면에 보여 준다.'),('packing','incomplete','rucksack','보급품이 부족한 열린 군장과 빈 보급 선반.'),('packing','books','rucksack','보급품을 다 받지 못한 군장 빈 부분에 책을 넣는 손과 군장.')],
'N010':[('packing','contrast','rucksack','논평 표기. 빈 안전 확인표에서 책이 든 군장으로 시선을 유도한다.'),('packing','pack','rucksack','책을 넣은 군장이 무겁게 놓인 채 다음 경과를 묻는다.')],
'N011':[('ground','clock','training_base','연병장 전경에 시작 시각 16:26경.'),('ground','march','recruits','총기와 완전군장을 휴대한 훈련병들. 모두 같은 방향으로 이동.')],
'N012':[('ground','march','recruits','연병장을 걷는 여섯 훈련병, 두 바퀴 표기.'),('ground','race','commander','중대장 지시에 따라 같은 진행방향으로 선착순 뜀걸음을 시작한다.')],
'N013':[('ground','push','recruits','완전군장 상태로 지면을 짚고 팔굽혀펴기를 하는 훈련병들.'),('ground','run','recruits','같은 연병장에서 완전군장 뜀걸음, 세 바퀴 표기.'),('ground','pack_detail','rucksack','완전군장을 휴대한 훈련병들과 군장·끈을 가까이 보여 준다.')],
'N014':[('ground','rule','documents','논평. 군기훈련 규정집과 위반된 훈련 장면을 함께 짚는다.')],
'N015':[('ground','collapse','recruit','17:11경. 뛰던 비식별 훈련병이 지면에 쓰러지고 주변 동료가 멈춘다.'),('ground','elapsed','recruit','쓰러진 훈련병의 같은 위치를 유지. 16:26→17:11, 약 45분 경과.')],
'N016':[('ground','stopped','recruit','쓰러진 훈련병 곁에서 훈련 동작을 멈춘다.'),('ground','emergency','recruit','논평. 쓰러진 훈련병과 응급조치가 필요했던 상황을 표시. 즉시 처치가 이뤄졌다고 재연하지 않는다.')],
'N017':[('ground','delay','officers_patient','경찰 수사결과 표기. 쓰러진 훈련병과 간부들 사이 응급 인지·처치 지체를 시계로 표현한다.')],
'N018':[('ground','patient','recruit','논평. 내려놓은 군장보다 쓰러진 사람에게 시선을 모은다.'),('infirmary','record','medical_record','의무대 전경과 병원 이송 기록. 장소 전환을 기록 페이지 넘김으로 동기화.')],
'N019':[('infirmary','care','patient','의무대에서 들것의 환자 상태를 살피는 비식별 의료진.'),('sokcho','arrival','sokcho_hospital','속초의료원 표시가 있는 건물로 같은 방향의 들것 이송.'),('gangneung','arrival','gangneung_hospital','강릉아산병원 표시가 있는 병원 입구로 같은 방향 이송.')],
'N020':[('gangneung','fever','medical_record','이송 당시 기록에 40°C 초과 고열. 특정 체온 수치는 만들지 않는다.'),('gangneung','urgent','patient','긴급한 상태의 환자와 살피는 의료진, 진지한 호흡.')],
'N021':[('sokcho','damage','medical_record','속초의료원 도착 때 검사 기록. 장기 손상 의심·중증, 관계자 설명임을 표시한다.')],
'N022':[('gangneung','arrival_time','hospital','강릉아산병원 전경과 21:40경 도착 기록.'),('gangneung','transfer_interval','medical_record','속초의료원 출발·강릉아산병원 도착을 기록에서 이어 약 3시간 전체 경과를 보여 준다.')],
'N023':[('gangneung','transfer_interval','medical_record','두 병원 사이 기록 전체를 한 장에 보여 준다.'),('gangneung','not_drive','medical_record','전체 경과 약 3시간과 차로 달린 시간 미확정을 명확히 구분한다.')],
'N024':[('icu','treatment','patient','중환자실 전경. 환자와 의료진의 치료가 이어진다.'),('icu','loss','patient','같은 병상에서 움직임을 멈추고 2024-05-25 사망을 엄숙하게 표시. 희화화 없음.')],
'N025':[('record','cause','medical_record','수사결과 보도의 사인 기록: 열사병에 의한 다발성 장기부전. 신체 내부 묘사 없음.')],
'N026':[('family','letter','mother_letter','가족 공간 전경. 비식별 어머니의 편지와 첫 전화 기록.'),('family','call_time','phone','편지 옆 전화기와 05-23 17:54 기록.'),('family','phone','mother','뒷모습 어머니가 아들이 쓰러졌다는 전화를 받는다. 현장 대사 합성 없음.')],
'N027':[('court','witness_wide','witnesses','법정 전경. 살아남은 동료들이 증인석에 선다.'),('court','witness','witness','증인석의 동료가 당시 장면을 증언한다.')],
'N028':[('court','witness_date','witnesses','2024-08-27 공판. 동료 증인 네 명을 보여 준다.'),('court','four_witnesses','witnesses','증인 네 명과 증인석. 사건 대상 여섯 명과 구분.')],
'N029':[('court','book_testimony','rucksack','증언 재구성 표기. 증인 옆 책이 든 군장, 약 40권이라는 증언.'),('court','not_weight','rucksack','같은 군장 곁 약 40권은 증언이고 실제 무게 확정치가 아님을 표시.')],
'N030':[('ground_testimony','rebuke','commander_patient','법정 증언 재구성. 이미 쓰러진 훈련병을 향해 중대장이 질책하는 손짓과 입 모양. 타격·창작 대사 없음.')],
'N031':[('ground_testimony','rebuke','commander_patient','같은 위치의 쓰러진 훈련병과 질책하는 중대장, 증언임을 유지.'),('ground_testimony','patient','recruit','위급한 상황에서 쓰러진 훈련병의 상태로 시선을 옮긴다.')],
'N032':[('court','distress','witness','증인석의 동료 한 명이 진단 사실을 밝힌다. 외상 후 스트레스 장애 표기.'),('court','distress','witness','논평. 같은 증인을 중심에 두고 생존 이후에도 남는 후유증을 무겁게 보여 준다.')],
'N033':[('court','regret','witness','동료 증인 한 명이 빠른 처치에 대한 아쉬움을 말한다. 의학적 확정이 아닌 증인 심경 표시.')],
'N034':[('prosecution','investigate','prosecutor','검찰 사무실 전경. 검사가 사건 자료를 검토한다.'),('prosecution','evidence','evidence','훈련 방식·진행 경과·신체조건 기록을 펼쳐 학대 판단에 연결한다.')],
'N035':[('court','indict','defendants','법정 전경. 중대장·부중대장 두 피고인과 학대치사·직권남용 가혹행위 기소 문서.'),('court','indict','indictment','논평. 훈련이라는 표제 아래 드러난 기소 혐의 기록.')],
'N036':[('court','defense','defense','중대장 측 변호인이 잘못된 행동 인정과 학대치사 부인을 주장한다.'),('court','defense','defense','변호인 측 주장이라는 표기를 유지하고 발언자를 보여 준다.')],
'N037':[('court','judge','judge','반대편 판사로 역숏. 법원의 답.'),('court','guilty','judgment','판사와 두 피고인. 1심 유죄, 훈련과 사망 사이 인과관계를 판결문에 표시.')],
'N038':[('court','unfit','judgment','판사가 신체조건에 맞지 않은 훈련과 무거운 죄책을 판결문에서 짚는다.')],
'N039':[('court','trust','judgment','군 사기·전투력·국민 신뢰 훼손이라는 재판부 판단을 문서로 보여 준다.'),('court','trust_comment','judgment','논평 표기. 군의 신뢰를 무너뜨린 책임을 같은 판결문과 두 피고인에 연결한다.')],
'N040':[('court','no_forgiveness','judgment','판결문에 피해자 측 용서를 받지 못한 점.'),('court','turn_page','judgment','판사가 같은 판결문의 다음 이유 페이지로 손을 옮긴다.')],
'N041':[('court','remorse','defendants','1심 양형 이유 문서와 두 피고인. 사실관계 인정·반성 태도 참작.')],
'N042':[('court','purpose','judgment','판사와 판결문. 군 기강 확립을 위한 교육 목적 참작, 유죄 판단 병기.')],
'N043':[('court','purpose','judgment','교육 목적이라는 판결문 구절.'),('court','purpose_comment','judgment','논평. 유죄인 훈련에 교육 목적을 고려한 판결문.'),('court','sentence_question','judgment','선고형을 묻는 판결문 페이지. 숫자는 아직 공개하지 않는다.')],
'N044':[('court','not_acquittal','judgment','무죄 아님을 분명히 하는 판결문.'),('court','guilty','judgment','학대치사 유죄라는 판결문 구절.'),('court','purpose','judgment','교육 목적은 양형 이유라는 별도 항목.')],
'N045':[('court','distinguish','judgment','목적 참작과 행위 정당화를 나눈 판결문 해설.'),('court','distinguish','judgment','같은 문서에서 유죄 판단과 양형 이유를 분명히 구분한다.')],
'N046':[('court','prosecutor_date','prosecutor','2024-11-12 검찰 구형. 검사와 두 피고인.'),('court','request_a','commander','중대장에게 징역 10년 구형을 요청하는 검사와 중대장.'),('court','request_b','deputy','부중대장에게 징역 7년 구형을 요청하는 검사와 부중대장.')],
'N047':[('court','request_only','prosecutor','검사의 구형 문서: 요청이며 선고 아님.'),('court','trust_request','prosecutor','검사와 구형 이유 문서. 지도력·관리체제 신뢰 훼손.')],
'N048':[('court','verdict_date','court','2025-01-07 춘천지법 선고. 법정 전경.'),('court','sentence_a','commander','판사를 향한 중대장과 징역 5년 선고.'),('court','sentence_b','deputy','같은 자리 부중대장과 징역 3년 선고.')],
'N049':[('court','compare','judgment','검찰 요청과 1심 선고를 나란히 둔 기록.'),('court','not_final','commander','중대장 1심 5년 옆 다음 심급 문서, 아직 최종 숫자가 아님.')],
'N050':[('appeal','appeal','judgment','항소심 법정 전경. 하나의 행위로 묶는 판단이 바뀌는 문서.')],
'N051':[('appeal','group','legal_diagram','법정 안 설명판. 하나의 행위에서 여러 범죄로 이어지는 상상적 경합 도해.'),('appeal','group','legal_diagram','같은 도해를 가까이: 죄는 여러 개, 행위는 하나.')],
'N052':[('appeal','separate','legal_diagram','항소심 문서와 도해. 같은 장소·기회만으로 하나로 묶지 않는 판단.')],
'N053':[('appeal','individual','six_recruits','피해자마다 다른 피해를 설명하는 비식별 여섯 인물과 분리된 기록.'),('appeal','individual','six_recruits','각 인물별 기록으로 시선을 이동. 특정 미확인 추가 폭행은 그리지 않는다.')],
'N054':[('appeal','plural','legal_diagram','여러 행위에서 여러 죄로 이어지는 실체적 경합 도해.'),('appeal','plural','legal_diagram','사람별 피해 구분이 쟁점이라는 설명판.')],
'N055':[('appeal','ungroup','six_recruits','논평. 여섯 사람을 감싼 한 개 테두리가 열리고 인물별 틀이 보인다.'),('appeal','not_six_crimes','legal_diagram','정확히 죄 6개 계산이 아님을 설명하는 도해. 미확정 죄수 숫자 없음.')],
'N056':[('appeal','appeal_date','commander','2025-06-18 항소심. 중대장에게 징역 5년 6개월.'),('appeal','increase','commander','같은 중대장과 1심 5년→항소심 5년 6개월, +6개월.')],
'N057':[('appeal','deputy_sentence','deputy','부중대장 징역 3년 유지.'),('appeal','separate_reason','deputy','부중대장 기록을 중대장 증형 이유와 구분해 보여 준다.')],
'N058':[('appeal','judge','judge','항소심 재판부로 시선 이동.'),('appeal','preventable','judgment','충분히 예방할 수 있었던 사망사고라는 항소심 지적.')],
'N059':[('appeal','culture','judgment','후진적 병영문화 답습이라는 항소심 판결문.'),('appeal','preventable','judgment','예방할 수 있었다는 판결문 구절과 무겁게 내려놓는 판사의 손.')],
'N060':[('appeal','duty','judgment','국가의 생명·신체 보호에 대한 사회 기본 기대 배반이라는 판결문과 판사.')],
'N061':[('appeal','safe_return','judgment','논평. 판결문 속 생명·신체 보호 의무.'),('appeal','baseline','judgment','생명과 안전 보호가 기본이라는 논평 문구, 같은 판결 기록.')],
'N062':[('supreme','dismiss','supreme','대법원 전경과 2025-09-25 중대장 상고 기각 기록.'),('supreme','final_a','commander','중대장 징역 5년 6개월 확정 문서.')],
'N063':[('supreme','final_b','deputy','부중대장 징역 3년 확정 상태 문서, 확정일 미표기.'),('supreme','not_same_day','records','두 사람의 문서를 나누고 부중대장 확정일 미채택을 명시한다.')],
'N064':[('policy','policy','policy_document','국방부 대책 문서와 브리핑 공간 전경.'),('policy','policy','policy_document','군이 바꾸겠다고 발표한 대책 문서를 펼친다.'),('policy','basic','policy_document','대책 문서의 기본 절차 항목으로 시선을 모은다.')],
'N065':[('policy','exclude_exercise','policy_document','2024-06-27 국방부 발표. 훈련병 군기훈련 체력단련 제외, 일반 체력훈련 전체 금지 아님.')],
'N066':[('policy','explain','policy_document','개인 소명 단계를 포함한 표준 절차 문서.'),('policy','missing_explain','policy_document','사건에서 빠진 소명 단계와 대책의 필수 단계를 비교한다.')],
'N067':[('policy','authorize','policy_document','육군 신병교육부대 승인권자를 영관급 지휘관으로 높이는 대책 문서.')],
'N068':[('policy','health','policy_document','대책 문서의 건강상태 수시 확인 항목.'),('policy','weather','policy_document','기상에 따라 진행 판단하는 항목. 실제 당일 기온 없음.'),('policy','emergency_plan','policy_document','응급상황 대비 후 시행하는 항목.')],
'N069':[('policy','health','policy_document','사람 확인 항목과 인체 상태 확인 그림.'),('policy','weather','policy_document','날씨 확인 항목과 온도지수계 그림.'),('policy','emergency_plan','policy_document','응급상황 준비 항목과 구급가방.'),('policy','basic','policy_document','논평. 기본 절차 문서, 신기술이 아니라는 점.'),('policy','basic','policy_document','훈련 전 기본 점검 문서와 비식별 훈련병.')],
'N070':[('policy','summer','calendar','혹서기 관리 달력. 07-01 시작→06-01 시작으로 확대.'),('policy','summer_end','calendar','같은 대책 발표 화면에서 종료일 08-31을 숫자로 표시.')],
'N071':[('policy','measure','temperature','온도지수계와 하루 3회 이상 측정 기록.'),('policy','implementation','policy_document','논평. 발표 문서를 현장 안전 확인표와 연결한다.')],
'N072':[('policy','list','policy_document','발표된 대책 목록.'),('memorial','empty','memorial','훈련병을 기다린 비어 있는 수료 자리와 추모 공간 전경.')],
'N073':[('memorial','certificate','certificate','2024-06-19 인제체육관 수료식장 추모 공간. 명예수료증을 보여 준다.')],
'N074':[('memorial','flowers','mourners','비식별 참석자가 국화꽃을 놓고 고인을 추모한다.'),('memorial','space','memorial','수료식 안에 마련된 같은 추모 공간과 조문객.')],
'N075':[('memorial','mother_letter','mother_letter','어머니 편지: 수료생 251명 가운데 아들 부재.'),('memorial','empty','empty_chair','한 사람의 빈 자리. 고인의 신원·얼굴 없음.')],
'N076':[('entrance_memory','farewell','family','편지 속 입영 날의 기억 재구성. 비식별 아들이 부모 손을 잡고 등을 다독인다.')],
'N077':[('yongsan','mourners','parents','그날 저녁 용산역 분향소 전경. 뒷모습 부모가 조문객을 맞는다.'),('yongsan','bow','parents','같은 분향소에서 비식별 부모와 추모객이 마주 선다.')],
'N078':[('yongsan','guilty','judgment','분향소 곁 판결 기록. 법원이 인정한 학대치사.'),('yongsan','end','memorial','생명과 안전의 책임을 말하는 마지막 추모 공간. 엄숙하게 정지한다.')],
}

# The following onsets are grammatical clause boundaries inside one sentence.
C={
'N005_01':['중대장이'],
'N009_02':['군장의'],
'N019_01':['속초의료원으로,','다시'],
'N024_01':['쓰러진'],
'N046_01':['중대장 징역','부중대장 징역'],
'N048_02':['부중대장'],
'N068_01':['기상에','응급상황'],
}

def beats():
 groups={}
 for r in script():groups.setdefault(r['narrationId'],[]).append(r)
 out=[]
 for nid,sentences in groups.items():
  texts=[]
  for r in sentences:
   parts=[r['text']]
   for marker in C.get(r['id'],[]):
    tail=parts.pop();a,b=re.split(r'(?<!\S)(?='+re.escape(marker)+r')',tail,maxsplit=1);parts.extend([a.strip(),b.strip()])
   texts.extend([(r,t) for t in parts])
  specs=P[nid]
  if len(texts)!=len(specs):raise ValueError((nid,len(texts),len(specs),[t for _,t in texts]))
  for (r,t),(loc,action,subject,desc) in zip(texts,specs):
   out.append(dict(sentenceId=r['id'],narrationId=nid,text=t,location=loc,action=action,subject=subject,shows=desc,facts=r['facts'],serious=r['beat']=='serious' or loc in ['infirmary','sokcho','gangneung','icu','record','family','ground_testimony','memorial','entrance_memory','yongsan']))
 return out

if __name__=='__main__':
 import json
 from audio import E
 b=beats();(E/'narration_shot_plan.json').write_text(json.dumps(b,ensure_ascii=False,indent=2));print(len(b),'narration clauses')
