"""Build refs.json: metadata from meta/*.json + subtitle stats + hand observations (timestamps in seconds)."""
import json, glob, datetime, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from subs import stats
R = pathlib.Path(__file__).resolve().parents[1]
KST = datetime.timezone(datetime.timedelta(hours=9))
AUDIO = '미확인 — 오디오를 받거나 녹음하지 않음. 스토리보드·자막은 목소리·음악·효과음 근거가 아님.'

O = {}  # id -> dict(group, level, role, segments=[(t, obs)], notes)
def add(i, group, level, role, segs, notes=''):
    O[i] = dict(group=group, evidence_level=level, role=role, segments=[dict(t=t, observation=o) for t, o in segs], notes=notes)

add('w_LJ_GQObic', 'owner-reference', 'E3', '오너 지정 레퍼런스 #1 (16:9 장편)', [
 (0.0, '푸른 단색의 야간 조감 3D(교도소 단지). 자막 없음(수동 자막 첫 큐 3.03초).'),
 (5.0, '흰·청색 점토풍 3D 건물 위 상단 중앙 시점 카드 "1997년 1월 20일 새벽 3시." — 굵은 고딕, 흰색, 마침표로 끝남. 하단 중앙 흰 자막 1줄.'),
 (9.9, '감방: 전경에 파란 창살, 뒤에서 자홍 역광. 인물은 반전(네거티브/열화상) 처리.'),
 (14.9, '실존 인물 수형 사진(아카이브)과 붉은 림라이트 3D 인물을 나란히 배치 — 우리 규칙상 사용 불가(실존 인물 사진).'),
 (19.8, '뒷모습 인물이 환풍구로 손을 뻗음. 포화 파랑 벽(샘플 #0F2B73) + 빨강·자홍 림(샘플 #CF3567, 하이라이트 #EC7E8A).'),
 (24.8, '환풍구 클로즈업, 쇠창살 뒤 붉은 빛.'),
 (29.7, '공간 속 치수 주석: 노란 점선 호와 "32cm", "28cm" 라벨을 환풍구 위에 겹침. 자막도 같은 숫자를 말함.'),
 (34.7, '와이어프레임 메시 인체(자홍, 샘플 #B10D75).'),
 (39.6, '위에서 내려다본 평면도(청사진 블루 #062A64/#2559BD)에 인물 위치를 붉은 점 하나로 표시.'),
 (44.6, '로우 와이드: 벽 아래 작은 실루엣, 수직 점선과 "4.5m" 라벨. 바탕 블루 샘플 #09419F.'),
 (49.5, '땅 파는 인물, 파랑 공간에 빨강 림.'),
 (69.4, '근접 웅크린 인물, 거의 검정(#15020D) 위 빨강 림(#C5525D).'),
 (74.3, '철조망 매크로(파랑). 자막에 치수 "폭 1.8m, 높이 2.1m".'),
 (84.2, '우상단 시점 카드 "새벽 4시 30분."'),
 (89.2, '삼색 인물(파랑·연두·빨강) 예고 몽타주 시작.'),
 (94.1, '장 카드 "01. 무기수": 연두 점묘(도트) 글자(블러된 샘플 #889243), 회색 노이즈 위 흐린 얼굴.'),
 (99.1, '인물 도시에: 검정 바탕 + 어두운 격자(#181717), 붉은 링 원형 사진(링 #760811), 세리프 이름, 연도별 이력 줄.'),
 (104.0, '같은 도시에에 이력 줄이 추가됨(상태 누적).'),
 (109.0, '상단 중앙 시점 카드 "1989년 3월, 서울 돈…", 주황·청록 조명 장면.'),
 (128.8, '도식: 원형 인물 아이콘 + 교도소 아이콘 3개와 지명 라벨(이감 경로).'),
 (133.8, '네거티브 렌더(흰 인물·검은 윤곽) 누운 수형자들.'),
 (163.5, '대칭 1점 투시 창고, 천장 조명줄, 중앙 인물.'),
 (218.0, '장 카드 "03. 도주 생활".'),
 (222.9, '실제 방송 뉴스 화면을 어두운 질감 테두리 액자로 삽입 — 사용 불가.'),
 (247.6, '시점 카드 "1997년 12월 30일 오전 9시." 붉은 건물 정면 대칭.'),
 (257.6, '히어로 숫자 "302": 빛나는 입체 문자, 얕은 피사계 심도.'),
 (262.5, '청록 X레이 발광 인물(샘플 #85B8BD) 대 붉은 인물의 대치.'),
 (376.5, '전체가 빨강인 도시 모형(#6D0A0D/#BA2927).'),
 (386.4, '시점 카드 "1999년 7월 16일 오후 3시."'),
 (396.3, '장 카드 "04. 체포 작전"(창살 + 점묘 글자).'),
 (411.2, '빨강·초록 2색 근접 인물(#650F01/#72A51F).'),
 (416.1, '실제 신고 녹취 장면(경찰 상황실 영상 + 대화 자막) — 사용 불가.'),
 (455.7, '위에서 본 청록 경찰 차량 행렬.'),
 (500.3, '도시에에 최종 형량 줄 추가.'),
 (520.1, '네거티브 누운 인물 → 빨강 인물로 마무리.'),
], notes='16:9, 3840x2160, 535초, 업로드 2026-08-26. 설명란: "이 영상은 AI를 사용하지 않고, 손수 제작했습니다." (제작자 진술). 섬네일(16:9)은 영상 색보정과 달리 밝은 흰 점토 렌더 + 이름 칩("신창원" 빨강 칩, "경찰특공대" 검정 칩). 수동 자막: 첫 큐 3.03초, 큐 길이 중앙값 2.53초(10~90% 1.57~3.60초), 큐당 글자 중앙값 16자·최대 26자, 1줄, 현재형 서술. 기존 문서(references/REFERENCE_ANALYSIS.md, 로컬 사본 기반, 이번에 재검증 안 함): 컷 156개, 숏 길이 중앙값 2.77초, 숏 움직임 밀기65/정지29/빼기27/팬·트랙36. 같은 문서의 음량·음성 수치는 이번 증거 규칙상 쓰지 않음.')

add('WFZJTsqHn8k', 'extol-shorts', 'E3', '같은 사건의 엑스톨 Shorts 판(9:16 적응)', [
 (0.0, '검정 9:16. 상단 고정 제목 2줄(흰 "907일 동안 경찰을 농락한" / 빨강 #E10307 "신창원의 미친 탈옥 과정"), 1행 y≈315~384px.'),
 (2.0, '장편의 3D 숏을 가운데 창(y 581~1338px, 약 1.42:1)으로 잘라 넣음. 창 안 시점 카드.'),
 (5.9, '자막은 창 아래쪽에 겹쳐 2줄, 굵은 디스플레이 고딕, 흰색 + 부드러운 검은 글로(y≈1100~1420).'),
 (41.6, '평면도 + 붉은 점(장편 0:39.6과 같은 숏).'),
 (43.5, '"4.5m" 치수 숏 재사용.'),
 (89.1, '예고 몽타주 숏, 마지막 91초 "전대미문의 도주극이 시작되었습니다" — 장편으로 넘기는 클리프행어.'),
], notes='95초. 창 아래 y>1420px(약 26%)는 비어 있음.')

add('DIsfbI0mZxA', 'extol-shorts', 'E3', '엑스톨의 네이티브 9:16 판결 비교 Shorts(형량 주제)', [
 (0.0, '전면 9:16. 얼굴 없는 발광 인물 2명, 머리 위 큰 글자 "B"(청록)·"A"(주황)로 당사자 표시.'),
 (4.0, '회색 단색 3D 방(호텔 객실), 인물만 발광.'),
 (9.9, '질문 자막 "B의 죽음에 A의 책임은 어느 정도일까요?" — 퀴즈형 질문.'),
 (13.8, '판결 문서 카드: 회색 질감 바탕, 흐린 저울 선화, 상단 "대법원 1982.3.23. 선고 …" + 본문 단락.'),
 (31.6, '주황 A·청록 B가 한 공간에서 대치, 회색 세트.'),
 (51.4, '자막 "28미터 아래 지상으로 떨어져 사망했습니다." — 숫자는 자막으로만.'),
 (55.3, '"대법원 판결은 이렇습니다." 뒤 판결문 카드 16초 유지(55.3~71.1).'),
 (79.0, '마지막 자막 "…인정할 것인가의 문제였습니다."'),
], notes='83초. 조회수 6,102(채널 Shorts 중 하위권). 당사자를 색(주황/청록)으로 구분 — 우리는 사람에 색을 주지 않음.')

add('7vrL0PMGKzM', 'extol-shorts', 'E3', '엑스톨 Shorts 중 최다 조회', [
 (0.0, '흑백 반전(적외선풍) 3D 조감, 흰 나무·검은 하늘.'),
 (5.9, '붉은 림 인물(시신) 하나만 색, 나머지 무채색.'),
 (15.7, '파란 인물 하나, 노란 강조물.'),
 (21.6, '치수 주석 "1.5m"(점선) + 자막 "1.5m 정도 되는 얕은 곳이었다."'),
 (23.6, '자막 "이 형사의 키는 175cm가 넘었다." — 수치로 의문 제기.'),
 (51.1, '마지막 질문 자막 "…다시 현장을 찾은 것일까?" — 클리프행어.'),
], notes='55초, 조회수 73,299. 레이아웃은 WFZJ와 같음(제목 띠 + 창 + 자막).')

add('50GA6_DeJbE', 'extol-shorts', 'E2', '엑스톨 Shorts, 빨강·흰 네거티브 그레이드', [
 (0.0, '빨강/흰 반전 듀오톤.'), (14.5, '노란 X레이 발광 인물 하나로 시선 유도.'), (34.8, '같은 그레이드 유지, 창 레이아웃.')], notes='59초, 조회수 50,828.')
add('ysL2O9W78yQ', 'extol-shorts', 'E2', '엑스톨 Shorts, 무채색 + 단일 빨강', [
 (0.0, '시점 카드 "2003년 9월." 흑백 공간.'), (14.7, '빨강 인물만 색.'), (37.8, '초록 인물 하나(다른 장면 표시).')], notes='43초, 조회수 39,230.')
add('vYDAedqndrI', 'extol-shorts', 'E2', '엑스톨 Shorts, 노랑 단색 마네킹', [
 (0.0, '"2018년 3월 어느 날." 노랑·초록 단색 주차장.'), (11.8, '노란 얼굴 없는 마네킹 무리.'), (23.6, '실제 사진·뉴스 화면 삽입(사용 불가).'), (47.1, '어두운 파랑 취조실.')], notes='54초, 조회수 33,882.')
add('ds91ZveXdSA', 'extol-shorts', 'E2', '엑스톨 Shorts, 회색 + 빨강', [
 (0.0, '시점 카드 "2003년 9월 24일."'), (14.6, '빨강 인물 클로즈업, 노란 보조색.')], notes='81초, 조회수 10,241.')
add('5KO00s81QC0', 'extol-shorts', 'E2', '엑스톨 Shorts, 청록·회색', [
 (5.8, '실제 인물 사진 삽입(사용 불가).'), (23.2, '분홍 인물 군상.')], notes='60초, 조회수 3,859.')

add('PCBmzL4GpbQ', 'kr-crime-verdict', 'E3', '채널 규모 대비 고성과 판결 Shorts(구독 430, 조회 53,506)', [
 (0.0, '검정 바탕, 제목 2줄: 흰 따옴표 대사 + 초록 줄에 판결 자체("17만 원에 8개월 집행유예") — 결과를 제목에서 공개.'),
 (11.8, '사실적인 인물 이미지(하단 표기 "실제 사건 기반 재구성 · AI 재연"), 4:5 창.'),
 (35.3, '대사형 자막: 검은 상자 + 초록 글자 따옴표.'),
 (139.2, '같은 형식 반복, 하단에 작은 출처 줄.')], notes='151초. AI 재연 이미지 — 우리 규칙상 쓰지 않음.')
add('U0IutDImnJA', 'kr-broadcaster', 'E2', 'SBS 그것이 알고싶다 Shorts', [
 (0.0, '제목 띠(흰 + 빨강) + 16:9 방송 화면 창 + 하단 노란 프로그램 로고.'), (14.8, 'CCTV풍 청록 화면.'), (53.3, '자료 화면 계속.')], notes='75초.')
add('KrnvG_mf9GY', 'kr-broadcaster', 'E2', 'SBS 그것이 알고싶다 Shorts', [(0.0, '같은 레이아웃(제목 띠 + 방송 창 + 로고).')], notes='80초.')
add('lMUWr6w2oX8', 'kr-broadcaster', 'E2', 'JTBC 사건반장 Shorts', [
 (0.0, '제목 띠(흰 + 노랑) + 스튜디오 화면 창 + 빨강 그라데이션 위 로고.'), (41.6, '창 안 방송 자막.')], notes='94초.')
add('MMS6pM1dvKQ', 'kr-broadcaster', 'E3', 'KBS 뉴스 판결 Shorts(재판부 판단)', [
 (0.0, '남색 그라데이션 바탕, 따옴표 제목 2줄.'), (20.7, '판결 인용 카드: 흰 카드 + 인용문 + 인물 칩 + 법원 엠블럼.'), (29.5, '신문 지면풍 카드.'), (44.3, '창 아래 반투명 상자 자막.')], notes='60초. 자동 자막 끝 "KBS 뉴스 김범준입니다" — 기자 낭독으로 보이나 음색은 미확인.')
add('Zm3A_uNj2mo', 'kr-broadcaster', 'E2', 'MBC 실화탐사대 계열(실화 On)', [(0.0, '남색, 제목 흰 + 청록, 프로그램 화면 창, 하단 진행자·로고.'), (29.5, '얼굴 흐림 처리 자료.')], notes='58초.')
add('kJcsOC-Gb2g', 'global-courtroom', 'E3', 'Courtroom Consequences — 선고 반응', [
 (0.0, '전면 법정 실영상. 0~3초 제목 오버레이(대문자, 빨강+흰).'), (5.8, '화자 칩 "Judge"(초록 바탕) + 검은 상자 흰 자막.'), (11.7, '소리 설명 자막 "*STARTS CRYING*".'), (32.1, '반응 숏으로 끝.')], notes='35초. 실영상 — 재현 불가.')
add('NDefsGLjWmc', 'global-courtroom', 'E2', 'COURT TV — 선고 낭독', [
 (0.0, '전면 실영상, 좌상단 로고, 노란 하단 자막.'), (19.4, '가족 반응 숏 교차.'), (58.3, '마지막 자막 "And that, sir, is the judgment."')], notes='138초, 3.3M. 실영상.')
add('2cK8l5Yg5w8', 'global-motion', 'E3', 'Kurzgesagt Shorts — 평면 벡터의 프리미엄 반례', [
 (0.0, '전면 평면 벡터, 강한 그라데이션 배경, 인물 1명.'), (17.5, '기울어진 라벨 배너 "COUMARIN"(노랑 바탕 검정 글자), 원형 프레임.'), (23.3, '경고 테이프 프레임 "FREAK ACCIDENT".'), (29.1, '사물 하나 + 라벨 하나 + 작은 자막.'), (61.2, '첫 숏 인물로 돌아옴(루프).')], notes='67초, 5.08M. 밝고 채도 높지만 숏마다 한 주제·한 라벨로 절제. 자막 없음(자동 자막 미제공).')
add('SAIPNwqH978', 'global-motion', 'E3', 'Vox Shorts', [
 (0.0, '0~6초 노란 상자 질문 제목.'), (20.8, '노란 이름 칩, 흰 자막의 핵심어 노랑 하이라이트.'), (47.6, '자료 화면 혼합.')], notes='118초.')
add('6h8pLcLViC8', 'global-crime', 'E2', 'Coffeehouse Crime Shorts', [(0.0, '진행자 얼굴 + 사진·자료 화면.'), (17.7, '가운데 1~3단어 대문자 자막, 핵심어 빨강.')], notes='60초. 실사·얼굴.')
add('uXLJaEDvtHU', 'global-crime', 'E2', 'MrBallen Shorts', [(0.0, '토크 영상 + 자료 사진 인서트.')], notes='179초. 얼굴 기반.')
add('fUM81_EcAvo', 'kr-motion', 'E2', '14F 일사에프 Shorts(이번 표본은 토크 클립)', [(0.0, '제목 띠 + 토크 영상 창 + 하단 로고. 모션그래픽 아님.')], notes='56초. "14F = 모션그래픽" 가정의 반례.')
add('OBxpYW_TJvU', 'kr-motion', 'E2', 'KBS 크랩 Shorts', [(0.0, '제목 흰 + 초록, 자료 사진·영상 + 인터뷰 하단 자막.')], notes='67초.')
add('mpAS3gilamo', 'control-cheap', 'E3', '대조군: 법률 퀴즈 Shorts(형식이 가장 가까운 저품질 사례)', [
 (0.0, 'AI 생성풍 마스코트 일러스트, O/X 두 상자, 화면 전체가 글자.'), (8.5, '"3초 안에 골라보세요! 3 2 1" 카운트다운.'), (11.3, '"정답은 X!!" 외침형 글자, 효과선.'), (27.9, '"아예 하지 마!!!"')], notes='31초, 조회 631 / 구독 6.')
add('5L30F-FDBS8', 'control-cheap', 'E3', '대조군: AI 판사', [
 (0.0, '스톡·AI 이미지가 작은 가로 창에, 아래 작은 자막.'), (58.8, '"VERDICT" 홀로그램 판사 AI 이미지.')], notes='96초, 조회 2,903 / 구독 23. 소규모 채널이라 조회/구독 비율은 의미가 약함.')


add('EsGemJYqaWE', 'kr-story-outcome', 'E2', '이야기→결말형 승자(코디네이터 제시, 구독 66 / 조회 98,421)', [
 (0.0, '남색 프레임, 따옴표 제목 2줄, 실사 사진(쇠사슬 묶인 차).'), (2.9, '숫자 태그 "5시간+".'), (8.8, '평면 카툰 인물 일러스트를 실사 사이에 삽입.'),
 (23.5, '법정 사진 + 빨간 원 표시.'), (41.2, '결말 카드: 어두운 남색 카드에 법원·선고일·결과 텍스트.'), (48.7, '댓글 말풍선형 마무리 카드.')],
 notes='51초. 사건→반전(고소)→심급별 결과→최종 결론. 화면은 실사+카툰 혼합으로 저렴한 편이나 이야기 구조가 강함. 자동 자막 기준 초당 7.3음절.')
add('KsmJcoLeRJU', 'kr-story-outcome', 'E2', '이야기→결말형 승자(코디네이터 제시, 구독 2,900 / 조회 708,448)', [
 (0.0, '초록 제목 띠 "법정에 갑자기 웬 수표가?", 미국 법정 실영상 창, 핵심어 노랑·빨강 자막.'), (35.2, '판사 행동이 결말(수표) — 판결 자체보다 반전이 보상.')],
 notes='47초. 실영상(권리 미확인) — 재현 불가.')
add('t8EFnyTfgqs', 'kr-sentencing-quiz', 'E2', '한국 형량형 소채널(코디네이터 제시, 구독 28 / 조회 730)', [
 (0.0, '전면 어두운 화면, 가운데 큰 글자 "음주 뺑소니 사망 그런데 집행유예" — 결과를 훅에서 공개, 빨강 핵심어.'),
 (8.7, '비 오는 도로 이미지 + 시점 글자 "2023년 7월, 한밤".'), (26.0, '빨간 하강 선 그래프 "마이너스" — 감경 요소 시각화.'), (40.5, '"집행유예." 빨강.'), (49.1, '다음 편 예고 카드.')],
 notes='53초. 어둡고 빨강 강조인 미감인데도 저조 — "미감 = 성과"가 아님을 보여주는 반례. 이미지 출처 미확인(AI·스톡 추정).')
add('rGcRlRrtL1o', 'kr-sentencing-quiz', 'E2', '한국 법률 퀴즈 소채널(코디네이터 제시, 구독 19 / 조회 944)', [
 (0.0, '제목 띠 + AI 만화풍 법정 일러스트(그림체는 일관).'), (61.2, '고양이 마스코트 퀴즈 마무리.')], notes='68초.')
add('CJoJWoWXt9k', 'kr-motion', 'E2', '크랩 16:9 형량 비교 영상(코디네이터 제시, 1,587,293회)', [
 (7.9, '실제 법정 화면 + 빨강 자막 "징역 1,000년 선고!".'), (94.5, '기사 문서 카드, 노랑 형광 하이라이트.'), (141.8, '변호사 인터뷰.'),
 (173.3, '평면 모션그래픽 분할 화면 "대륙법 / 영미법".'), (236.4, '신문 콜라주.')],
 notes='16:9, 260초, 2020년. 분노형 비교 질문("우리는 왜 12년?")을 전문가 설명으로 풀어줌 — 법적 이유를 정확히 제시하는 구조.')

FETCHED_ONLY = ['r2uQwpaTwjs', 'E1kNZVAMwcQ', 'Ireis8rYMUU', 'V15wrmD5VFs', 'ku8TIusmD3Y', 'wjnvHmeh-co', 'KHyoKZbQ8PY', 'o0gBqs3YK_w', '4m8hIppjat4']

out = []
for f in sorted(glob.glob(str(R / 'meta' / '*.json'))):
    d = json.load(open(f)); i = d['id']
    o = O.get(i, dict(group='screen', evidence_level='E1', role='메타데이터·자막·스토리보드 수집, 화면 검토 안 함', segments=[], notes=''))
    st = stats(i)
    sb = [x for x in d.get('formats', []) if x['format_id'] in ('sb0',)]
    out.append(dict(
        id=i, url=f'https://www.youtube.com/watch?v={i}', title=d.get('title'), channel=d.get('channel'), channel_id=d.get('channel_id'),
        subscribers=d.get('channel_follower_count'), views=d.get('view_count'), likes=d.get('like_count'), comments=d.get('comment_count'),
        views_per_subscriber=round(d['view_count'] / d['channel_follower_count'], 2) if d.get('channel_follower_count') and d.get('view_count') else None,
        duration_s=d.get('duration'), upload_date=d.get('upload_date'), width=d.get('width'), height=d.get('height'),
        observed_at=datetime.datetime.fromtimestamp(d['epoch'], KST).isoformat(), group=o['group'], evidence_level=o['evidence_level'], role=o['role'],
        evidence=dict(metadata=f'meta/{i}.json', storyboard=f'frames/{i}/' if (R / 'frames' / i).exists() else None,
                      storyboard_format=(f"sb0 {sb[0]['width']}x{sb[0]['height']}, {sb[0]['rows']}x{sb[0]['columns']}/sprite" if sb else None),
                      subtitles=st.get('subs'), subtitle_kind=st.get('kind'), audio=AUDIO),
        subtitle_stats={k: st.get(k) for k in ('first_cue', 'span', 'rate', 'unit', 'hook', 'last')} if st.get('subs') else None,
        segments=o['segments'], notes=o['notes']))
order = {'E3': 0, 'E2': 1, 'E1': 2}
out.sort(key=lambda r: (order[r['evidence_level']], r['group'] != 'owner-reference', r['group']))
baseline = dict(id='v3_q011..q014', group='our-baseline', evidence_level='E3+audio(ours)',
  files=['ours/sheet_v3_q011.png', 'ours/sheet_v3_q012.png', 'ours/sheet_v3_q013.png', 'ours/sheet_v3_q014.png', 'ours/covers_q011_014.png'],
  segments=[dict(t=0.0, observation='1080x1920 남색 바탕, 상단 노란 제목 + 시리즈 태그, 가운데 1:1 평면 카툰 카드(화면 높이의 약 40%), 아래 2줄 자막, 하단 약 30% 빈 공간.'),
            dict(t=4.0, observation='효과음 글자 "덜컥!"(q011), "쿵!"(q013) — 만화식 의성어.'),
            dict(t=12.0, observation='퀴즈 카드: 베이지 종이 + A 벌금(회색)/B 집행유예(청록)/C 실형(빨강) 버튼 + 안경 쓴 판사 마스코트, "판사가 본 사정" 목록이 한 줄씩 추가.'),
            dict(t=24.0, observation='판사 마스코트가 팻말을 든 정답 카드(나무 법대).'),
            dict(t=29.0, observation='야간 거리 엔드 카드 "다음 사건도 맞혀 보세요".')],
  measured=dict(narration_rate_syl_per_s_over_span={'q011': 6.99, 'q012': 6.12, 'q013': 6.9, 'q014': 6.78}, subtitle_cue_mean_s=1.7,
                loudness='q011·q013 통합 -14.1 LUFS, LRA 1.4 / 1.8 LU (우리 파일, ffmpeg ebur128)', shots_q011='정지 장면 약 4개(기내·퀴즈 카드·정답 카드·엔드 카드)',
                tts='Supertonic M1, 속도 1.3', sfx='코드 합성 thunk/tick/knock/crash (episodes/quiz/make.py) — 청감 평가는 하지 않음'))
doc = dict(generated=datetime.datetime.now(KST).isoformat(timespec='seconds'),
  evidence_levels=dict(E3='스토리보드 전 프레임을 시점별로 검토 + 확대 크롭/전해상도 커버(oar2) + 자막 타이밍 분석',
                       E2='스토리보드 요약 시트(약 2~2.5초 간격) 검토 + 자막 분석(있을 때)',
                       E1='메타데이터·자막·스토리보드 수집만, 화면 검토 안 함 (관찰 수에 넣지 않음)',
                       screen='screen/*.json — 채널 Shorts 탭·검색 평면 목록(제목·조회수), 선별에만 사용'),
  audio_policy=AUDIO, baseline=baseline, refs=out)
json.dump(doc, open(R / 'refs.json', 'w'), ensure_ascii=False, indent=1)
from collections import Counter
print(Counter(r['evidence_level'] for r in out), len(out))
