#!/usr/bin/env python3
"""Assemble refs/2026-10-26.json from raw evidence (meta, subs, storyboards) + manual observations."""
import json, statistics, datetime, os

RAW = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(RAW), "2026-10-26.json")
TODAY = datetime.date(2026, 10, 26)
OBS_AT = "2026-10-26T15:39/16:00+09:00"

def load(p):
    return json.load(open(os.path.join(RAW, p), encoding="utf-8"))

tempo = load("tempo.json")
names = dict(l.rstrip("\n").split("\t") for l in open(os.path.join(RAW, "channels/list.tsv"), encoding="utf-8"))
chan_med = {}
for cid in names:
    rows = [json.loads(l) for l in open(os.path.join(RAW, f"channels/{cid}.jsonl"), encoding="utf-8")]
    v = [r.get("view_count") or 0 for r in rows]
    chan_med[cid] = {"n_recent_shorts": len(v), "median_views": int(statistics.median(v)) if v else None,
                     "max_views": max(v) if v else None}
queries = {e["id"]: sorted(set(e["queries"])) for e in load("search/all_candidates.json")}

# ---- manual observations (from storyboard sb0 ~1 fps, frame0.jpg, ko auto-subtitles) ----
# t in seconds. ev: frames | subtitles | frames+subtitles
V = {}
def add(vid, category, hook, case, guess, reveal, cta, tempo_note, comp, title, segs, notes=None, ev="frames", peer=False, reveal_frac=None):
    V[vid] = dict(category=category, hook_first_2s=hook, case_presentation=case, guess_prompt=guess,
                  reveal=reveal, subscribe_or_comment_call=cta, length_tempo_note=tempo_note,
                  visual_composition=comp, title_cover_pattern=title,
                  segments=[{"t": t, "observation": o, "evidence": e} for t, o, e in segs],
                  notes=notes, evidence_level=ev, format_peer_low_performer=peer, reveal_fraction=reveal_frac)

add("Nykfh2I4eBk", "국내 블랙박스 사건 + 판결",
    "0s 화면: 상단 고정 헤드라인 '가슴이 뻥 뚫리는 역대급 사이다 판결!'(흰+노랑), 중앙 블랙박스, 하단 자막 '진짜 역대급 판결이 나왔습니다' + 제보 이메일. 첫 대사 0.1s '진짜 역대급 판결이 나왔습니다.' — 판결의 방향(사이다)만 먼저 약속.",
    "블랙박스 1인칭 원본 영상 한 개를 그대로 쓰고 내레이션으로 상황 설명(3.9–16.2s: 경적→급정거 고의사고, 두 번).",
    "없음.", "17.9–20.2s '법원의 판결은 벌금 500만 원'(런타임의 약 78%), 20.2s '오랜만에 사이다네요' 직후 23s 종료.",
    "구독/댓글 요청 없음. 제보 이메일만 상시 노출.",
    "23s. 단일 연속 영상, 그래픽 비트 2개(빨간 화살표, '여기서 끝이 아님!!').",
    "3단 구성: 상단 헤드라인 / 중앙 16:9 영상 / 하단 작은 자막+제보 안내, 흰 배경.",
    "제목 '역대급 사이다 판결' = 헤드라인 축약. 결과의 '방향'만 공개하고 구체 형량은 숨김.",
    [(0.0, "고정 헤드라인 + 블랙박스, 자막 '진짜 역대급 판결이 나왔습니다'", "frames+subtitles"),
     (3.8, "빨간 화살표로 상대 차량 지목", "frames"),
     (11.5, "오버레이 '여기서 끝이 아님!!'(11.5–13.4s) — 두 번째 고의사고 예고", "frames"),
     (17.9, "'법원의 판결은 벌금 500만 원'", "subtitles"),
     (22.0, "마지막 프레임까지 같은 블랙박스 화면, 엔드카드 없음", "frames")],
    reveal_frac=0.78)

add("EsGemJYqaWE", "국내 판결 스토리 (AI 실사풍 재연 이미지 + 플랫 카툰 캐릭터 혼합, 'EP' 번호 시리즈)",
    "0s 화면: 상단 고정 2줄 '“남의 차에 손을 대? 고소할 거야”' + '남의 건물에 차 대고 고소한 차주의 결말', 중앙 쇠사슬로 묶인 차 사진, 큰 자막 '남의 건물에'. 첫 대사 0.2s '남의 건물에 허락 없이 댄 차를 관리인이 손수레와 쇠사슬로 다섯 시간 넘게 묶어 버렸습니다' — 가장 이상한 장면부터 시작.",
    "숫자 카드('5시간+', '5시간 36분')와 카툰 차주 캐릭터 대사('터미널 주차비 아깝게, 여기 잠깐 대 놓지 뭐')로 사건을 재구성. 거의 매 1초 새 이미지.",
    "영상 안의 퀴즈 없음.",
    "다단계: 26.5s '1심 무죄'(52%) → 33.3s 큰 글씨 '벌금 10만 원'(2심 유죄) → 34.3s 이전 회차 교차 카드 'EP012 · 굴삭기로 18시간 → 유죄' → 38.2s 대법원 → 44.1s '환송심도 무죄'(86%) → 45.1s '2012 → 2018'.",
    "50.1s 의견 2지선다 카드(👍 / 💬 두 줄) — 좋아요와 댓글로 입장을 나눠 표시하게 함. 구독 요청 없음.",
    "51s. 관찰상 컷 약 45개(storyboard 자동 측정 7.3회/10s).",
    "네이비 배경, 상단 헤드라인, 중앙 정사각 이미지, 이미지 하단에 1–3어절 굵은 자막 박스. 하단 1/3은 비어 있음.",
    "제목 = 인용구 + '~의 결말'. 결과를 숨긴 긴장형.",
    [(0.0, "쇠사슬 묶인 차 + 인용구 헤드라인", "frames"),
     (2.9, "숫자 카드 '5시간+'", "frames"),
     (6.9, "카툰 캐릭터(차주) 등장, 대사 자막", "frames+subtitles"),
     (19.6, "'5시간 36분 / 새벽 1시 36분까지'", "frames"),
     (26.5, "법정 사진 + '1심 무죄'", "frames+subtitles"),
     (33.3, "망치 이미지 + 대형 '벌금 10만 원'", "frames+subtitles"),
     (34.3, "'EP012 · 굴삭기로 18시간 → 유죄' 다른 회차 교차 카드", "frames"),
     (44.1, "'대법원 … 환송심도 무죄'", "frames+subtitles"),
     (50.1, "👍/💬 두 줄 의견 카드로 종료", "frames")],
    reveal_frac=0.86)

add("4oAtyLyRABA", "TV 블랙박스 프로그램 클립 재편집 (국내 민사 판결)",
    "0s 화면: 고정 헤드라인 '간만에 사이다 판결이 나온 사고'(노랑+흰), 블랙박스 화면, 자막 '길이 좁아요 가다가'. 첫 대사는 제보자 음성.",
    "블랙박스 + 출연자 리액션 컷 교차(0–24s).",
    "24.8–26.9s 내레이션 '법원에서는 어떤 판결이 통고됐을까요?' — 멈추지 않는 수사적 질문(약 60% 지점).",
    "28.2–30.5s '서울중앙지법에서 47만 4,000원 줘라'(67%) → 33–38s 항소심 '1심 취소, 청구 기각'(≈88%) → '이런 판결이 많이 나와야 돼'로 종료.",
    "없음.", "42s, 컷 약 20개(자동 5.2회/10s).",
    "상단 헤드라인, 중앙 16:9 방송 화면, 하단 검정 여백.",
    "'간만에 사이다 판결' — 결과 방향 약속형.",
    [(0.0, "헤드라인 + 블랙박스", "frames"),
     (4.9, "출연자 리액션 컷 시작", "frames"),
     (24.8, "'법원에서는 어떤 판결이…?' 수사적 질문, 멈춤 없음", "subtitles"),
     (28.2, "'47만 4,000원 줘라'", "subtitles"),
     (33.6, "'항소' → 1심 취소", "frames+subtitles"),
     (39.8, "'이런 판결이 많이 나와야 돼' 후 종료", "frames+subtitles")],
    notes="방송 콘텐츠 재사용으로 보임(권리 문제). 형식만 참고.", reveal_frac=0.86)

add("Ehjs0mbaaYw", "국내 블랙박스 사건 + 형사 판결",
    "0–2s 화면: 채널 로고, 헤드라인 '한문철TV 레전드 사건 / BMW 가오남의 최후'(흰+노랑), 사진 속 가해자에 빨간 원(결말 장면을 먼저 보여줌). 첫 대사 0.1s 헤드라인을 그대로 읽음.",
    "2.9s부터 블랙박스 + 내레이션. 19.6s 밈 컷(카툰 캐릭터 어깨 으쓱) '누가 봐도 보복운전 아닌가요?', 29.4s·40.2s 리액션 짤.",
    "수사적 질문만(19.6s), 멈춤 없음.",
    "36.3s '1심 판사의 판단은 명확했습니다' → 42.1–44.1s 키워드 카드 '특수손괴' / '징역 6개월' / '실형'(86–90%) → 45–48s 보험 지급 거절 → 49s 종료.",
    "없음.", "49s, 장면 전환 약 30회(자동 5.3회/10s).",
    "검정 프레임 + 코너 마크, 상단 헤드라인, 중앙 영상, 하단 흰 자막. 법률 용어와 형량을 스톡 이미지 위 빨간 스탬프로 표시.",
    "'~의 최후' — 결과 방향(응징) 약속형.",
    [(0.0, "결말 장면(가해자 빨간 원) + 헤드라인", "frames+subtitles"),
     (2.9, "블랙박스 시작", "frames"),
     (19.6, "카툰 밈 + '누가 봐도 보복운전 아닌가요?'", "frames+subtitles"),
     (42.1, "스탬프 카드 '특수손괴'", "frames"),
     (43.1, "스탬프 카드 '징역 6개월', '실형'", "frames+subtitles"),
     (47.0, "'보험금지급 거절' 카드", "frames")],
    reveal_frac=0.86)

add("JvJa_kdz6Yw", "해외 법정 영상 + 한국어 번역·내레이션 (하단 마스코트)",
    "0s 화면: 헤드라인 '판사에게 손가락 욕하면 벌어지는 일'(흰+빨강 키워드+노랑), 판사 얼굴과 대사 자막 '바이바이'. 하단 1/4에 호두 마스코트 고정.",
    "판사–피고인 교차컷, 대사는 노란 박스, 내레이션은 흰 자막.",
    "없음.",
    "27.8s '30일 교도소 수감을 선고합니다'(62%) → 29.7s '그리고 4일 뒤' 후일담(반성, 수감 철회) → 44s 종료.",
    "없음.", "45s, 컷 약 15개(자동 3.1회/10s).",
    "상단 헤드라인 / 중앙 영상 / 하단 정적 마스코트 캐릭터.",
    "'~하면 벌어지는 일' — 결과 예고형.",
    [(0.0, "판사 + '바이바이' 대사, 마스코트", "frames"),
     (27.8, "'30일 교도소 수감을' 선고", "frames"),
     (29.7, "'그리고 4일 뒤' 후일담", "frames"),
     (40.2, "'보석금을 줄여주고 교도소 수감도 철회해 주었죠'", "frames+subtitles")],
    notes="ASR 불완전(배경음). 화면 자막으로 판독.", reveal_frac=0.62)

add("KsmJcoLeRJU", "해외 법정 영상(프랭크 카프리오 판사) 재편집",
    "0s 화면: 질문형 헤드라인 '법정에 갑자기 웬 수표가?'(초록+흰), 판사 클로즈업, 자막 '벌금을 선고하던 판사가'. 첫 대사 0.3–2.2s '벌금을 선고하던 판사가 갑자기 수표를 꺼냅니다' — 반전 장면을 첫 문장에 제시.",
    "5.9s '총 360달러입니다' → 8–24s 피고인 사연. 화자별 자막 색(판사 노랑, 피고인 분홍).",
    "없음(헤드라인 질문은 '형량 맞히기'가 아니라 반전 장면에 대한 궁금증).",
    "30.6–36.2s '그들이 보내온 수표로 225달러가 대신 채워졌고 … 남은 벌금은 125달러'(65–77%) → 41s 포옹 → 46s 페이드아웃.",
    "없음.", "47s, 줌·클로즈업 전환 잦음(자동 6.4회/10s).",
    "상단 헤드라인, 화면 꽉 찬 세로 크롭 영상, 하단 1/3에 색 구분 자막.",
    "질문형이지만 퀴즈가 아니라 '이상한 장면' 질문.",
    [(0.0, "판사 클로즈업 + '벌금을 선고하던 판사가'", "frames+subtitles"),
     (2.0, "'갑자기 수표를 꺼냅니다'", "frames+subtitles"),
     (5.9, "'총 360달러입니다'", "frames"),
     (30.6, "'그들이 보내온 수표로 225달러가 대신 채워졌고'", "frames+subtitles"),
     (35.2, "'125달러입니다'", "frames"),
     (41.1, "포옹 장면", "frames")],
    reveal_frac=0.65)

add("ApqOKh_QTxo", "국내 블랙박스 사건 + 검찰 결정",
    "0s 화면: 헤드라인 '차 VS 사람 관행 박살 낸 검찰의 역대급 판단'(흰+노랑), 블랙박스. 0.9s 보행자에 빨간 원. 첫 대사 '왕복 8차선 도로 정상 신호에 따라 진행하던 중 보행자가 갑자기 튀어나옵니다'.",
    "빨간 원·화살표 반복, 하단에 시청자 댓글 캡처 카드(3.8–17.9s), 사고 도면.",
    "22.7–23.6s '투표' 카드 '1. 운전자 잘못 있다 / 2. 운전자 잘못 없다 → 100%' — 시청자 판단을 1초 정도 화면에 보여줌(멈춤 없음).",
    "25.5–31.8s 검찰 결정서 + '경찰과 지방경찰청은 잘못이 있다. 검사는 잘못이 없다'(81–94%) → 33s 종료.",
    "없음.", "34s(자동 4.4회/10s).",
    "상단 헤드라인, 중앙 영상/문서, 하단 검정 여백.",
    "'~박살 낸 역대급 판단' — 결과 방향 약속형.",
    [(0.9, "보행자 빨간 원", "frames"),
     (3.8, "시청자 댓글 캡처 카드", "frames"),
     (22.7, "'투표' 카드, 2번 100%", "frames"),
     (25.5, "검찰 결정서 화면", "frames"),
     (27.7, "'경찰 … 잘못이 있다 / 검사는 잘못이 없다'", "frames+subtitles")],
    reveal_frac=0.81)

add("3K0uY0x-cus", "해외 법정 영상 + 변호사 해설(PIP)",
    "0s 화면: 결과형 헤드라인 '판사 폭행한 남성 최후 / 1년 형 → ‘65년 형’'(흰+민트), 판사 화면, 하단 변호사 브랜딩. 2.9s 판사석으로 뛰어드는 습격 장면을 3초 안에 보여줌.",
    "3.6s '폭행 미수 혐의로 재판에 선 남성' → 11.2s '실형을 선고하려는 판사' → 13–16s 습격 → 17.2s 재재판.",
    "없음.",
    "30.5–37.8s '기존 폭행 미수 사건은 약 19개월에서 최대 4년 … 결국 최대 65년 형'(74–92%). 헤드라인의 숫자를 마지막에 설명.",
    "없음. 38–40s 습격 장면 반복(루프 유도로 보임).", "41s(자동 3.7회/10s).",
    "상단 헤드라인, 중앙 영상, 하단 변호사 얼굴 + 이름.",
    "'최후' + 숫자 대비(1년 → 65년) 결과 공개형.",
    [(0.0, "결과형 헤드라인 '1년 형 → 65년 형'", "frames"),
     (2.9, "습격 장면(클라이맥스) 선공개", "frames"),
     (11.2, "'실형을 선고하려는 판사'", "subtitles"),
     (30.5, "'기존 폭행 미수 사건은 약 19개월에서…'", "frames+subtitles"),
     (36.3, "'결국 최대 65년 형을 선고받죠'", "frames+subtitles"),
     (38.1, "습격 장면 반복 후 종료", "frames")],
    reveal_frac=0.88)

add("-niDfHQhqmE", "국내 실제 판결(학폭 피해자의 살인), 흐린 실사·AI풍 이미지, 음슴체 내레이션",
    "0s 화면: 긴장형 헤드라인 '학폭으로 칼을 들다 / 죽은 건 가해자'(흰+초록), 아파트 야경, 자막 '2024년 새벽'. 첫 대사 0.3–6.7s '2024년 새벽 … 18세 최군이 동급생 박군을 흉기로 찔러 살해함. 근데 숨진 박군은 학폭 가해자였음' — 4초 안에 반전.",
    "6.7–36.5s 가혹행위 정황을 이미지 1–2s 간격으로 나열(빨간 원 강조).",
    "제목 끝에 '유죄?무죄?'만 있고 영상 안 질문은 없음.",
    "39.3s '1심 장기 5년 단기 3년' → 45.1s '항소심 징역 2년 집행유예 5년'(70–82%) → 47.9–51.1s '무죄 제외 역대 최저 형량으로 기록'.",
    "52.1–55s 화면+음성 '학폭 가해자들은 능지처참 당해야 한다 생각하신다면 좋아요 눌러주세요' — 동의하면 좋아요를 누르라는 요청.",
    "56s(자동 3.4회/10s, 어두운 이미지라 낮게 측정; 육안 약 30회 전환).",
    "상단 헤드라인, 중앙 정사각 이미지, 이미지 하단 흰 자막.",
    "긴장형 헤드라인 + 제목 끝 '유죄?무죄?'.",
    [(0.0, "긴장형 헤드라인 + '2024년 새벽'", "frames+subtitles"),
     (5.9, "'숨진 박군은 학폭 가해자였음'", "frames+subtitles"),
     (39.3, "'징역 장기 5년 단기 3년이었지만'", "frames+subtitles"),
     (44.2, "'징역 2년 집행유예 5년으로'", "frames+subtitles"),
     (52.1, "좋아요 요청 문구 화면", "frames+subtitles")],
    notes="성범죄 가혹행위 묘사 포함 — 몇년나옴 금지선과 겹침. 형식만 참고.", reveal_frac=0.80)

add("XSO59xOZ0e8", "국내 판결(누명 사건), 무료 클립아트풍 캐릭터 + 실사 배경 합성, 커뮤니티 글 프레이밍",
    "0–1.9s 화면: 검은 바탕에 커뮤니티 게시글 카드 '[베스트] 쇼츠 게시판 > 결말이 이상하다는 한국 판결 근황', 고정 헤드라인 같은 문구(노랑+흰). 첫 대사 0.0s 제목을 그대로 읽음.",
    "2.0s '2015년'부터 캐릭터 대사를 큰 흰 글씨로('만졌잖아!!', '체포하라!', '당했다니까요!!'), 경고 아이콘 카드로 전환점 표시. 거의 매 1초 새 장면.",
    "37.2s '놀라운 판결을 하게 되는데?' 티저(멈춤 없음).",
    "26.6–28.4s 누명 남성 '징역 6년'(58%) → 46.1–48s 진범 '2년 6개월'(94%) 직후 종료.",
    "없음.", "49s, 장면 약 40회(자동 5.3회/10s).",
    "상단 헤드라인, 중앙 정사각 이미지(캐릭터+배경), 이미지 하단 노란 테두리 자막.",
    "'결말이 이상하다는 ~ 근황' — 결과를 숨긴 긴장형.",
    [(0.0, "커뮤니티 게시글 카드", "frames+subtitles"),
     (5.9, "캐릭터 대사 '만졌잖아!!'", "frames"),
     (17.6, "경고 아이콘 카드", "frames"),
     (27.4, "'징역 6년을 선고받게 되는데'", "frames+subtitles"),
     (37.2, "'놀라운 판결을 하게 되는데?'", "frames"),
     (47.0, "'2년 6개월형을 받게 되었다고' 후 종료", "frames+subtitles")],
    notes="성범죄 사건 — 금지선. 클립아트 캐릭터 연출만 참고.", reveal_frac=0.94)

add("2dOUKItDw2c", "법률 썰(상속 빚), 커뮤니티 게시글 템플릿 + AI 웹툰풍 일러스트, 1인칭 반말",
    "0s 화면: 네이비 헤더 '썰로몬', 게시글 제목 '몰랐던 빚 반드시 확인해야 할 1가지', 조회수 표기, 캐릭터가 시청자를 손가락으로 가리킴. 첫 대사 0.0s '지금부터 돌아가신 부모님의 모르는 빚이 나한테 넘어왔을 때 확인해야 될 걸 알려줄게'.",
    "본문이 한 줄씩 타이핑되고 일러스트가 2–4s마다 바뀜(빈 이미지 구간 있음).",
    "없음.", "23.1–29.7s '최우선으로 확인해야 할 한 가지 … 정말 몰랐는지가 중요'(54–69%).",
    "41s '변호사나 법무사는 일단 찾아가서 상담이나 받아봐라'. 구독 요청 없음.",
    "43s(자동 5.3회/10s).",
    "흰 게시글 화면, 상단 고정 헤더+제목, 중앙 정사각 일러스트, 작은 본문 글씨.",
    "'반드시 확인해야 할 1가지' — 정보 약속형.",
    [(0.0, "게시글 헤더 + 손가락 가리키는 캐릭터", "frames+subtitles"),
     (4.9, "가족 일러스트 '어렸을 때 부모님이 이혼하시고'", "frames+subtitles"),
     (16.6, "놀라는 캐릭터 '채권자가 내 통장에다 압류를'", "frames+subtitles"),
     (24.4, "체크리스트 일러스트 '최우선으로 확인해야 할 1가지'", "frames+subtitles"),
     (40.1, "변호사 사무실 일러스트 + 상담 권유", "frames+subtitles")],
    notes="2024년 영상(오래됨). 카툰/일러스트 형식 비교용.")

add("viX9bKBe8Bc", "변호사 토킹헤드 랭킹형 법률 상식",
    "0s 화면: 헤드라인 '의외로 범죄가 아닌 행동 TOP 5'(초록+흰), 변호사 전신. 첫 대사 '의외로 범죄가 아닌 행동. 탑 5위.'",
    "5위→1위 카운트다운, 반투명 리스트 패널이 항목마다 채워짐(1.0s부터).",
    "없음.", "1위를 19.9–24.0s(80–96%)까지 보류.", "없음.",
    "25s, 단일 테이크(자동 0.4회/10s, 리스트 패널 갱신만).",
    "인물 중앙, 하단 반투명 리스트 패널, 상단 헤드라인.", "'의외로 ~ TOP 5' 랭킹형.",
    [(0.0, "헤드라인 + 변호사", "frames+subtitles"),
     (1.0, "빈 리스트 패널 등장(5칸)", "frames"),
     (19.9, "'1위 자기 사건 증거 직접 없애기'", "subtitles")],
    reveal_frac=0.80)

add("efhcMCRukh4", "해외 음주운전 사망사고 법정 영상 재구성",
    "0s 화면: 헤드라인 '미국에선 음주운전하면 / 자비는 없다'(흰+노랑) — 중형이라는 방향을 먼저 공개, 주황 수의 피고인. 첫 대사 0.1s '음주 운전으로 가족 세 명을 숨지게 한 여자가 … 기억이 없다고 주장합니다'.",
    "4.9–24s 항공 영상, 머그샷, 피해 가족 사진, 유족 진술.",
    "없음.", "30.9s '판사는 선고합니다' → 39.8s '징역 50년'(85%).",
    "43.5–46s 화면+음성 '이 판결에 대해 여러분은 어떻게 생각하시나요?'",
    "47s(자동 4.3회/10s).", "상단 헤드라인, 중앙 영상, 하단 흰 자막.",
    "'~하면 자비는 없다' — 결과 방향 공개형.",
    [(0.0, "헤드라인 + 피고인", "frames+subtitles"),
     (5.9, "사고 항공 영상 + 머그샷 '시속 190km로'", "frames+subtitles"),
     (30.4, "'판사는 선고합니다'", "frames+subtitles"),
     (39.8, "'가해자에게는 징역 50년이 선고되었고'", "subtitles"),
     (45.0, "'어떻게 생각하시나요?' 화면", "frames+subtitles")],
    reveal_frac=0.85)

add("-gaDkoZU6mM", "해외 법정 사진·영상 재구성(채널 브랜드 하단 고정)",
    "0s 화면: 피고인 입에 테이프를 붙이는 장면 + 헤드라인 '판사가 베푼 마지막 관용'(저울 아이콘). 첫 대사 0.1–2.9s '법정에서 피고인의 입에 테이프가 붙여집니다. 이게 도대체 무슨 일일까요?' — 기묘한 장면 + 질문.",
    "3.9–33s 사건 배경, 판사 교체. 대사는 노랑/초록 자막.",
    "1.6–2.9s 수사적 질문(형량 질문 아님).",
    "45.8–47.5s '최초 형량보다 두 배 이상 많은 33년'(88%) → 49.3s 엄마와 포옹 허락('관용').",
    "49–51s 화면 '판사의 판결이 어떠신가요?'", "52s(자동 6.9회/10s).",
    "상단 헤드라인(찢어진 종이 테두리), 중앙 이미지, 하단 손글씨 브랜드 '판결의 순간'.",
    "'판사가 베푼 마지막 관용' — 결과 일부 공개 + 궁금증.",
    [(0.0, "테이프 붙이는 장면", "frames+subtitles"),
     (2.9, "'이게 도대체 무슨 일일까요?'", "frames+subtitles"),
     (45.3, "'33년형을 선고했습니다'", "frames+subtitles"),
     (49.1, "'판사의 판결이 어떠신가요?'", "frames")],
    notes="채널 중앙값 대비 1.4배로 채널 안에서는 이상치가 아님. 상위 채널 사례로 포함.", reveal_frac=0.88)

add("8JHDPfnJVaw", "변호사 2인 대화형 판결 해설(메신저 말풍선 자막)",
    "0s 화면: 질문형 헤드라인 '바벨에 깔렸다 / 헬스장 책임X?' + 말풍선 '변호사님'. 첫 대사 '변호사님 헬스장에 상주하는 사람 없으면 불법이죠? 네.'",
    "2.8s B-roll(벤치프레스), 5.9–7.5s '1심 무죄' 언급, 15.8s 밈 컷.",
    "12.8s '그럼 유죄라고 보시나요?'(질문자→변호사).",
    "판결은 초반(23–29%)에 언급, 이후 변호사 의견으로 종료.", "없음.",
    "26s(자동 5.8회/10s).", "인물 중앙, 말풍선 자막(흰=질문자, 초록=변호사), 상단 헤드라인.",
    "질문형 헤드라인.",
    [(0.0, "질문형 헤드라인 + 말풍선", "frames+subtitles"),
     (2.8, "벤치프레스 B-roll", "frames"),
     (12.8, "'그럼 유죄라고 보시나요?'", "subtitles"),
     (15.8, "스펀지밥 밈 컷", "frames")],
    notes="채널 중앙값 대비 1.2배 — 이상치 아님.")

add("7MrLyfL34GA", "버스 흡연 상황 실사 영상 + 말풍선 자막",
    "0s 화면: 질문형 헤드라인 '버스에서 담배피면 / 벌금 얼마?!'(흰+민트), 자막 '담배 피면 얼마 정도 벌금 나오는교'.",
    "승객–기사 실랑이 실사(출처 미표기).", "제목/헤드라인 질문만.",
    "벌금액은 영상 끝까지 나오지 않음(자막 전체 확인) — 답 없는 질문형.", "없음.",
    "20s(자동 8.0회/10s).", "상단 헤드라인, 중앙 실사, 말풍선형 자막.",
    "질문형 + 답 미제공.",
    [(0.0, "질문형 헤드라인 + 흡연 장면", "frames+subtitles"),
     (8.6, "'승객을 이런 식으로 하면 됩니까?'", "frames+subtitles"),
     (17.1, "'가자고요' 후 종료, 금액 언급 없음", "frames+subtitles")])

add("t8EFnyTfgqs", "형량 '계산' 쇼츠 — 몇년나옴과 가장 가까운 형식(국내 실제 판결)",
    "0s 화면: 고정 헤드라인 없음. 어두운 AI 배경 중앙 큰 글씨 '음주 뺑소니 / 사망 / 그런데 / 집행유예'(빨강) — 정답까지 공개한 결과형. 첫 대사 '사람을 치고 그대로 도망쳤습니다. 그런데 감옥엔 하루도 안 갑니다.'",
    "6.1s '사건을 입력합니다' → 18.4s '계산을 시작합니다. 도주치사, 시작은 징역 2년 6개월' → 감경 요소마다 '마이너스'(24–36s).",
    "44.3–48.2s '여러분의 계산은 몇 년입니까? 댓글로 알려주세요'(정답 공개 후).",
    "39–40.5s '이렇게 빼고 나온 답이, 집행유예'(76%) → 42.3s '사람이 죽었는데 실형은 없었습니다'.",
    "댓글 요청 + 49.8–52s '다음 사건, 내일 저녁 6시에 접수됩니다'. 50.1s 화면에 템플릿 변수 '{{v2}}'가 그대로 노출됨.",
    "53s(자동 1.9회/10s).", "검정 배경, 화면 중앙 대형 텍스트, 상단 헤드라인 없음.",
    "결과형(정답 공개) 헤드라인.",
    [(0.0, "'음주 뺑소니 사망 그런데 집행유예'", "frames"),
     (6.7, "'사건을 입력합니다'", "frames+subtitles"),
     (20.2, "'도주치사, 시작은 징역 2년 6개월'", "frames+subtitles"),
     (26.0, "'마이너스.' 카드(빨간 하락 그래프)", "frames"),
     (40.5, "'집행유예.'", "frames+subtitles"),
     (45.3, "'몇 년입니까 / 댓글로 알려주세요'", "frames+subtitles"),
     (50.1, "'접수됩니다.{{v2}}' 템플릿 변수 노출", "frames")],
    notes="저성과 동종 대조군(구독자 28, 최근 쇼츠 40개 중앙값 815회).", peer=True, reveal_frac=0.76)

add("rGcRlRrtL1o", "가상 사례 법률 퀴즈(AI 법정 일러스트, 고양이 마스코트)",
    "0s 화면: 헤드라인 '선고 중 난동피우다 / 형량이 늘어난 사건' + 하단 '냐옹이판사 알쏭달쏭 생활법률 퀴즈'. 첫 대사 '우리나라 법정에서 판결을 마음에 안 든다고 피고인이 난동을 피우면 어떻게 될까요?'",
    "15–17s 징역 1년 선고 → 난동 → 39.4s 징역 3년으로 정정.",
    "47.6s(70%) '다음 중 누구의 말이 맞을까요? 1) 판사 2) A씨' 보기 화면.",
    "62.2s '정답: 2) A씨'(91%).", "63–66s 고양이 마스코트 '구독&좋아요'.",
    "68s(자동 6.5회/10s).", "상단 헤드라인, 중앙 AI 일러스트, 하단 노란 자막.",
    "사건 요약형 헤드라인.",
    [(0.0, "헤드라인 + 법정 일러스트", "frames+subtitles"),
     (39.4, "'징역 3년에 처한다'", "subtitles"),
     (47.6, "퀴즈 보기 '1) 판사 2) A씨'", "frames+subtitles"),
     (62.2, "'정답: 2) A씨'", "frames"),
     (64.1, "마스코트 '구독&좋아요'", "frames")],
    notes="저성과 퀴즈 동종 대조군(구독자 19).", peer=True, reveal_frac=0.91)

add("FLcCGqxBMuY", "해외 바디캠 영상 + 한국어 대사 자막",
    "0s 화면: 헤드라인 '부패한 경찰이 / 판사의 차량을 세웠다'(노랑+흰) — 아이러니 설정, 바디캠 화면에서 판사가 차 문을 열고 나옴.",
    "3.9–8.9s '의심스럽게 운전하셔서', '제한속도가 58km인데 48km로 달리셨어요' 등 노란 대사 자막.",
    "없음.", "41–48s '그쪽이 판사라고요?' 반전(약 75%).",
    "56.1–58s 보라색 엔드카드 '구독! 좋아요! 알림설정! 부탁드리겠습니다! / 궁금한 뒷 이야기는 고정댓글에!' — 결말을 고정댓글로 넘김.",
    "59s(자동 7.1회/10s).", "상단 헤드라인, 중앙 바디캠, 하단 출처 표기.",
    "아이러니 설정형 헤드라인.",
    [(0.0, "헤드라인 + 바디캠", "frames"),
     (6.9, "'제한속도가 58km인데'", "frames"),
     (44.2, "'그쪽이 판사라고요?'", "frames"),
     (56.1, "엔드카드 '구독! 좋아요! 알림설정! … 뒷 이야기는 고정댓글에!'", "frames")],
    notes="원음 영어. ko 자동(번역) 자막은 HTTP 429로 받지 못함 — 화면 자막만 판독.", reveal_frac=0.75)

add("76soQnhHk58", "국내 판결 요약(커뮤니티 게시글 템플릿 '실화판결 요약', 스톡 사진, 음슴체)",
    "0s 화면: 게시글 제목 '주차하려고 법 어긴 부부, 그 끝은?' + 본문 '죽은 아버지가' + 실루엣 사진. 첫 대사 '죽은 아버지가 살아 있다고.'",
    "한 줄마다 스톡 사진 교체(약 1s).", "없음.",
    "15.2–17.3s '공문서부정행사죄, 위계공무집행방해죄 인정됨. 둘 다 징역형 다만 집행유예로 감'(63–72%).",
    "20.3–23.1s '이런 판결 더 알고 싶음? 구독하고 다음 이야기도 확인하셈' + 종 아이콘.",
    "24s(자동 5.4회/10s).", "흰 게시글 화면, 손글씨풍 폰트, 중앙 사진.",
    "'~그 끝은?' 결말 질문형.",
    [(0.0, "게시글 제목 + '죽은 아버지가'", "frames+subtitles"),
     (15.7, "'둘 다 징역형' + GAME OVER 이미지", "frames+subtitles"),
     (20.3, "'더 알고 싶음? 다음 이야기도 확인하셈' 종 아이콘", "frames+subtitles")],
    reveal_frac=0.68)

videos = []
for vid, obs in V.items():
    m = load(f"meta/{vid}.json")
    fc = m.get("channel_follower_count") or 0
    views = m.get("view_count") or 0
    cm = chan_med.get(m["channel_id"], {})
    ud = datetime.datetime.strptime(m["upload_date"], "%Y%m%d").date()
    has_subs = os.path.exists(os.path.join(RAW, f"subs/{vid}.ko-orig.vtt")) or os.path.exists(os.path.join(RAW, f"subs/{vid}.ko.vtt"))
    ev_sources = ["metadata(yt-dlp --dump-json)", "frame0.jpg", "storyboard sb0 (~1 fps)"] + (["ko auto-subtitles"] if has_subs else [])
    videos.append({
        "id": vid, "url": f"https://www.youtube.com/shorts/{vid}", "title": m.get("title"),
        "channel": m.get("channel"), "channel_id": m.get("channel_id"),
        "channel_follower_count": fc, "upload_date": m.get("upload_date"), "age_days": (TODAY - ud).days,
        "duration_s": m.get("duration"), "view_count": views, "like_count": m.get("like_count"),
        "comment_count": m.get("comment_count"),
        "views_per_subscriber": round(views / fc, 1) if fc else None,
        "comments_per_1k_views": round((m.get("comment_count") or 0) * 1000 / views, 2) if views else None,
        "channel_recent_shorts": cm, "views_vs_channel_median": round(views / cm["median_views"], 1) if cm.get("median_views") else None,
        "description_excerpt": (m.get("description") or "")[:240],
        "found_via": queries.get(vid, []),
        "category": obs["category"],
        "evidence_level": "frames" if obs["evidence_level"] == "frames" else obs["evidence_level"],
        "evidence_sources": ev_sources,
        "subtitles_available": has_subs,
        "observed_at": OBS_AT,
        "hook_first_2s": obs["hook_first_2s"], "case_presentation": obs["case_presentation"],
        "guess_prompt": obs["guess_prompt"], "reveal": obs["reveal"], "reveal_fraction_of_runtime": obs["reveal_fraction"],
        "subscribe_or_comment_call": obs["subscribe_or_comment_call"],
        "length_tempo": {"duration_s": m.get("duration"), "note": obs["length_tempo_note"],
                          "storyboard_visual_changes_per_10s": tempo[vid]["changes_per_10s"],
                          "method": "consecutive sb0 frame mean-abs-diff > 18 (0–255); ~1 fps sampling, lower bound for cuts, counts camera motion too"},
        "visual_composition": obs["visual_composition"], "title_cover_pattern": obs["title_cover_pattern"],
        "segments": obs["segments"], "format_peer_low_performer": obs["format_peer_low_performer"],
        "notes": obs["notes"],
    })

# metadata-only screened (not observed)
selected = set(V)
screened = []
for fn in sorted(os.listdir(os.path.join(RAW, "meta"))):
    if not fn.endswith(".json") or fn.startswith("own_"):
        continue
    vid = fn[:-5]
    if vid in selected:
        continue
    try:
        m = load(f"meta/{fn}")
    except Exception:
        continue
    screened.append({"id": vid, "title": m.get("title"), "channel": m.get("channel"),
                     "channel_follower_count": m.get("channel_follower_count"), "view_count": m.get("view_count"),
                     "upload_date": m.get("upload_date"), "duration_s": m.get("duration"),
                     "evidence_level": "metadata-only", "why_not_observed": "screened for size/recency/format; not selected for the 20"})

own = load("meta/own_IKjz8gGErMk.json")
own_baseline = {
    "id": "IKjz8gGErMk", "title": own.get("title"), "view_count": own.get("view_count"), "duration_s": own.get("duration"),
    "upload_date": own.get("upload_date"), "evidence_level": "frames", "evidence_sources": ["storyboard sb0", "frame0.jpg", "ko auto-subtitles"],
    "storyboard_visual_changes_per_10s": tempo["IKjz8gGErMk"]["changes_per_10s"],
    "segments": [
        {"t": 0.0, "observation": "헤더 '몇년나옴 · 형량 퀴즈 #1' + 헤드라인 '음주운전 신고하려던 사람을 차로 2번 박았다 / 몇 년 받았을까?'(질문형), 카툰 장면", "evidence": "frames"},
        {"t": 0.2, "observation": "첫 대사 '음주 운전 신고하려던 30대 남성을 20대 여성 운전자가 차로 두 번 박았습니다'", "evidence": "subtitles"},
        {"t": 4.7, "observation": "'쾅!' 효과, 5.6s '약 34일 치료' 카드, 8.4s '반성 없음' 스탬프", "evidence": "frames"},
        {"t": 10.2, "observation": "보기 카드 A 벌금 / B 집행유예 / C 실형 + '댓글로 먼저 찍고 보기', 14.0–15.8s 3-2-1 카운트다운 — 정적 구간 약 6s(런타임의 21%)", "evidence": "frames+subtitles"},
        {"t": 16.8, "observation": "'정답은' → 17.7s '징역 8개월 집행유예 2년'(62%), 헤드라인이 '정답: …'으로 바뀜", "evidence": "frames+subtitles"},
        {"t": 19.6, "observation": "'집행유예 이유' 리스트 3줄", "evidence": "frames+subtitles"},
        {"t": 23.3, "observation": "엔드카드 '다음 사건도 맞혀 보세요 / 몇년나옴?' 약 3s 정지 화면", "evidence": "frames+subtitles"}],
    "caveat": "다른 공개 쇼츠 3편(6–7회)은 2026-10-26 같은 날 업로드돼 몇 시간밖에 안 됐음. 조회수 차이를 형식 차이로 읽지 말 것."}

cases = [
    {"id": "C1", "source_url": "https://kapwing.com/resources/we-grew-a-faceless-youtube-channel-to-1000-subscribers",
     "author": "Julia Enthoven (Kapwing)", "published": "2025-01-06", "observed_at": "2026-10-26",
     "channel": "In the Now by Kapwing (UC2t1MoBsrxynD_UIE4xCO9g)", "niche": "스포츠 뉴스 → 여자 체조, AI 음성(ElevenLabs) 얼굴 없는 쇼츠",
     "claimed_growth": "구독자 0 → 1.2k, 157일(2024-06-17 → 2024-11-21), 쇼츠 58 + 일반 2, 총 1.1M 조회, 평균 19k, 최고 216k",
     "method": "검색되는 질문형 주제('Is Simone Biles injured?'), 반복 시리즈 틀('Hardest routine on ___'), 선수 일대기, 구독 요청 문구",
     "verification": "부분 교차확인(yt-dlp): 가장 오래된 쇼츠 92UXZFwFvgU 업로드 2024-06-17(일치), 현재 구독자 1,330, 쇼츠 59 + 일반 4, 최신 쇼츠 2025-05-05(이후 활동 중단). 조회수 합계와 일자별 구독 추이는 확인 못 함.",
     "self_reported": True, "cross_checked": "partial",
     "conflict_of_interest": "Kapwing이 자사 편집기·Script-to-Video 도구를 본문 내내 홍보."},
    {"id": "C2", "source_url": "https://x.com/FacelessPrinter/status/1889709297212264578",
     "retrieved_via": "https://api.fxtwitter.com/FacelessPrinter/status/1889709297212264578 (공개 임베드 미러, 로그인 없음)",
     "author": "@FacelessPrinter", "published": "2025-02-12", "observed_at": "2026-10-26",
     "channel": "Quiz Sloth (@quiz_sloth) — 첨부 스크린샷으로 식별(당시 112K, 152 videos)",
     "niche": "퀴즈(롱폼 10–50분 'Guess the …' 영상)",
     "claimed_growth": "개설 4개월 만에 15.2M 조회, '$3 RPM이면 $45,000+'(가정 계산)",
     "method": "Canva로 30문항 퀴즈 영상, ElevenLabs 음성, CapCut 편집, 반복 업로드, 이후 외주",
     "verification": "교차확인(yt-dlp): 가장 오래된 영상 WmP1V2XirhI 2024-09-12(게시 5개월 전, 대체로 일치), 현재 구독자 311,000, 영상 382개. Shorts 탭 0개 → 쇼츠 사례가 아님. 수익 주장은 확인 불가(가정 계산).",
     "self_reported": False, "cross_checked": "partial (channel exists, start date consistent; views/revenue not verified)",
     "conflict_of_interest": "게시자는 채널 운영자가 아님. 프로필 '$3M+ without showing my face … Start your YouTube journey' + 유료 Whop 커뮤니티 링크."},
    {"id": "C3", "source_url": "https://x.com/Ytautomation6/status/1990141612836401259",
     "retrieved_via": "api.fxtwitter.com 미러", "author": "@Ytautomation6", "published": "2025-11-16", "observed_at": "2026-10-26",
     "channel": "비공개(식별 불가)", "niche": "얼굴 없는 트루크라임",
     "claimed_growth": "구독자 22K, 3.5M+ 조회, 업로드 260+, 월 $1K+ — 판매 매물",
     "method": "명시 없음", "verification": "채널 식별 불가로 교차확인 불가.", "self_reported": True, "cross_checked": "no",
     "conflict_of_interest": "채널 판매 + '채널 대신 만들어 드림' 대행 광고."},
    {"id": "C4", "source_url": "https://flippa.com/12742356-high-performing-true-crime-youtube-shorts-channel-with-viral-content-format-strong-engagement-and-excellent-monetization-potential",
     "author": "Flippa 판매자(익명)", "published": "미표기", "observed_at": "2026-10-26",
     "channel": "비공개(익명 매물)", "niche": "바디캠 영상 기반 트루크라임 쇼츠",
     "claimed_growth": "1년에 구독자 65,000, 게시물 241, 월 매출 $3,416(검색 요약에는 월 이익 $2,681로 표기돼 수치가 엇갈림), 호가 $22,000",
     "method": "사건 조사 → 대본 → 편집 → 꾸준한 업로드, 바디캠 영상 사용",
     "verification": "채널 비공개로 교차확인 불가.", "self_reported": True, "cross_checked": "no",
     "conflict_of_interest": "판매 매물 설명."},
    {"id": "C5", "source_url": "https://x.com/mung99933/status/2101220953573487043 (X 아티클 '유튜브 기본강의 chapter2. (1천벽과 1만벽의 진실)')",
     "retrieved_via": "api.fxtwitter.com 미러(본문 텍스트만; 본문 속 스크린샷은 받지 않음)",
     "author": "@mung99933 (야옹야옹, 팔로워 7,243)", "published": "2026-09-19", "observed_at": "2026-10-26",
     "channel": "식별 불가(스크린샷 속 신규 스포츠 채널, 이름 미기재)", "niche": "스포츠 쇼츠(글 작성용 신규 채널)",
     "claimed_growth": "두 번째 영상부터 반응, 세 번째 영상 100만 회 돌파. 조회수 구간별 '벽'(5–50 / 100–500 / 1천–1만 / 1만+) 주장. 보통 영상 6개 안에 10만 회가 나오고, 10개 안에 안 나오면 방향이 틀렸을 확률이 높다는 주장.",
     "method": "유행 템플릿(커뮤니티폼·썰쇼츠·랭킹 등)을 시크릿 모드로 1시간 쇼츠 피드를 보며 골라 템포·TTS·폰트·BGM까지 그대로 따라 하기. 1천 회 벽 = 기본 품질(템포·시각자료·TTS·템플릿) 테스트라는 주장.",
     "verification": "채널 식별 불가 → 교차확인 불가. 구간별 알고리즘 설명은 근거 없는 주장으로 취급.", "self_reported": True, "cross_checked": "no",
     "conflict_of_interest": "강의 판매는 안 보임. 글 끝에 음식점·양조장 광고."},
    {"id": "C6", "source_url": "https://www.youtube.com/watch?v=wCYnkhuXe84",
     "found_via": "readray.ai(구 lilys.ai) 요약 노트 → yt-dlp 검색으로 원본 확인",
     "author": "유튜버랩 (UCCcsXVGRyiN_SnFM3r0c4Xg, 구독자 2,170)", "published": "2025-07-14", "observed_at": "2026-10-26",
     "channel": "식별 불가(본인의 얼굴·목소리 없는 지식·이슈·썰 채널이라고만 밝힘)", "niche": "지식/이슈 쇼츠",
     "claimed_growth": "쇼츠 1개(약 78만 회)로 구독자 9,700명(약 12.4명/1천 회). 그 전 6개월은 신규 시청자 정체.",
     "method": "최근 6개월 댓글 전수 분석 → 정보 영상 중간에 운영자 TMI·주관 삽입 → '쉬어가는 영상'(제작 과정, 어려움, 감사) 1편 발행. 그 영상에서만 9,700명 증가.",
     "verification": "본 채널이 공개되지 않아 교차확인 불가. 자막(ko auto)으로 영상 내 주장만 확인.", "self_reported": True, "cross_checked": "no",
     "conflict_of_interest": "자기 유튜브 팁 채널 구독 유도. 설명란에 유료 상품 없음."},
]

excluded_sources = [
    {"url": "https://subscribr.ai/youtube-strategy/faceless-youtube-channel-growth", "why": "도구 판매사 요약글. '자동차 채널 0→1,500' 사례가 채널 식별 없이 인용됨 — 사례로 세지 않음."},
    {"url": "https://shortsfast.com/blog/faceless-youtube-channel-pre-flight-checklist-2026/", "why": "도구 판매사 일반 가이드, 사례 없음."},
    {"url": "https://www.hollywoodreporter.com/business/digital/tiktok-creators-youtube-shorts-amid-insane-subscriber-growth-1235002615/", "why": "검색 요약상 이미 틱톡 수백만 팔로워였던 크리에이터 사례 — '0에서 시작한 얼굴 없는 채널'이 아님."},
    {"url": "https://tilnote.io/pages/6a035a63b62fc097dcd79751", "why": "수익화 조건 일반 정보, 사례 없음."},
    {"url": "https://kapwing.com (C1과 같은 주장을 인용한 shortsfast/subscribr 글)", "why": "같은 주장의 재인용 — 별도 사례로 세지 않음."},
]

unreachable = [
    {"source": "x.com 게시물 직접 열람", "url": "https://x.com/FacelessPrinter/status/1889709297212264578", "status": "HTTP 402 (WebFetch)", "workaround": "api.fxtwitter.com 공개 미러로 본문·작성일·첨부 이미지 URL 확보"},
    {"source": "X 검색 화면", "url": "https://x.com/search", "status": "로그인 필요 — 시도하지 않음", "workaround": "웹 검색을 x.com/twitter.com 도메인으로 제한해 게시물 발견"},
    {"source": "xcancel.com 미러", "url": "https://xcancel.com/FacelessPrinter/status/1889709297212264578", "status": "HTTP 451"},
    {"source": "nitter.net 미러", "url": "https://nitter.net/FacelessPrinter/status/1889709297212264578", "status": "HTTP 200이지만 본문 없는 껍데기 페이지(title만)"},
    {"source": "@mung99933 X 아티클 속 채널 스크린샷", "status": "미수집 — 본문에 채널명이 없어 사례 C5의 채널을 식별하지 못함"},
    {"source": "Reddit 검색(r/NewTubers)", "url": "https://www.reddit.com/r/NewTubers/search.json?q=…", "status": "HTTP 403; old.reddit.com은 HTTP 302 리다이렉트", "workaround": "없음 — Reddit 사례 미수집"},
    {"source": "Rizzle 얼굴 없는 채널 사례 글", "url": "https://rizzle.com/blog/post/case-study-for-faceless-youtube-videos-channel", "status": "HTTP 404"},
    {"source": "Indie Hackers 얼굴 없는 채널 한 달 후기", "url": "https://indiehackers.com/post/i-invested-5-min-per-day-for-a-month-into-my-faceless-youtube-channel-results-f919afdc1e", "status": "HTTP 403"},
    {"source": "FLcCGqxBMuY 한국어 자동 자막", "status": "HTTP 429 Too Many Requests 3회(원음 영어) — 화면 자막으로만 관찰"},
    {"source": "yt-dlp YouTube 검색 + Shorts 필터(sp=EgIQCQ%3D%3D)", "status": "0건(추출기가 shorts lockup을 파싱하지 않음)", "workaround": "로그아웃 상태 검색 HTML + youtubei 이어받기를 직접 파싱(shorts_search.py)"},
    {"source": "해시태그 페이지 #형량퀴즈 #판결퀴즈 #몇년받았을까", "status": "0건"},
    {"source": "yt-dlp 스토리보드 .mhtml", "status": "webp 페이로드 1바이트 잘림으로 디코딩 깨짐", "workaround": "스토리보드 스프라이트 URL을 직접 받아 재구성"},
    {"source": "/opt/homebrew/bin/yt-dlp", "status": "bad interpreter(python3.13 없음)", "workaround": "~/.local/bin/yt-dlp 2026.10.21 사용"},
    {"source": "다른 채널의 유지율·CTR·구독 전환", "status": "비공개 지표 — 추정하지 않음"},
]

# ---- search log ----
search_log = [json.loads(l) for l in open(os.path.join(RAW, "search/search_log.jsonl"), encoding="utf-8")]
for q in search_log:
    q.setdefault("tool", "youtube")
search_log += [
    {"tool": "yt-dlp", "query": "ytsearch20:형량 퀴즈", "method": "yt-dlp ytsearch --flat-playlist", "results": 20, "pages_reached": 1, "error": None, "note": "대부분 롱폼 — 폐기", "observed_at": "2026-10-26T15:24+0900"},
    {"tool": "yt-dlp", "query": "ytsearch40:형량 퀴즈 shorts", "method": "yt-dlp ytsearch --flat-playlist", "results": 40, "pages_reached": 2, "error": None, "note": "쇼츠가 거의 안 잡힘 — 쇼츠 전용 파서로 전환", "observed_at": "2026-10-26T15:26+0900"},
    {"tool": "yt-dlp", "query": "results?search_query=형량 퀴즈&sp=EgIQCQ%3D%3D", "method": "yt-dlp URL", "results": 0, "pages_reached": 1, "error": "no entries parsed", "observed_at": "2026-10-26T15:25+0900"},
    {"tool": "oembed", "query": "youtube.com/oembed for 901 candidate ids with ≥5k views", "method": "제목·채널 선별", "results": 888, "pages_reached": None, "error": "13 failed", "observed_at": "2026-10-26T15:37+0900"},
    {"tool": "yt-dlp", "query": "--dump-json --skip-download for 55 shortlisted Shorts", "method": "메타데이터", "results": 55, "pages_reached": None, "error": None, "observed_at": "2026-10-26T15:39+0900"},
    {"tool": "yt-dlp", "query": "channel/<id>/shorts --flat-playlist --playlist-end 100 for 20 channels", "method": "채널 최근 쇼츠 조회수 중앙값", "results": 20, "pages_reached": None, "error": None, "observed_at": "2026-10-26T15:48+0900"},
    {"tool": "yt-dlp", "query": "ytsearch8:쇼츠 하나로 구독자 9700명 / ytsearch5:유튜버랩 쇼츠 구독자", "method": "사례 C6 원본 찾기", "results": 13, "pages_reached": 1, "error": "첫 시도(긴 질의)는 0건", "observed_at": "2026-10-26T15:52+0900"},
]
web = [
    ("faceless YouTube Shorts channel 0 to 1000 subscribers true crime case study", 9),
    ("site:x.com faceless shorts channel subscribers in 30 days quiz shorts", 9),
    ("유튜브 쇼츠 얼굴 없는 채널 구독자 0에서 1000명 후기 썰 채널", 9),
    ("true crime YouTube Shorts channel grew from zero subscribers in months interview creator story 2025", 18),
    ("쇼츠 채널 운영 후기 구독자 1만 달성 사건 썰 채널 블로그", 9),
    ("courtroom sentencing shorts channel growth subscribers \"shorts\" reddit faceless court cam channel results", 10),
    ("[x.com,twitter.com] faceless shorts channel \"subscribers\" \"days\" true crime OR quiz OR court thread", 10),
    ("[x.com,twitter.com] 쇼츠 구독자 1000명 달성 채널 개설 개월", 9),
    ("썰쇼츠 채널 운영 3개월 구독자 후기 브런치 OR 블로그 사건사고 쇼츠", 9),
    ("reddit \"faceless\" shorts channel true crime OR courtroom \"first 1000 subscribers\" what worked", 9),
    ("쇼츠 채널 개설 한 달 만에 구독자 1만 명 인터뷰 얼굴 없는 채널 운영자", 9),
    ("\"quiz\" YouTube Shorts channel grew subscribers case study interactive \"comment your answer\" growth results", 9),
]
for q, n in web:
    search_log.append({"tool": "web_search", "query": q, "method": "WebSearch (standard)", "results": n, "pages_reached": 1, "error": None, "observed_at": "2026-10-26T15:49–16:00+0900"})
for u, st in [("kapwing.com case", "ok"), ("flippa 12742356", "ok"), ("rizzle.com case", "404"), ("lilys.ai → readray.ai note", "ok (301 → refetch)"),
              ("tilnote.io 6a035a…", "ok (사례 아님)"), ("indiehackers post", "403"), ("x.com status", "402"),
              ("blog.youtube interactive Shorts", "ok"), ("api.fxtwitter.com ×3", "200"), ("xcancel.com", "451"), ("nitter.net", "200 shell"),
              ("reddit search.json", "403"), ("old.reddit search.json", "302")]:
    search_log.append({"tool": "fetch", "query": u, "method": "WebFetch/curl", "results": None, "pages_reached": 1, "error": None if st.startswith(("ok", "200")) else st, "status": st, "observed_at": "2026-10-26T15:49–16:00+0900"})

hypotheses = [
    {"id": "H1", "area": "0프레임 훅·첫 대사·제목/커버 — 결과형(긴장형) vs 질문형",
     "statement": "0프레임 헤드라인과 첫 대사를 '몇 년 나왔을까?' 질문 대신, 판결이 왜 놀라운지 보여주는 긴장 문장(결과의 방향이나 모순만 공개, 정확한 형량은 숨김)으로 바꾸면 피드에서 넘기지 않고 보는 비율이 오른다.",
     "supporting_video_ids": ["Ehjs0mbaaYw", "EsGemJYqaWE", "XSO59xOZ0e8", "-niDfHQhqmE", "3K0uY0x-cus", "Nykfh2I4eBk", "4oAtyLyRABA", "ApqOKh_QTxo", "efhcMCRukh4", "JvJa_kdz6Yw", "FLcCGqxBMuY"],
     "evidence_summary": "동종 대조군 2편을 뺀 관찰 영상 18편 중 14편은 0프레임이 결과 방향·긴장 진술('~의 최후', '~의 결말', '사이다 판결', '죽은 건 가해자', '1년 형 → 65년 형')이고 4편만 질문형(KsmJcoLeRJU, 7MrLyfL34GA, 8JHDPfnJVaw, 76soQnhHk58). 그 4편도 '몇 년?'을 맞히라는 질문이 아니라 반전 장면·실생활·결말에 대한 질문이다. 잘 된 영상은 가장 이상한 사실을 첫 4초 안에 말한다(EsGemJYqaWE 0.2s 쇠사슬 5시간, -niDfHQhqmE 4s '숨진 건 가해자', KsmJcoLeRJU 0.3s '판사가 수표를 꺼냅니다', 3K0uY0x-cus 2.9s 습격 장면).",
     "counter_evidence": "t8EFnyTfgqs는 결과형(정답까지 공개: '그런데 집행유예')인데도 730회(채널 중앙값 815)에 머문다 — 결과형만으로는 부족하고, 정답 전체 공개는 퀴즈 이유를 없앨 수 있다. 질문형 KsmJcoLeRJU(708k, 채널 중앙값의 43배)도 잘 됐다.",
     "change_for_episodes": "#11·#13(A): 헤드라인 1줄째 = 가장 충격적인 사실(숫자 포함, 예: '131m 매달고 질주'), 2줄째 = 모순 신호('그런데 판사가 본 건 따로 있었다' 류), '몇 년 나왔을까?'는 빼고, 첫 대사도 같은 사실로 3초 안에 시작. 제목 = 헤드라인과 같은 문장 + '#형량퀴즈'. #12·#14(B): 지금처럼 질문형 유지(대조군). 나머지 요소는 A/B 동일.",
     "metric_primary": "Shorts 피드 '시청함 vs 넘김' 비율(viewed vs swiped away)",
     "metric_secondary": ["처음 3초 유지율", "평균 시청 비율(% viewed)"],
     "test_design": "2편 vs 2편, 같은 요일·시간 업로드. 사건 소재 차이가 커서 방향성만 본다. 업로드 후 48시간 같은 시점에 비교.",
     "confidence": "중간 — 패턴은 일관되지만 다른 채널 지표는 비공개라 상관관계만 있음."},
    {"id": "H2", "area": "맞히기 질문 위치·정답 공개 타이밍·길이",
     "statement": "보기 카드와 3초 카운트다운으로 영상을 멈추는 대신, 질문을 2초 이하 짧은 비트로 줄이고 '판사가 본 사정' 2–3개를 먼저 보여준 뒤 정답을 런타임 75% 이후에 공개하면 평균 시청 비율이 오른다.",
     "supporting_video_ids": ["4oAtyLyRABA", "Ehjs0mbaaYw", "XSO59xOZ0e8", "EsGemJYqaWE", "-niDfHQhqmE", "3K0uY0x-cus", "-gaDkoZU6mM", "efhcMCRukh4", "ApqOKh_QTxo"],
     "evidence_summary": "관찰한 판결 스토리 14편의 정답 공개는 런타임의 62–94%, 중앙값 약 83%. 보기 카드나 카운트다운으로 멈추는 영상은 하나도 없고, 질문은 정답 직전 2초 이하의 수사적 비트다(4oAtyLyRABA 24.8s '어떤 판결이…?' → 28.2s 정답). 7편은 2단계 공개(1심→2심, 기존 형량→실제)로 끝까지 끌고 간다. 우리 IKjz8gGErMk는 10.2–15.8s 보기+카운트다운 정지 구간(21%), 정답 62%, 이후 3초 정지 엔드카드.",
     "counter_evidence": "퀴즈 동종 rGcRlRrtL1o는 보기를 70% 지점에 두는데도 944회 — 늦은 질문만으로는 부족하다. 길이: 잘 된 영상은 20–59s(중앙값 약 45s)로 폭이 넓고, 구독 대비 조회 비율 1위 Nykfh2I4eBk는 23s라 길이 자체는 강한 변수로 보이지 않음.",
     "change_for_episodes": "4편 모두: (1) 보기 3개는 0프레임부터 헤드라인 아래 얇은 띠로 상시 표시하거나 1.5초 플래시로만 보여주고 카운트다운 삭제. (2) 사건 → '판사가 본 사정' 카드 2–3장(가중/감경, 예: '반성 없음', '합의 실패', '초범') → 정답을 75% 이후 공개 → 2초 안에 종료. (3) 1심→2심 변경이 있는 사건은 2단계 공개로 사용. 길이는 25–35s, 최대 40s.",
     "metric_primary": "평균 시청 비율(% viewed)과 유지율 곡선(10–16s 구간 하락이 사라지는지)",
     "metric_secondary": ["정답 공개 시점까지 남은 시청자 비율", "댓글 수/1천 회(정답 찍기 댓글)"],
     "test_design": "4편 모두 적용하고 #1–#10의 같은 지표와 비교(사전·사후). H1과 섞이지 않도록 4편에 동일 적용.",
     "confidence": "중간."},
    {"id": "H3", "area": "템포·화면 구성",
     "statement": "내레이션 한 구절마다(1.5초 이하) 화면을 바꾸고 죄명·형량·숫자를 큰 스탬프 카드로 보여주면 평균 시청 비율이 오른다.",
     "supporting_video_ids": ["EsGemJYqaWE", "XSO59xOZ0e8", "KsmJcoLeRJU", "-gaDkoZU6mM", "Ehjs0mbaaYw", "2dOUKItDw2c"],
     "evidence_summary": "스토리보드 자동 측정(약 1fps, 하한값) 화면 변화: EsGemJYqaWE 7.3, -gaDkoZU6mM 6.9, KsmJcoLeRJU 6.4, XSO59xOZ0e8 5.3, Ehjs0mbaaYw 5.3회/10s. 우리 IKjz8gGErMk 3.0, 0eo5o8u5EMM 1.9, 부진한 동종 t8EFnyTfgqs 1.9. 일러스트 캐릭터로 성공한 EsGemJYqaWE·XSO59xOZ0e8·2dOUKItDw2c는 구절마다 포즈·장면을 바꾸고 숫자를 카드로 띄운다('5시간 36분', '벌금 10만 원'; Ehjs0mbaaYw '특수손괴/징역 6개월/실형' 스탬프). 20편 중 19편이 2줄 헤드라인을 영상 내내 상단에 고정(우리도 이미 함).",
     "counter_evidence": "Nykfh2I4eBk(0.9회/10s)와 viX9bKBe8Bc(0.4회/10s)는 거의 컷 없이도 잘 됐다 — 실사 블랙박스·토킹헤드처럼 장면 자체에 움직임이 있으면 예외. 자동 측정은 카메라 움직임도 센다.",
     "change_for_episodes": "4편 모두: 캐릭터 포즈·줌·컷어웨이·숫자 카드로 1.5초마다 화면 변화(목표 6회/10s 이상). 죄명·형량·핵심 숫자는 스탬프 카드. 대사는 화자별 색 자막(KsmJcoLeRJU 방식). 3초 정지 엔드카드 삭제. 하단 빈 검정 영역은 자막·보기 띠로 활용.",
     "metric_primary": "평균 시청 비율(% viewed)",
     "metric_secondary": ["시청함 vs 넘김 비율", "유지율 곡선의 중간 이탈 구간"],
     "test_design": "H2와 함께 4편 공통 적용 → #1–#10과 비교. 효과를 H2와 분리하려면 이후 회차에서 따로 검증.",
     "confidence": "중간–낮음."},
    {"id": "H4", "area": "구독·댓글 요청(엔딩)",
     "statement": "'다음 사건도 맞혀 보세요' 3초 엔드카드 대신 판결에 대한 2지선다 의견 질문(👍 적당하다 / 💬 너무 가볍다)을 마지막 1.5초에 넣으면, 조회 수를 해치지 않고 댓글과 1천 회당 구독 증가가 늘어난다.",
     "supporting_video_ids": ["EsGemJYqaWE", "efhcMCRukh4", "-niDfHQhqmE", "-gaDkoZU6mM", "FLcCGqxBMuY"],
     "evidence_summary": "동종 대조군을 뺀 18편 중 12편은 아무 요청 없이 정답 직후 끝난다. 의견 질문은 EsGemJYqaWE(👍/💬 카드), efhcMCRukh4('어떻게 생각하시나요?'), -niDfHQhqmE(동의하면 좋아요), -gaDkoZU6mM('판결이 어떠신가요?')에 있다. 1천 회당 댓글은 0.27–3.52로 엇갈리고, 가장 높은 영상(-niDfHQhqmE 3.52, ApqOKh_QTxo 1.98, XSO59xOZ0e8 1.89)은 논쟁적 판결 소재다. 일반 구독 요청은 FLcCGqxBMuY(6.4M, '구독·알림 + 뒷 이야기는 고정댓글에'), 76soQnhHk58, 그리고 부진한 동종 2편(rGcRlRrtL1o 구독&좋아요, t8EFnyTfgqs 댓글 요청+다음 편 예고)에 있다.",
     "counter_evidence": "다른 채널의 구독 전환율은 공개되지 않아 근거가 가장 약하다. 댓글 수는 소재 영향이 커 엔딩 효과와 분리되지 않는다. 사례 C6(자기 보고)은 운영자 존재감·감사 영상이 구독 전환을 크게 올렸다고 주장 — 검증 불가.",
     "change_for_episodes": "#11·#12: 엔딩 = 의견 2지선다 1.5초 + 고정 댓글에 '다음 사건 예고 + 구독' 안내. #13·#14: 지금 엔딩('다음 사건도 맞혀 보세요') 유지. H1의 A/B와 엇갈리게 배치(#11 A+새 엔딩, #12 B+새 엔딩, #13 A+기존, #14 B+기존).",
     "metric_primary": "1천 회당 구독 증가(subscribers gained per 1k views)",
     "metric_secondary": ["1천 회당 댓글 수", "엔딩 직전·직후 유지율(루프 재생 여부)"],
     "test_design": "편당 1개씩이라 통계적 의미는 없다. 방향만 보고 #15 이후 반복 검증.",
     "confidence": "낮음."},
]

episode_plan = {
    "#11": {"H1": "A 긴장형", "H4": "의견 2지선다 엔딩", "H2_H3": "적용"},
    "#12": {"H1": "B 질문형(대조)", "H4": "의견 2지선다 엔딩", "H2_H3": "적용"},
    "#13": {"H1": "A 긴장형", "H4": "기존 엔딩", "H2_H3": "적용"},
    "#14": {"H1": "B 질문형(대조)", "H4": "기존 엔딩", "H2_H3": "적용"},
    "note": "4편으로는 통계적 결론이 안 나온다. 같은 시간대 업로드, 48시간 시점 같은 지표로 비교하고 방향만 읽는다.",
}

doc = {
    "generated_at": "2026-10-26T16:06+09:00",
    "scope": "몇년나옴 #11–#14 가설용 레퍼런스. 다른 채널의 비공개 지표(유지율·CTR·구독 전환)는 추정하지 않음. 모든 수집 텍스트는 신뢰하지 않는 데이터로 취급.",
    "evidence_level_counts": {
        "videos_observed": len(videos),
        "frames_with_subtitles": sum(1 for v in videos if v["subtitles_available"]),
        "frames_only": sum(1 for v in videos if not v["subtitles_available"]),
        "subtitles_only": 0,
        "metadata_only_screened_not_observed": len(screened)},
    "method": {
        "discovery": "로그아웃 YouTube 검색(Shorts 필터) HTML 파싱 + youtubei 이어받기, 해시태그 Shorts 페이지, oEmbed로 제목·채널 선별",
        "per_video": "yt-dlp --skip-download --dump-json; ko 자동 자막(vtt); 스토리보드 sb0(101×180, 3×3, 약 1fps) 스프라이트; i.ytimg.com frame0.jpg와 썸네일. 영상·음성 파일은 받지 않음.",
        "selection": "인접 형식(판결·법정·법률 썰·퀴즈형 스토리), 구독자 대비 조회수와 채널 최근 쇼츠 중앙값 대비 배수, 최근성. 동종 저성과 2편(t8EFnyTfgqs, rGcRlRrtL1o)은 대조군으로 포함.",
        "tools": "~/.local/bin/yt-dlp 2026.10.21",
        "raw_dir": "~/projects/verdict-kr/work/research/refs/2026-10-26-raw/"},
    "own_baseline": own_baseline,
    "videos": videos,
    "screened_metadata_only": screened,
    "cases": cases,
    "excluded_sources": excluded_sources,
    "search_log": search_log,
    "unreachable": unreachable,
    "hypotheses": hypotheses,
    "episode_plan": episode_plan,
}
json.dump(doc, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print("wrote", OUT, len(videos), "videos", len(screened), "screened", len(search_log), "log entries")
