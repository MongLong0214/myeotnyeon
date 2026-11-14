# cinecode 분석 보고서 (2026-11-08)

- 대상: https://github.com/sarpstar/cinecode, 커밋 `67f9807`(2026-11-03), 클론 위치 `src/`
- 범위: 168개 파일, 약 31,000줄. 정독: SKILL, references 전체, `templates/quick/film.html`(카메라·모션·캐릭터·자막), `qc.py`, `scene_check.py`, `moves.py`, `captions.py`, `validate_shots.py`, `voice_treat.py`, `mix.py`, `make.py` 게이트, 카툰 계열 스타일 문서. 나머지는 설명문과 핵심 함수만.
- 실행: `scene_check.py repeats`, `action`을 LF2 v3 렌더에 돌림(`demo/`). 우리 코드 무수정, 커밋·푸시·전역 설치 없음.
- (서브에이전트 파일 쓰기가 막혀 CTO가 보고 원문을 저장함)

## 1. 정체
Claude Code/Cursor용 "코드로 영화 만들기" 스킬 키트. 장면마다 시간 t의 순수 함수인 HTML(Canvas 2D/three.js)을 헤드리스 Chrome으로 캡처 → ffmpeg MP4 → Web Audio 사운드 −14 LUFS 마스터링. Quick mode는 `film.html` 한 파일(1,698줄)에 타임라인·2.5D 카메라·전환·캐릭터 리그·자막·사운드. 가치의 대부분은 규칙 문서와 측정 스크립트. 엔진이 Remotion과 달라 함수·아이디어 단위로만 옮긴다.

## 2. 라이선스
| 대상 | 라이선스 | 우리 사용 |
|---|---|---|
| 저장소 전체 | MIT © 2026 Sarp Yıldız | 상업 사용 가능. 옮긴 파일 머리에 `Portions adapted from cinecode (MIT)` + MIT 본문 |
| `styles/` 다수 | MIT © 2026 LemoLab | 같음 |
| Kenney 효과음, VCSL/VSCO2 샘플 | CC0 | 표기 의무 없음 |
| FilmGrab 스틸 | 저작권 | 무드 참고만, 영상 사용 금지 |

## 3. 재사용 후보 (S = 반나절 이하, M = 1–3일)
| # | 무엇 | 파일 | 연결 문제 | 노력 |
|---|---|---|---|---|
| 1 | 반복 구도·정지·1프레임 튐 검출 | `scene_check.py` | 정적·반복 화면 | S |
| 2 | 러버호스 팔·다리(2차 베지어, 외곽선 먼저) | `film.html` `characterLimb` | 어색한 팔(직선 2개) | S–M |
| 3 | 몸 연기 포함 감정 테이블 | `EMOTIONS`, `actionPose` | 약한 코믹 연기 | S |
| 4 | 모델 시트 | `modelSheet`, `characters.md` | 결함 사전 확인 | S |
| 5 | 모션 함수 + 수치 규칙 | `motion.md`, `MOTION` | 뻣뻣함·타이밍 | S |
| 6 | 카메라 handheld/path/follow/retime/whip/iris/matchFrom | `film.html` 271–443, `camera-moves.md` | 카메라 워크 | S–M |
| 7 | 2.5D 깊이 평면 패럴랙스 | `plane()` | 평면 배경 | M |
| 8 | 카메라 덱 추첨 + 리듬 검사 | `moves.py`, `validate_shots.py` | 반복 샷·단조 리듬 | S |
| 9 | 성인 SF 시트콤 툰 문법 | `styles/scifi-toon.md` | 톤 | S/M |
| 10 | 오디오 립싱크(RMS+스펙트럼 중심) | `scifi-toon.md` §5 | 단순 입 | M |
| 11 | 자막 그룹 분할·균형 줄바꿈·유지 시간 | `captions.py`, `wrap()`, `craft.md` §5 | 자막 분할 | S |
| 12 | 효과음 피크 동기 규칙 | `sound.md` | 소리 타이밍 | S |
| 13 | Kenney CC0 효과음 + 우드블록·슬랩스틱 | `sounds.py`, `samples.py` | 무료 폴리 | S |
| 14 | TTS 정리 ffmpeg 체인 | `voice_treat.py` 27–60 | TTS 날것 소리 | S |
| 15 | 장면별 음량 검사 | `scene_check.py sound` | 음량 튐 | S |
| 16 | 레퍼런스 형식 측정 | `ref_video.py` | 프레임 실측 | S |
| 17 | 롱폼 호기심 지도·60–90초 반전·템포 태그 | `writing.md` §13–15 | 지루한 롱폼 | S |
| 18 | 훅 검사(0–2초 움직임) | `qc.py hook` | 숏츠 첫 2초 | S |

## 4. 실측 (LF2 v3, 432초)
- `repeats` 기본(mad<5): 14회 18초. `--repeat-mad 10`: 37회 65초(15%).
- `action`(앞 90초, 3초 창): 기본 1.0으로 1창만. 2.5면 서서 말만 하는 창 5개 검출(한 편 추정치).

## 5. 바로 가져다 쓸 것
- **P1 (S)** `scene_check.py`를 `lf_toon/tools/`에 복사. `repeats <mp4> --repeat-mad 10`, `action <mp4> --scenes <컷 경계> --fps 2 --min 2.5`, `pops <mp4>`. 기준 제안: 반복 ≤5%(콜백 예외), 정지 창 ≤15%, pops 0 — 기존 판정 2–3편으로 보정.
- **P2 (S–M)** 팔을 한 경로로: 외곽선 path(Q 곡선, round) 위에 같은 경로로 소매색; 소매·피부 경계는 같은 곡선에 strokeDasharray; 손은 끝점 접선 방향 회전, 크기를 키에 묶음.
- **P3 (S)** 표정에 tilt/어깨/lean/bounce/땀·눈물·홍조 추가(`EMOTIONS` 657–674 출발점), 모델 시트 스틸로 장면 전 확인.
- **P4 (S)** anticipate/back/spring/arc(약 25줄). 규칙: 준비 동작 반대 방향 10–20%·3–5프레임; 부속물 1–4프레임 늦게 출발·2–5프레임 늦게 정지; 원인→반응 2–4프레임; 오버슈트 15–25%(가장 큰 탄성 한 편 1회); 착지 후 4–6프레임 홀드, 리액션 0.5–1초 홀드.
- **P5 (S–M)** 카메라: handheld(0.3–1.1 Hz 저역 노이즈), path(Hermite), follow(lag 0.35), retime(freeze/ramp), whip(0.2–0.35초). 리듬 cv≥0.30, 같은 길이 5연속 금지.
- **P6 (S)** 자막: `textWrap: 'balance'` + `keep-all`; whisper 단어 시간 기준 0.25초 쉼·구두점·16–18자/줄·2줄 이하; 유지 `max(1.8s, 발화+0.6s)`; 펀치라인 전 지우기; 마지막 줄 한 어절이면 앞 줄 어절 하나 내림.
- **P7 (S)** 효과음 피크를 접촉 프레임에, whoosh 피크는 컷 2–3프레임 전. 펀치라인에서 음악·리버브 끊기, 클라이맥스 0.3–0.5초 전 침묵. Kenney CC0 내려받기만. TTS CLEAN 체인, 장면 간 ±3 LU.
- **P8 (S)** BIBLE: 첫 30–60초 질문 심기, 호기심 지도, 60–90초마다 반전, 10–15초마다 사건, 키 모먼트 읽는 시간+1.5초 정지.

## 6. 쓰지 않을 것
유료 클라우드 TTS(`tts.py`, `keys.py`), three.js/3D(3D 금지), 엔진 통째(`film.html`, `capture.mjs`, `make.py` 등 — Remotion과 중복), 세션 운영 게이트(`guard.py`, `hook.cjs` 등 — 과설계), 룩 선택 도구·FilmGrab(포맷 고정·저작권), 터키어 전용 폰트·금칙어 도구, 실사·뮤직비디오용 도구, Pixabay(API 키).

## 7. 한계
대형 운영 파일은 관련 부분만 정독. 실측 한 편, action은 앞 90초만; 임계값은 제안값. 영상은 시청하지 않음. cinecode 손은 장갑형이라 손 모양이 아니라 팔 곡선 방식만 가져옴.
