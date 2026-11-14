# 채널 팩 공장 — 감사와 설계 (2026-11-08, 1차)

기존 규칙은 그대로 둔다: 게이트·서명 [README.md](README.md), 불합격 조건 [REVIEW_CHECKLIST.md](REVIEW_CHECKLIST.md), 업로드 [upload_precheck.md](upload_precheck.md).
이 문서는 채널 팩과 `make.py`만 다룬다. 공개 레포 MongLong0214/myeotnyeon의 `factory/discover`(JS, 소재 열기 수집)는 소재 단계의 다른 구현이다. 소재 단계의 기준은 지금도 `research/topic_scores/RANKED.md`다.

## 1. 감사 (오늘 기준)

| 단계 | 자동 | 수동·임시 | 몇년나옴 하드코딩 |
|---|---|---|---|
| 소재 | `topic_score.py`, `topic_gap.py` → RANKED.md | 채택은 CTO 판단(A1) | 판결 퀴즈 전제 |
| 사실(출처 2곳 이상) | 원문 스냅샷 해시, 출처 수 (`gates.fact_gate`) | 의미 대조는 CTO 서명 | 레드라인 정규식 `gates.redline_gate` |
| 대본 | 숏츠는 `episodes_n16.py` 명세 | 롱폼은 빌드마다 `script_*.md`를 손으로 씀 | 묻는 문구 '몇 년 받았을까?', 선택지 `CHOICES`, 아웃트로 |
| 스토리보드 | 숏츠는 명세의 cue/set | 롱폼은 빌드마다 TSX(Scenes, Film) | — |
| TTS(로컬) | `fresh.py`, `prepare_v52.py`(Supertonic) | 롱폼은 빌드마다 `synth.py` | 음성 M1, 속도 7.5음절/초(숏츠)·6.2–6.6(롱폼), 메타 고지 문구 |
| 렌더 | `render.cjs` + compositor v52 | 롱폼은 빌드마다 `render.cjs`·`finalize.sh` | 자막 70px/800/외곽선 12(`Quiz.tsx`), 줄당 14·18자 |
| QA 게이트 | `gates.py` + `review_gates.py` A1–H16, `captions.py` | 서명 항목 | 제목 접미 `#몇년나옴`(`title_gate`), 숏츠 22–40초 |
| CTO·CEO·원일 검수 | 서명은 `input_sha256`에 묶음 | CEO 시각 검수와 원일 시청은 운영 절차 | — |
| 업로드 패키지 | `short.py`가 `upload/pkg/`에 씀 | 롱폼은 손으로 | 번호·원장 `upload/ledger.json` |
| 업로드·리드백 | 없음 | `upload_one.sh`(Aside) 뒤 사람이 원장 기록 | Studio 채널 확인, 하루 1개 |

빈 곳: 롱폼은 공통 경로가 없고 빌드마다 스크립트를 복사한다. 단계 상태와 재실행 규칙이 없다. q014: not rebuildable: required input hook_v51/q014.png missing (`episodes/quiz/v52_q013_q014_support/bundle_v52_revised/public/`, 11-06 정리). 대체 입력 없음.
q017 시험 빌드(`out/factory/myeotnyeon/q017_factory`): 자동 게이트 FAIL 2건(`no_empty_panel` C2 28프레임, `E2` 폭력 비트 미매핑)을 그대로 둔다. 내용·게이트 수정 없음.

## 2. 설계

- **채널 팩** `channels/<id>/channel.json`: identity, language, sources(명세 레지스트리·원문 보관소), voice, art(엔진·리그 프리셋·스타일 바이블), subtitle(short/long 줄 규칙), templates(제목·설명·고정 댓글), formats(short/long, 퀴즈 규격), facts(최소 출처 수), red_lines, checklist(채널에 적용할 H 규칙), upload(주기·원장·사전 점검), review(검수 순서). 에셋 경로도 팩에 둔다.
- **에피소드 명세** `channels/<id>/episodes/<eid>.json`: `channel`, `id`, `format`, 입력(`registry`+`source_id` 또는 롱폼 `build_dir`·`script`·`storyboard`·`facts`·`commands`), `number`, `dry_number`.
- **CLI** `factory/make.py --channel <id> --episode <spec> --stage <name|all> [--out] [--dry-run]`. `--channel`은 필수이고 기본값이 없다.
  - 숏츠 단계: spec → facts → script → storyboard → tts → captions → meta → render → gates → review → package → upload.
  - 롱폼: inputs → facts → tts → captions → render → deliver → gates(manual) → review(manual) → upload(manual). 보존된 빌드 하나(N18 v4, 명세 `channels/myeotnyeon/episodes/n18_v4.json`)를 `out/factory/<channel>/<eid>/root/<build>`에 복사해, 빌드의 스크립트를 고치지 않고 그대로 돌린다. 엔진(compositor node_modules·src/v4, lf_toon/src), factory/lib, 데이터도 APFS 클론으로 복사하고 링크는 쓰지 않는다(`offline.cjs`의 설치 경로만 복사본에서 바꾼다). 단계마다 원본 빌드(내용 해시)와 lf_toon/src·compositor·factory(stat)를 앞뒤로 대조한다. 바뀌면 그 단계는 실패한다. never_touch 빌드의 변화는 "foreign changes during run" 경고로만 남긴다. 원본 렌더 뒤 수정된 입력은 "inputs differ from delivered original"로 경고한다. 렌더 자식은 별도 프로세스 그룹으로 돌리고 그 PID를 잠금에 기록한다. N18 v4에는 합성 단계가 없다(v2 M1 내레이션을 재사용). 그래서 tts는 그 트랙을 추출하고 입력 해시로 캐시한다.
- **멱등성**: 산출물은 정확히 `out/factory/<channel>/<eid>/`에만 쓴다(다른 `--out`과 심볼릭 링크는 거부). `run.json`에 이 에피소드 실행이 만든 파일 목록을 남기고, 목록에 없는 파일이 있으면 거부한다. 단계마다 `stages/<stage>.json`(입력 해시, 산출물 sha256)을 남긴다. 입력 해시는 해당 팩 키, 명세, 앞 단계 산출물, 실제 입력 파일(원문, v52 캐시, compositor 소스, 공용 에셋), make.py 자신의 해시로 만든다. 그래서 음성을 바꾸면 tts부터, 자막 규칙을 바꾸면 script·captions부터 다시 돈다. 낡거나 일부만 만들어진 산출물은 `superseded/`로 옮기고 지우지 않는다. 실패나 `running`으로 남은 기록은 완료로 치지 않는다.
- **잘못된 대상 거부**: 번호 없는 원장 기록은 qid당 하나만, `<qid>_std/meta.txt`에 "번호 미배정"으로 시작하는 줄이 있는 게시·예약본일 때 통과한다. `no`가 null이거나 정수가 아니면 FAIL이다. 명세 채널 ≠ `--channel`이면 거부한다. 다른 채널·에피소드가 이미 쓴 출력 폴더, `upload/`·`episodes/`·`production/` 아래 출력, 캐시 음성 ≠ 채널 음성도 거부한다. `.lock`으로 한 에피소드에 쓰는 프로세스를 하나로 제한한다. 죽은 PID의 잠금은 보고만 하고, `--break-stale-lock`을 줄 때만 푼다.
- **사람 경계** (`manual` = 다음 담당자와 필요한 입력을 적은 대기 상태. 완료가 아니다):
  - 사실 서명: CTO → `signoffs/facts.json`
  - 게이트 서명: CTO → `signoffs/cto.json`. 형식은 기존 `cto_signoffs`와 같다.
  - CEO 시각 검수 → `signoffs/ceo.json`
  - 원일 시청 → `signoffs/owner.json`
  - 서명은 모두 해시에 묶인다. 업로드는 서명이 다 있어도 항상 `manual`이다. make.py는 업로드하지 않는다.
- **채널 추가**: `channels/myeotnyeon/channel.json`을 `channels/<id>/`로 복사해 id와 모든 값을 바꾼다(`_template`은 잘못된 대상 거부 시험용 자리표시). 에피소드 명세 하나를 `number: 99, dry_number: true`로 만들어 `--stage all`을 돌린다. 숏츠 엔진(compositor)과 롱폼 리그는 아직 채널 팩을 읽지 않는다. 다른 그림체나 자막 크기가 필요하면 그 채널의 엔진 프리셋을 따로 만들어야 한다(다음 단계).
