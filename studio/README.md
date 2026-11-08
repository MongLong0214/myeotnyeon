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

```sh
cd studio/factory
python3 -m venv ../.venv && ../.venv/bin/pip install pillow numpy   # 테스트가 ../.venv/bin/python 을 직접 부른다
../.venv/bin/python -m unittest discover -s tests
```

`c925280`의 추적 파일만으로는 47개 중 29개가 통과한다(가져오기 전 원본 추출본과 같은 결과다). 나머지 18개는 이 저장소에 없는 입력 때문에 실패한다.

| 실패 테스트 | 없는 입력 |
|---|---|
| `test_number_gate`, `test_review_gates`, `test_signoff_sources`, `test_visual_gates` (import 실패) | `qa` 모듈 — 렌더 출력 폴더 `episodes/quiz/out/v3/`에 있던 파일로, 커밋된 적이 없다 |
| `test_make.MakeCLI.*` 9개 | `facts` 단계가 요구하는 기사 원문 `research/raw*/<sid>.txt`(예: `N17_1.txt`). 원본에서도 커밋되지 않았고, 공개본에서는 제3자 기사라 어차피 뺀다 |
| `test_make_long.LongForm.*` 6개 | `build` 단계에서 실패한다. 롱폼 빌드는 git 밖의 `production/lf_toon/`과 미디어를 쓴다 |
| `test_make_long.LongForm.test_write_through_copy_cannot_reach_original` | `production/lf_toon/` (원본에서도 git 밖에서 관리) |
| `test_cas_adoption.FrameTests.test_advisory_survives_calibration_and_decode_errors` | 프레임 이미지 입력 |

미디어가 있어야 하는 경로(렌더 `production/compositor`·`episodes/*` 빌드, TTS `tts`·`tts_lab`, 레퍼런스 측정 `research/format_v4/*`의 영상 분석, 업로드 `upload/`)는
영상·음성·모델 가중치·폰트 바이너리가 없어서 이 저장소만으로는 실행되지 않는다. 그 스크립트들은 기록과 재현 근거로 남겨 둔 것이다.
