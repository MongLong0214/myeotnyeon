import csv,json,re,math
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parent
W=R.parents[2]
E=W/'episodes/v4/n18'
rows=list(csv.DictReader((R/'rewrite_lines.tsv').open(),delimiter='\t'))
facts=(E/'facts.md').read_text()
publishers={'S01':'문화일보','S02':'세계일보','S03':'한겨레','S04':'뉴시스','S05':'KBS','S06':'YTN','S07':'뉴시스','S08':'뉴시스','S09':'뉴스1','S10':'경향신문','S11':'경향신문','S12':'YTN','S13':'뉴스핌'}
fact_sources={}
for line in facts.splitlines():
 m=re.match(r'\| ([ECDJ]\d+) \|',line)
 if m:fact_sources[m[1]]=re.findall(r'S\d+',line)
def syll(t):return len(re.findall('[가-힣]',t))
def stamp(t):return f'{int(t)//60:02}:{t%60:05.2f}'
cues=[
 ('M0','차갑고 절제된 저음 펄스, 강도 2/5; 나레이션보다 22dB 아래. 두 번째 줄 사망 사실 뒤 0.6초 무음. 세 번째 줄 질문 끝에서 잔향도 끊기.'),
 ('M1','건조한 저음·희박한 타악, 강도 2/5; 나레이션보다 24dB 아래. 현장 소리 재현 없음. 날짜 카드에만 작은 종이 질감 전환음.'),
 ('M2','검찰·변호인 교대마다 저음 리듬 악기 한 층 교체, 강도 3/5; 나레이션보다 22dB 아래. 주장 내용 자체에 위협 효과음 없음.'),
 ('M3','불협화음이 적은 낮은 현·피아노, 강도 2/5; 나레이션보다 24dB 아래. 첫 선고 직전 베드 제거, 선고 숫자에 0.2초의 짧은 저음 히트.'),
 ('M4','좁은 음역의 반복 펄스, 강도 2→3/5; 나레이션보다 23dB 아래. 기준이 바뀌는 문서 전환에 마른 클릭 1회. 법률 정의에서는 타악 빼기.'),
 ('M5','선고 전 낮은 현을 한 층 추가, 강도 3/5; 나레이션보다 22dB 아래. 예상 질문 뒤 음악·환경음 완전 제거. 중대장 항소심 숫자에만 0.25초 저음 히트, 이후 강도 1/5.'),
 ('M6','짧고 미해결된 피아노·패드, 강도 1/5; 나레이션보다 25dB 아래. 마지막 질문 뒤 2초 여백, 출처 화면은 무음.')]
sections=list(dict.fromkeys(x['section'] for x in rows))
section_cues=dict(zip(sections,cues))
position=0;items=[];shot_durations=[];section_times={}
for i,r in enumerate(rows):
 n=syll(r['narration']);ids=r['facts'].split(',')
 for id in ids:assert id in fact_sources,id
 duration=n/6.4+.35
 if i<3:
  # Exactly 18s cold open, spoken material remains at 6.4 syllables/s.
  cold_speech=sum(syll(x['narration']) for x in rows[:3])/6.4
  duration=n/6.4+(18-cold_speech)/3
 # Deliberate prediction holds are separate from speech rate.
 hold=1.2 if r['narration'].startswith('그렇다면 중대장의 일심 선고는') else 1.6 if r['narration'].startswith('그 판단을 듣고') else 0
 hold+=1.65 if i==len(rows)-1 else 0
 duration+=hold
 start=position;end=start+duration;position=end
 parts=r['visuals'].split(';')
 count=max(math.ceil(duration/4),min(len(parts),math.floor(duration/2)))
 count=max(1,count)
 selected=parts[:count] if count<=len(parts) else parts+[parts[-1]+'의 출처·기록 세부 크롭']*(count-len(parts))
 shots=[]
 for j,p in enumerate(selected):
  a=start+duration*j/count;b=start+duration*(j+1)/count
  shots.append(f'{stamp(a)}–{stamp(b)} {p}')
  shot_durations.append(b-a)
 cue=section_cues[r['section']][0]
 sound=f'{cue} 유지'
 if i==0:sound='M0 시작; 훈련 동작·명령·발소리 효과음 없음'
 if i==1:sound='M0 낮춤; 사망 사실 뒤 0.6초 완전 무음, 히트 없음'
 if i==2:sound='M0 재진입; 질문 끝 베드·잔향 끊기'
 if r['narration'].startswith('그렇다면 중대장의 일심 선고는'):sound='M3 제거; 끝에 1.2초 예상 여백 포함'
 if r['narration'].startswith('징역 오 년이었습니다'):sound='선고 첫 음절에 0.2초 저음 히트; M3는 다음 절부터 작게 복귀'
 if r['narration'].startswith('그 판단을 듣고'):sound='M5·환경음 제거; 끝에 1.6초 예상 여백 포함'
 if r['narration'].startswith('항소심 선고는 징역'):sound='중대장 선고 첫 음절에 0.25초 저음 히트; M5 강도 1/5로 복귀'
 if r['narration'].startswith('여러분은 반성과'):sound='M6 낮춤; 재판부 판단을 비웃는 음색 금지'
 item={**r,'id':f'V{i+1:03}','start_s':start,'end_s':end,'syllables':n,'shot_count':count,'shots':shots,'sound':sound};items.append(item)
 section_times.setdefault(r['section'],[start,end])[1]=end
total_syll=sum(x['syllables'] for x in items)
pauses=position-total_syll/6.4
source_tail=8
out=['# N18 대본 v2','',
 '**가제: 잘못은 인정했다. 학대치사는 부인했다. 법원은 왜 유죄로 봤나**','',
 f'16:9 · 나레이션 {total_syll:,}음절 · 발화 목표 6.2–6.6음절/초(기준 6.4) · 편집 예상 {stamp(position+source_tail)}. 발화 {total_syll/6.4:.2f}초 + 쉼·예상 여백 {pauses:.2f}초 + 출처 8초. 속도 범위 전체 예상 {stamp(total_syll/6.6+pauses+source_tail)}–{stamp(total_syll/6.2+pauses+source_tail)}. 음성 합성·렌더 전의 편집 설계이며 실측 러닝타임이 아니다.','',
 '각 V행은 짧은 발화 1–3문장이다. 숫자는 발화용 한글, 카드에는 아라비아 숫자를 쓴다. 모든 사실은 facts.md 채택 행만 사용한다. 질문·평가 요청·용어 풀이는 해당 근거를 함께 적되 새 사실이나 당사자의 속마음을 만들지 않는다. 사건 결과의 충격을 감추는 대신 법원의 판단과 선고 수치에 대한 질문을 연다.','',
 '**재구성 고지:** 시작부터 공간 이미지마다 “재구성 · 실제 사건 현장·인물·배치 아님” 표시. 지도는 인제군 단위 위치 설명이며 부대 좌표·이동 경로를 만들지 않는다. 기록 카드는 “보도 요약 · 원본 공소장·판결문 아님” 표시. 연출 지시의 따옴표는 화면 글자의 범위 표시이며, 기사 제목 외의 요약 문구에 인용 부호를 렌더하지 않는다. 실사풍 공간은 모두 무인 이미지다. 새벽빛 법원·군 병원 외관도 일반적인 상징 이미지로 표시하며 사건 당시 시각·날씨·이송 병원을 뜻하지 않는다. 훈련 동작·신체·실신·죽음·고통·의료행위는 보여주거나 소리로 재현하지 않는다.','',
 '행마다 아래에 적은 컷 시각에 전환한다. 나레이션 중간에도 화면을 바꾸며, 한 문장을 한 화면으로 고정하지 않는다. 사건 현장을 상상한 인물 장면 대신 공간→문서→수치→지도→질문 카드를 교대한다.','',
 '## 음악·사운드 연출','',
 '다음 수치는 새 제작용 믹스 목표다. 레퍼런스 실측값으로 오인하지 않는다. 강도는 편집 방향(1 낮음–5 높음)이다. 음성 명료도를 우선해 베드를 덕킹한다. 휘슬·비명·심박·군 명령·사망 순간 효과음은 쓰지 않는다. 히트는 법정 숫자 공개에만 사용한다.','']
for section,(cue,desc) in section_cues.items():out.append(f'- **{cue} · {section}**: {desc}')
out+=['','## 발화·화면·큐','']
prev=None
for x in items:
 if x['section']!=prev:
  a,b=section_times[x['section']];out += ['',f"### {x['section']} · {stamp(a)}–{stamp(b)}",'', '| 행 · 편집 시간 | 나레이션 | 사실 ID | 화면 컷 | 음악·소리 |','|---|---|---|---|---|'];prev=x['section']
 out.append(f"| {x['id']} · {stamp(x['start_s'])}–{stamp(x['end_s'])} | {x['narration']} | {x['facts']} | {'<br>'.join(x['shots'])} | {x['sound']} |")
out+=['',f"{stamp(position)}–{stamp(position+source_tail)}: 무성 출처 화면 두 장, 4초씩. facts.md의 원문 URL·발행일과 ‘보도에 인용된 판결 이유를 정리함’을 표시한다. 재구성 고지는 유지한다.",'','## 열린 질문과 회수','',
 '| 질문 | 제기 | 회수 |','|---|---|---|']
find=lambda prefix:next(x for x in items if x['narration'].startswith(prefix))
for question,a,b in [('왜 유죄로 보았나','중대장 측은 잘못된 행동을 인정하면서도','부중대장의 혐의도'),('1심에서 학대치사를 인정했나','법원은 학대치사를 인정했을까요','중대장의 학대치사와'),('중대장의 1심 선고는 몇 년인가','지금 여러분이라면','징역 오 년이었습니다'),('항소심이 무엇을 달리 보았나','무엇을 다르게 봤길래','항소심은 실체적'),('중대장의 항소심 형은 얼마나 늘었나','그렇게 중대장의 형은 올라갔습니다','항소심 선고는 징역'),('중대장 형은 확정됐나','그렇다면 이 결과는','원심 판단에 잘못이')]:
 out.append(f"| {question} | {find(a)['id']} | {find(b)['id']} |")
out+=['','장 끝 연결: 01은 인정·부인의 충돌, 02는 유죄 여부와 실제 선고, 03은 형 증가 이유, 04는 증가 폭, 05는 확정 여부를 남긴다. 06의 마지막 질문은 시청자 의견이므로 정답을 만들어 회수하지 않는다.','', '## 사용 사실과 넣지 못한 디테일','',
 '사용 행: '+', '.join(sorted({id for x in items for id in x['facts'].split(',')}))+'.','',
 '입대 후 며칠인지와 입대일은 사실표 채택 행이 없어 제외했다. 날짜 카운터는 E05의 “당일 → 이틀 후”만 쓴다. 그날의 분 단위 진행·시각·기상·훈련 시간·군장 무게·현장 대사·동선도 제외했다. 가족의 직접 발언과 피고인들의 개별 최후진술은 보존 기사에 있더라도 사실표 채택 행이 없어 인용하지 않는다. 피해자의 개인사를 상상해 채우지 않는다. 초기 수사기관 간 이동·정확한 기소일·부중대장의 확정일과 경위·2심 구형도 채택 행이 없어 쓰지 않는다.','',
 '화면의 기사 제목 인용은 S07(뉴시스·2024.11.12), S11(경향신문·2025.01.07)의 원문 제목과 S10(경향신문·2025.06.18)의 “2심서 형량 가중”이라는 짧은 원문 조각이다. S10은 ‘제목 일부’로 표시한다. 사실 내용은 각각 C03, C05, C07·J07의 독립 매체 교차 근거로 확인한다. 그 밖의 문서는 보도 요약이며 직접 인용 부호를 붙이지 않는다.']
(E/'script_v2.md').write_text('\n'.join(out)+'\n')
(R/'rewrite_timing.json').write_text(json.dumps({'syllables':total_syll,'speech_s_at_6_4':total_syll/6.4,'pause_s':pauses,'planned_duration_s':position+source_tail,'shot_count':sum(x['shot_count'] for x in items)+2,'shot_duration_min_s':min(shot_durations),'shot_duration_max_s':max(shot_durations),'items':items},ensure_ascii=False,indent=2))

review=['# N18 대본 v2 · 정확성 자체 점검','',
 '기준은 facts.md의 채택 행과 그 안의 서로 다른 원발행사다. 이번 작업은 네트워크로 기사 원문을 새로 조회하지 않았다. 로컬 사실표와 보존 본문으로 확인했으며 최신 사건 상태를 새로 검증했다는 뜻이 아니다. 판결문을 직접 읽었다고 표현하지 않는다.','',
 '## 행별 사실·발행사','',
 '아래 출처는 각 사실 ID별 독립 발행사를 표시한다. 네이버를 발행사로 세지 않으며 같은 뉴시스의 날짜가 다른 기사를 두 독립 발행사로 세지 않는다. 질문·호명·연출은 사실이 추가되지 않았는지도 함께 검토했다.','',
 '| 행 | 사실 ID → 원발행사(보존 출처) | 점검 |','|---|---|---|']
for x in items:
 refs=[]
 for id in x['facts'].split(','):
  ss=fact_sources[id]; independent={publishers[s] for s in ss};assert len(independent)>=2,(id,ss)
  refs.append(id+' → '+', '.join(f'{publishers[s]}({s})' for s in ss))
 note='질문·설명 포함, 새 사실 추가 없음' if '?' in x['narration'] or '여러분' in x['narration'] else '보도 요지·주장/판단 주체 구별'
 review.append(f"| {x['id']} | {'<br>'.join(refs)} | {note} |")
review += ['','## 표현·화면 경계','',
 '| 항목 | 결과와 적용 |','|---|---|',
 '| 피고인 신원 | 역할명 중대장·부중대장만 사용. 이름·이니셜·성별·나이·계급 없음. 기사 이미지 원본을 그대로 넣지 않고 허용된 제목 일부를 활자로 재작성. |',
 '| 허구 장면·대사 | 현장 인물·대사·동선·시각·날씨 없음. 새벽빛 법원·군 병원은 일반 상징 공간임을 상시 명시. 실신·사망은 발화·기록만, 이미지·음향 재연 없음. |',
 '| 피해자 존중 | 인물·몸·고통·죽음의 이미지와 소리 없음. 조롱·개그 큐 없음. 피해자 수는 기록 탭으로만 표현. |',
 '| 직접 인용 | 인물 발언 인용 없음. S07·S11 원문 제목과 S10 제목 일부 “2심서 형량 가중”을 보존 제목과 대조. 각 발행사·발행일·S10 제목 일부 표기. C03·C05·C07·J07 교차 근거와 연결. |',
 '| 과도한 형량 평가 | 금지된 표현을 나레이터·화면에 쓰지 않음. 예상 질문은 의견을 요청하며 특정 답을 유도하거나 법원의 실제 이유를 대체하지 않음. |',
 '| 구형과 선고 | 중대장 1심 10년 구형 ↔ 5년 선고, 부중대장 1심 7년 구형 ↔ 3년 선고만 비교. 2심 수치는 1심 선고와의 변화로만 비교하고 1심 구형과 연결하지 않음. |',
 '| 확정 | 중대장은 2025.09.25 대법원 상고 기각·5년 6개월 확정. 부중대장은 그날 보도 기준 3년 확정 상태. 확정일·본안 판결일을 같은 날로 만들지 않음. |',
 '| 재구성 | 공간마다 재구성·실제 현장/인물/배치 아님. 기록은 보도 요약이며 원본 판결문·공소장처럼 보이게 만들지 않음. |',
 '| 사운드 | 음악·저음 히트는 편집 연출. 실제 훈련·응급·사망 소리로 제시하지 않음. 선고 숫자 외 피해 관련 사실에 충격 히트 없음. |','',
 '## 용어','',
 '| 용어 | 사용·점검 |','|---|---|',
 '| 학대치사·직권남용 가혹행위 | 검찰의 기소와 중대장 측 부인, 법원의 유죄를 구별. “부인했으므로 무죄”나 제작자의 단정으로 바꾸지 않음. |',
 '| 상상적 경합 | 하나의 행위가 여러 죄에 해당: J01·J09. 1심 판단으로 표시. |',
 '| 실체적 경합 | 여러 행위로 여러 죄를 범함: J07·J09. 2심에서 피해자별 행위 양상을 달리 본 설명은 J08. |',
 '| 법정형 / 선고형 | J10의 가능한 처벌 범위와 C05·C07의 실제 선고를 분리. 1심 선고에 배수를 곱하지 않음. 가중 가능성을 자동 증형으로 말하지 않음. |',
 '| 양형기준 | J02의 참고 기준. 법정형 상한이라고 하지 않음. |',
 '| 피해자 6명 | E02의 대상 인원. 확정된 범죄 6개라는 산술로 옮기지 않음. 도식에는 실제 범죄 개수 아님 표시. |',
 '| 중대장 증형·부중대장 유지 | J07·J08의 판단 차이는 중대장 증형 설명에 연결. 부중대장 개별 유지 이유를 새로 추론하지 않음. |','',
 '## 제작 길이·컷 점검','',
 f'발화 {total_syll:,}음절. 6.4음절/초에서 발화 {total_syll/6.4:.2f}초, 쉼 {pauses:.2f}초, 출처 8초로 편집 예상 {stamp(position+8)}. 속도 범위는 대본에 병기했다. 콜드 오픈 V001–V003은 18.00초. 본문 {sum(x["shot_count"] for x in items)}컷의 계획 길이 {min(shot_durations):.2f}–{max(shot_durations):.2f}초이며 출처 2컷은 각 4초다. 음성·새 영상은 이번 작업에서 만들지 않았으므로 실제 발음·믹스·완성 컷의 검증으로 표시하지 않는다.','',
 '자체 점검 결과는 작성자의 검토다. 사실표의 두 발행사 조건을 충족한 행을 옮긴 것이며 외부 법률 검토나 판결문 대조를 했다고 주장하지 않는다.']
(E/'script_v2_review.md').write_text('\n'.join(review)+'\n')
print(json.dumps({'syllables':total_syll,'duration_s':position+8,'cold_open_s':items[2]['end_s'],'cut_min':min(shot_durations),'cut_max':max(shot_durations),'lines':len(items)},ensure_ascii=False))
