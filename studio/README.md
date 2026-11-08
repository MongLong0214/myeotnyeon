# studio — 몇년나옴 제작 저장소 (공개본)

비공개 로컬 제작 저장소(`verdict-kr/work`)의 `main` 커밋 `c925280ddc18accef622c3ca4060660e512e0f04`에서
**추적 중이던 파일만** `git archive`로 가져왔다. 커밋되지 않은 작업과 미디어(영상·음성·이미지·모델)는 들어 있지 않다.
`REPO.md`는 비공개 시절의 운영 문서이며 "원격 없음" 문구는 그 당시 기준이다.

## 공개하면서 바꾼 것

- **제외한 제3자 자료.** 뉴스·웹 기사 원문(txt/html), 판결문 원문·법원 포털 캡처, 다른 채널 영상의 자막(vtt)·ASR 전사·설명란·화면 OCR.
  빠진 파일이 있던 폴더마다 `MANIFEST.md`(같은 폴더에 `manifest.json`이 이미 있으면 `MANIFEST_EXCLUDED.md`)가 있고,
  원래 파일명·크기·원본 sha256·원 출처 URL(기록돼 있던 경우만, 추적·서명 쿼리는 제거)을 남겼다.
- **필드 단위 삭제.** `research/format_v4/extol_all/<영상ID>/*.json`의 `description`(다른 채널의 설명란),
  `research/format_v4/ref_extol2/comments_coded.csv`의 댓글 본문·댓글 ID(우리 분류 열만 남김),
  제3자 영상 제목에 있던 사적 개인 실명 1건(`validation_dates/AwNtHOCSCok.json`)을 가렸다.
- **로컬 경로·식별자.** `/Users/<사용자>/projects/verdict-kr/work/`는 저장소 상대 경로로, 그 밖의 홈 경로는 `$HOME/...`로 바꿨다.
  키체인 항목 이름은 `KEYCHAIN_SERVICE_PREFIX.*` 자리표시자로 바꿨다. 쓰려면 자기 키체인 항목 이름으로 바꾼다.
- **compositor 테스트 이름.** `production/compositor/tests/endTransition.test.ts` → `endTransition.spec.ts`.
  저장소 루트의 `npm test`(`node --test`)가 이 파일을 자동으로 찾아 실행하는데, 이 테스트는 compositor 의존성(`remotion`)을 설치해야 돈다.
  compositor 안에서 `npm install && npm run test:end-transition`으로 실행한다.

## 실행 위치

Python 스크립트의 경로는 `studio/`를 기준으로 한 상대 경로다. **`studio/`에서 실행한다.**
`$HOME/.local/bin/yt-dlp`, `$HOME/.cache/...`처럼 남은 경로는 원래 작업 머신의 위치를 적은 자리표시자다.

## 검증

### 단위 테스트 — CI `studio-factory`가 PR마다 실행

```sh
python3 -m venv .venv && .venv/bin/pip install -r factory/requirements-test.txt   # studio/에서. 테스트가 .venv/bin/python 을 직접 부른다
# textgate.py가 쓰는 im-not-ai 지표(MIT)를 고정 커밋으로 받는다
# (다른 위치에 두려면 IM_NOT_AI_DIR 환경변수로 지정)
git clone https://github.com/epoko77-ai/im-not-ai .deps/im-not-ai && git -C .deps/im-not-ai checkout bad4ef0a2b514318b2278b65cb4545414ad84d82
swiftc -O factory/ocr_vision.swift -o factory/.ocr_vision   # macOS Vision OCR 테스트용
cd factory && ../.venv/bin/python -m unittest discover -s tests
```

macOS와 `ffmpeg`가 필요하다. 검토 게이트가 시스템 한글 글꼴(`AppleSDGothicNeo.ttc`)과 Vision OCR을 쓴다.
`.ocr_vision`을 빌드하지 않으면 `test_one_frame_korean_date_outside_subtitles_is_caught` 하나가 건너뛰어진다. CI에서는 빌드하므로 실행된다.
`make.py` 텍스트 단계의 테스트는 `tests/fixtures/archive/`의 합성 헤더 파일(출처 ID·매체·날짜·URL만, 기사 본문 없음)을 원문 보관본 대신 쓴다.

### 통합 테스트 — `factory/tests_integration/`, CI에서 실행하지 않음

```sh
cd factory && ../.venv/bin/python -m unittest discover -s tests_integration
```

아래 제작 산출물이 있는 제작 머신에서만 통과한다. 이 저장소에는 그 산출물이 없으므로 여기서는 실패하는 것이 정상이다.

| 모듈 | 필요한 제작 산출물 |
|---|---|
| `test_make_production.py` (2) | `episodes/quiz/q017/v52/`의 캐시된 렌더(`render*.json`, `audio.json`), `production/compositor/public/hook_v51/q017.png` |
| `test_make_long.py` (9) | git 밖의 N18 v4 롱폼 빌드 `production/lf_toon/` (`build_audio.wav` 포함) |
| `test_review_gates_n18.py` (2) | `production/lf_toon/v2/n18/{fact_trace.md,shots_v2.json}`, `factory/review_runs/n18_v2_1080p_001/frames/*.jpg` |
| `test_signoff_sources.py` (2) | 납품 패키지 `upload/pkg/q013_n16_v4/`(영상·표지·히어로 이미지)와 그 claim이 가리키는 기사 보관본 |
| `test_visual_gates.py` (10) | N18 최종 인코딩 프레임 `factory/tests/fixtures/n18_ceo_fix2.json` |

미디어가 있어야 하는 그 밖의 경로(렌더 `production/compositor`·`episodes/*` 빌드, TTS `tts`·`tts_lab`, 레퍼런스 측정 `research/format_v4/*`의 영상 분석, 업로드 `upload/`)도 이 저장소만으로는 실행되지 않는다.
