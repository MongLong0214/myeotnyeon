from pathlib import Path
import json,re
W=Path(__file__).resolve().parents[5]; O=W/'episodes/v4/n18/cartoon_v5'
# Text and facts below are authored from facts.md / facts_enrich.md only.
# stage denotes an explicitly illustrative performance, not witnessed blocking.
RAW='''
J06|host|훈련이 사람을 죽였습니다.
J04,C06|court|그런데 판결에는 교육 목적이 등장합니다.
F04,F05,J12|host|군기는 챙기면서, 안전은 왜 놓쳤을까요?
E01,C09|ground|육군 12사단 훈련병 사망 사건. 확정된 중대장 형은 5년 6개월입니다.
F04,F05|host|하지만 숫자만 보고 끝내면, 그날 빠진 안전장치도 함께 사라집니다.
E01,E02|ground|2024년 5월 23일, 강원 인제의 신병교육대. 군기훈련 대상은 6명이었습니다.
F02|barracks|경찰 수사결과, 계기는 전날 취침점호 뒤 떠들었다는 적발이었습니다.
F02,F04|investigation|여섯 명 모두 실제로 떠들었다고 단정하는 건 아닙니다. 소명할 절차가 있었으니까요.
F03|command|부중대장이 다음 날 오전 구두 보고를 하고, 중대장의 승인을 받았습니다.
F04,F05|host|승인은 받았는데, 확인은 빠졌습니다. 대체 무엇을 건너뛴 걸까요?

F04|investigation|경찰은 확인서 작성과 소명 기회가 지켜지지 않았다고 밝혔습니다.
F04|host|왜 훈련받는지 확인하고, 본인 말도 듣는 절차. 시작부터 빠진 겁니다.
F05|investigation|훈련병 신체 상태도, 훈련장 온도지수도 제대로 확인하지 않았다는 수사결과입니다.
F04,F05|command|사람 몸을 움직일 권한은 있는데, 그 몸을 확인하는 절차는 놓쳤습니다.
F06|ground|여기서 군장 이야기가 나옵니다. 훈련병들은 보급품도 모두 받지 못했습니다.
F06|barracks|경찰에 따르면, 군장의 빈 공간을 책으로 채우게 했습니다.
F07|witness|동료들은 나중에 법정에서 책 약 40권을 넣었다는 취지로 증언했습니다.
F07|host|책은 읽으라고 있는 건데, 여기서는 군장을 채우는 물건이 됐습니다.
F06,F07|investigation|정확한 무게를 하나로 찍지는 않겠습니다. 확인된 건 책으로 채웠다는 사실입니다.
F08,F09|command|그런 군장을 메고 시작된 훈련. 걷기에서 끝났을까요?

F10|ground|경찰이 특정한 시작 시각은 오후 4시 26분쯤입니다.
F08|ground|먼저 완전군장 상태로, 총기를 휴대한 채 연병장 두 바퀴를 걸었습니다.
F09|command|이어서 중대장이 완전군장 상태의 선착순 한 바퀴를 지시했습니다.
F09|ground|팔굽혀펴기, 다시 뜀걸음 세 바퀴. 경찰이 발표한 지시 순서입니다.
F11,F12|hospital|그리고 오후 5시 11분쯤. 시작 약 45분 뒤, 한 훈련병이 의식을 잃었습니다.
F13|investigation|경찰은 간부들이 열사병의 위급 상황을 제대로 인지하지 못했다고 봤습니다.
F13|hospital|신속한 응급처치도 지체했다는 판단입니다. 훈련 방법만의 문제가 아니었습니다.
F16|transport|훈련병은 의무대를 거쳐 속초의료원, 강릉아산병원으로 옮겨졌습니다.
F18,F19|hospital|강릉 도착은 밤 9시 40분쯤. 두 병원 사이의 전체 경과는 약 세 시간이었습니다.
F19,F23|host|차를 세 시간 탔다는 뜻은 아닙니다. 그 사이 가족에게는 어떤 연락이 갔을까요?

F23|letter|어머니는 공개편지에 첫 전화를 받은 시각을 오후 5시 54분으로 적었습니다.
F25|letter|그 편지에는 입영 날, 먼 길 돌아갈 부모를 아들이 걱정한 기억도 담겼습니다.
F25|memorial|차로 여섯 시간에서 일곱 시간. 부모 손을 잡고 등을 다독였다는 회고입니다.
F01|barracks|어머니가 편지에 적은 신병 생활은 아홉 날. 입대 날짜를 역산한 숫자는 아닙니다.
F15|memorial|훈련병은 이틀 뒤인 2024년 5월 25일 숨졌습니다.
F30|memorial|6월 19일, 동기들의 수료식장 추모 공간에는 명예수료증이 놓였습니다.
F31|memorial|참석자들은 국화꽃을 놓고 고인을 추모했습니다. 돌아온 건 사람이 아니었습니다.
F32|witness|그 뒤 8월 27일 공판. 함께 군기훈련을 받은 동료 네 명이 증인으로 섰습니다.
F35|witness|한 생존 훈련병은 외상 후 스트레스 장애 진단을 받았다고 법정에서 밝혔습니다.
C10,C01,D01|host|검찰은 단순 과실로 보지 않았습니다. 적용한 죄명은 학대치사였습니다.

E06|prosecution|훈련 방식과 진행 경과, 피해자의 신체조건까지 종합해 학대라고 판단했습니다.
C01,D01|court|중대장과 부중대장 모두 학대치사와 직권남용 가혹행위 혐의로 기소됐습니다.
C04|defendant|중대장 측은 잘못된 행동을 인정하면서도, 1심에서 학대치사 혐의는 부인했습니다.
C04,C06|host|행동은 인정하지만 그 죄는 아니라는 주장. 법원의 답은 달랐습니다.
C06,D05,J06|court|1심은 두 사람 모두 유죄. 군기훈련과 사망 사이의 인과관계도 인정했습니다.
J03|court|신체조건에 맞지 않는 군기훈련, 군의 사기와 전투력, 국민 신뢰를 해친 점을 짚었습니다.
J05|court|피해자 측에게 용서받지 못했다는 사정도 지적했습니다.
J04|host|그런데 이 판결에는, 피고인에게 유리하게 참작한 사정도 있습니다.
J04|defendant|사실관계를 인정한 점. 잘못을 반성하는 태도. 그리고 교육 목적입니다.
J04,C06|host|학대치사는 유죄인데, 교육 목적은 참작. 이 문장이 형량에서 어떻게 만났을까요?

J04|court|1심은 군 기강을 세우려는 교육 목적으로 훈련하다 범행에 이른 점을 참작했습니다.
J04,C06|host|교육 목적이라고 적었다고, 학대가 교육으로 바뀐 건 아닙니다. 유죄 판단은 유지됐습니다.
E07|prosecution|검찰은 군의 지도력과 관리 체제에 대한 국민 신뢰가 훼손됐다고 구형 이유를 밝혔습니다.
C03|prosecution|2024년 11월 12일. 중대장에게 요청한 형은 징역 10년이었습니다.
D03|prosecution|부중대장에게는 징역 7년. 둘 다 검찰의 구형입니다. 법원이 내린 선고와 구분합니다.
C05|court|2025년 1월 7일. 중대장에게 실제로 선고된 1심 형은 징역 5년입니다.
D04|court|부중대장은 징역 3년. 각자의 구형과 각자의 선고가 이렇게 갈렸습니다.
J03,J04|host|유죄와 형량은 다른 질문입니다. 무거운 사정과 유리한 사정을 함께 본 결과입니다.
F37|memorial|선고 뒤 어머니는 피고인들이 500년형을 받은들 적다고 하겠느냐고 말했습니다.
C07,J07|host|하지만 중대장 5년은 마지막 숫자가 아니었습니다. 항소심에서 무엇이 바뀌었을까요?

J01|court|1심은 하나의 행위가 여러 범죄를 구성하는 관계, 상상적 경합으로 봤습니다.
J07,J08|investigation|항소심은 다르게 봤습니다. 같은 장소에서 이어졌다는 것만으로 묶지 않았습니다.
J08|witness|피해자마다 구체적인 가혹행위와 학대의 양상이 달랐다는 겁니다.
J08|host|한 훈련장이라는 큰 묶음에서, 각 사람이 당한 행위로 시선이 옮겨갑니다.
J07,J09|court|여러 행위로 여러 죄를 범한 관계인 실체적 경합. 죄의 수에 관한 판단이 바뀌었습니다.
J08,E02|host|훈련병 6명이니까 범죄도 딱 6개라는 계산은 아닙니다. 행위를 구별한 판단입니다.
J11|court|항소심은 지휘관들이 후진적 병영문화를 답습했다고 지적했습니다.
J11|ground|충분히 예방할 수 있었던 사망사고를 초래했다는 판단입니다.
J12|court|국가가 병사의 생명과 신체를 보호하리라는 사회의 기본 기대를 배반했다고 봤습니다.
C07,J07|host|군기를 세운다는 명분, 사람을 지킬 책임. 바뀐 판단은 형량을 어디까지 움직였을까요?

C07|court|2025년 6월 18일, 항소심은 중대장에게 징역 5년 6개월을 선고했습니다.
C05,C07|host|1심 5년에서 6개월 증가했습니다. 이전 형에 배수를 곱한 산수는 아닙니다.
D06|court|부중대장은 1심과 같은 징역 3년입니다. 두 사람의 결과를 섞으면 안 됩니다.
C07,D06|host|중대장 형이 늘어난 이유를 부중대장 형이 유지된 이유로 그대로 옮길 수도 없습니다.
J13|court|대법원은 중대장에 대한 원심 판단에 잘못이 없다고 보고 상고를 기각했습니다.
C09|court|2025년 9월 25일. 중대장의 징역 5년 6개월이 확정됐습니다.
D08|court|부중대장의 징역 3년도 확정 상태입니다. 같은 날 보도로 확인되는 상태입니다.
D08|host|부중대장까지 그날 대법원이 본안을 판단했다고 말하지는 않겠습니다.
F38,F39|reform|재판과 별개로, 사건 뒤 국방부는 훈련병 군기훈련 대책을 발표했습니다.
F04,F39|host|그 대책에 다시 등장한 단어가 있습니다. 처음에 빠졌던 바로 그 절차입니다.

F38|reform|2024년 6월 27일 발표. 훈련병 군기훈련에서 체력단련 종목을 제외하기로 했습니다.
F38|ground|일반 신병 교육의 체력훈련을 전부 없앴다는 뜻은 아닙니다.
F39|reform|개인에게 반드시 소명 기회를 주도록 시행 절차도 표준화했습니다.
F40|command|육군 신병교육부대의 군기훈련 승인권자는 영관급 지휘관으로 높이기로 했습니다.
F41|hospital|건강 상태를 수시로 확인하고, 응급상황 대비책부터 마련하는 절차도 담겼습니다.
F04,F05,F39,F41|host|소명 듣기. 몸 상태 확인하기. 위급할 때 대비하기. 그렇게 대단한 주문입니까?
F04,F39|investigation|사건 전에 지키지 않은 절차가, 사건 뒤 대책에서 다시 강조됐습니다.
J11,J12|memorial|항소심이 남긴 말은 무겁습니다. 예방할 수 있었고, 보호받을 기대는 배반됐습니다.
J04,J12|host|교육 목적을 참작한 판결. 생명을 지킬 국가의 책임. 여러분은 어느 대목을 더 무겁게 봅니까?
J11,J12|memorial|군기를 세운다던 훈련에서, 반드시 먼저 지켰어야 할 것은 사람이었습니다.
'''

LEX=[('2024년 11월 12일','이천이십사 년 십일 월 십이 일'),('2024년 5월 23일','이천이십사 년 오 월 이십삼 일'),('2024년 5월 25일','이천이십사 년 오 월 이십오 일'),('2024년 6월 27일','이천이십사 년 유월 이십칠 일'),('2025년 1월 7일','이천이십오 년 일 월 칠 일'),('2025년 6월 18일','이천이십오 년 유월 십팔 일'),('2025년 9월 25일','이천이십오 년 구 월 이십오 일'),('오후 4시 26분','오후 네 시 이십육 분'),('오후 5시 11분','오후 다섯 시 십일 분'),('오후 5시 54분','오후 다섯 시 오십사 분'),('밤 9시 40분','밤 아홉 시 사십 분'),('5년 6개월','오 년 육 개월'),('500년형','오백 년형'),('12사단','십이 사단'),('11월 12일','십일 월 십이 일'),('6월 19일','유월 십구 일'),('8월 27일','팔 월 이십칠 일'),('40권','마흔 권'),('45분','사십오 분'),('10년','십 년'),('7년','칠 년'),('5년','오 년'),('3년','삼 년'),('6개월','육 개월'),('6명','여섯 명'),('6개','여섯 개'),('1심','일심')]
rows=[]
for i,line in enumerate(l for l in RAW.splitlines() if l.strip()):
    facts,stage,caption=line.split('|'); spoken=caption
    for a,b in LEX:spoken=spoken.replace(a,b)
    assert not re.search(r'[0-9A-Za-z]',spoken),spoken
    rows.append({'id':f'N{i+1:03d}','text':caption,'tts_text':spoken,'facts':facts.split(','),'stage':stage,'chapter':i//10+1,'cliffhanger':i%10==9 and i<80})
script={'title':'군기는 챙기면서, 사람은 왜 놓쳤나','version':'N18 cartoon v5 script v2','voice':'M1','voice_basis':'current Shorts q017/audio/na/index.json','source_documents':['../facts.md','../facts_enrich.md'],'lexicon':LEX,'lines':rows,'red_lines':['original fictional designs only','no identifiable victim or bereaved likeness','no collapse, patient, death or gore shown','no invented event dialogue or blocking presented as documentary fact','commander and deputy faceless; source role is 부중대장, not 소대장','all screen dates numeric'],'visual_note':'Character movement is labelled illustrative. Only narrator has lip sync; no event dialogue is synthesized.'}
O.mkdir(exist_ok=True)
(O/'script.json').write_text(json.dumps(script,ensure_ascii=False,indent=2))
intro='# N18 cartoon v5 · script v2\n\n사실 근거: `../facts.md`, `../facts_enrich.md`만 사용. 목소리: 현재 Shorts의 Supertonic 3 M1. 화면 날짜는 숫자. 현장 대사는 만들지 않는다. 인물 동작과 공간은 상징적 연출이며, 실신·환자·사망 순간은 보여주지 않는다. 사실표의 두 번째 지휘관은 **부중대장**이다.\n\n처음 3초: “훈련이 사람을 죽였습니다.” / 10초 안 질문: “군기는 챙기면서, 안전은 왜 놓쳤을까요?”\n\n'
body=[]
for c in range(1,10):
    body.append(f'## {c}\n\n| ID | 내레이션 / 숫자 자막 | 근거 | 연기 무대 |\n|---|---|---|---|')
    for r in rows[(c-1)*10:c*10]:body.append(f"| {r['id']} | {r['text']} | {', '.join(r['facts'])} | {r['stage']}{' · 다음 쟁점 열기' if r['cliffhanger'] else ''} |")
    body.append('')
(O/'script_v2.md').write_text(intro+'\n'.join(body))
syllables=sum(len(re.findall('[가-힣]',r['tts_text'])) for r in rows)
print(json.dumps({'lines':len(rows),'syllables':syllables,'runtime_at_7_8':syllables/7.8,'chapters_syllables':[sum(len(re.findall('[가-힣]',r['tts_text'])) for r in rows if r['chapter']==c) for c in range(1,10)]}))
