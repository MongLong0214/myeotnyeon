# Repository migration audit — 운영 코드와 myeotnyeon의 대조

2026-11-06 KST 작성. [REPO_ARCHITECTURE_PLAN.md](REPO_ARCHITECTURE_PLAN.md)의 사실 확인 부록이다. 이 문서의 감사 결과를 우선하여 기존 계획의 상태 표현을 읽는다.

- `W = /Users/isaac/projects/verdict-kr/work`, `R = /Users/isaac/projects/myeotnyeon`.
- W: `main@8f31ce88ec6d952171f2897b9e75f5c151b5776f`, 커밋 5개, 원격 없음. **디스크의 수정·미추적 운영 코드도 별도로 포함**했다.
- R: 현재 `task/task74ba7b2e7f604d90b8071a87-r12-factory-lib-robots-rfc-9309@08f3d461`; `dev`, `origin/dev`, `origin/main`은 `647aa171fffa4f6a9cd6c7ae33feb5f7086f71b5`. 로컬 `main` 브랜치는 없다. 원격 ref는 fetch 없이 읽은 로컬 스냅샷이다.
- ACP DB는 `sqlite3.connect('file:…/state.sqlite?mode=ro', uri=True)`로 읽었다. run 생성·취소, push, merge, 운영 코드 수정·이동·삭제는 하지 않았다. 테스트용 detached worktree만 scratch에 만들고 제거했다. 문서 두 곳 외 기존 파일은 수정하지 않았다.
- 이 문서는 **내부 감사용**이다. 요청에 따라 로컬 경로·Keychain 서비스 이름을 포함한다. 공개 저장소로 그대로 이관할 자료가 아니다. 비밀 값·토큰·계정 이메일·브라우저 프로필 ID는 수집하거나 기록하지 않았다.

## 1. Run A: 공식 상태, 후보, 계약, 검토 결과

### 1.1 확인된 원본

| 항목 | 확인 결과와 근거 |
|---|---|
| Run ID | `run_b86c2fe61ad8402a963074f5` |
| **공식 run 상태** | **ACTIVE**. `~/.agent-control-plane/state.sqlite`, `runs.state`. CEO 추가 지시와 일치. `ended_at = null`; review BLOCK과 다른 필드다. |
| Goal | `implement-product A: 검증된 제작 엔진을 허용 목록으로 이관하고 공개 안전 검사를 현 계약에 연결한다.` 현재 운영 코드 이관과 **목표 수준에서 겹친다**. |
| Task contract | `art_b8e5d31e936e4e1a88a5454d`, digest `sha256:1de3aed8026b347a3c424718623b0baec62bed8970990b455db5759c4a491207` |
| 고정 project manifest | `sha256:a8ede69800a77ff8135d3b0e77fa6a1255870507082a50d1f67a081ba7e83f3e`. DB `manifests.content_json`과 R의 `.agent-control-plane/project.json`을 비교: 내용 일치. W의 해당 파일은 **MISSING**. |
| 현재 후보 snapshot | `sha256:c2d0460d2f1e151b1bd75586adb0847865f367347cf18b0e7a2bbf9283a02df9`. **c2d0460d는 Git 커밋이 아니라 snapshot digest 접두사**다. |
| 후보 exact Git HEAD | `f975ad3d0adf0ab11d6e555db7fefd9d6b06c30f`; base `647aa171`. R에는 해당 객체가 없지만 아래 ACP worker checkout에서는 `git show` 가능했다. |
| 실제 ACP 등록 checkout | `/Users/isaac/projects/.acp-worker-checkouts/repo_755987169228449a9c6b7fb2` (`repositories.checkout_path`). R의 20개 브랜치와 Run A 후보를 혼동하면 안 된다. |
| 최신 **blind review** | **BLOCK, 42 findings**. `art_f33abbd3a2d547bd8300fb4e`, 2026-11-01T09:40:01.238Z 저장, `superseded=0`, 후보 c2d0460d. digest `sha256:0f80740aad1fa66220092f79c8d75b338e0c551cf6ef07771c948226d2c07df9`. 원문 findings 배열 접근 성공. |
| 별도 명령 **verification** | **PASS**. `art_9b64907cfa7b4fa68ca03087`, 2026-11-01T08:32:40.779Z, 같은 후보·contract·exact HEAD. `npm test`: 123 PASS, 실패/skip 0, exit 0. 따라서 “verification 자체가 BLOCK 42”라는 표현은 부정확하다. |
| 이번 로컬 재실행 | worker repo에서 f975ad3d의 detached worktree를 scratch에 생성하여 `npm test`: **123/123 PASS**, skip 0, exit 0. 기존 공식 검토 결과를 대체하거나 해제하는 증거는 아니다. |

현재 project contract는 `dev` integration / `main` release, rebase-before-review, merge commit, semver다. 모든 profile의 필수 명령은 **루트 `npm test` 하나**, network deny, timeout 1200초, memory 4096 MB다. `postMergeCommands=[]`, CommitLore preferred. 승인된 workflow는 `.github/workflows/project-ci.yml`, `project-ci`, digest `sha256:b25d3fa557bab83648ddc4dde3ed04ad0bf4988ceb413f773828db7780720408`이다. 실제 workflow는 Ubuntu의 Node 20/22에서 `npm test`와 `node --check index.js`를 실행한다. **현재 계약에 pytest·tsc·vitest가 이미 등록되어 있다는 근거는 없다.**

PLAN submission 2 (`art_e58cb587e8e043078908eb65`)는 CEO의 폰트 처리 결정을 “바이너리를 커밋하지 않고 commit-pinned 공식 URL에서 받아 SHA256 확인”으로 기록한다. 이는 원래 OFL 허용 목록과 구분해 볼 실행 계획 근거이며, 이번 감사는 폰트를 설치하거나 해당 결정을 새로 승인하지 않았다.

DB HANDOFF의 `bodyBase64`를 디코드해 첨부의 본문을 읽었다: `01–04` §5 허용/제외/redact, `05-handoff-s6-verification.md`, `06-handoff-s7-design-tickets.md`, `07-ticket-T1.md`, `10-handoff-s5-allowlist-rows.md`. 일부 발췌는 확보했으나, 원래 handoff 전문·design draft 전문·모든 이관 파일의 원본 비교 자료는 **MISSING/불완전**이다. 첨부 스스로 excerpt라고 밝힌다. 로컬 운영 원본을 읽을 수 있다는 사실만으로 당시 전체 비교가 완료됐다고 소급 판단하지 않는다.

### 1.2 실제 acceptance와 현 운영 코드: 유지/제외 및 현 계약 내 보정

**판단: Run A를 취소하거나 재계약해야 한다고 선결하지 않는다.** 원래 허용 목록의 엔진 이관, public-safe 결함 보정, 정확한 후보의 검증 증거 보충은 현 계약 내 보정 대상이다. 반면 목표의 유사성만으로 새 `factory/*`, `channel/analytics/*`, `production/lf_toon/*` 전체를 기존 §5 파일 허용 목록에 포함시킬 수는 없다. 이 추가 범위는 필요한 의존성이라는 근거 또는 별도 범위 변경이 있어야 한다. 현재 감사에서는 그 변경을 실행하거나 승인된 것으로 간주하지 않는다.

| 기존 task acceptance | 현 운영에서 필요한 부분 | 유지 / 제외 판단 | 현 계약 안에서 할 수 있는 보정 |
|---|---|---|---|
| ① T1 acceptance를 구체 테스트에 매핑, V1 py_compile·V2 episode 위반 0·현 npm PASS를 exact HEAD에 결합 | Python 실행 가능성, episode 입력 의미 보존, 실제 사용하는 renderer의 출력 검증 | **유지**. 구형 q001–q010만의 성공을 현재 q013/q014·롱폼 전체 동등성으로 일반화하는 것은 제외 | 기존 npm test에서 실행되는 제품 테스트로 누락된 검증을 구현/연결. candidate에 이미 V1/V2 실행 테스트가 있다. V3–V6는 “후속”이라고 써서 면제할 수 없음 |
| ② 기사 원문·음원·mp3/wav·계정 정보 공개 0, §5 허용 목록·redact 3건 독립 검토, audio 코드/미디어 구분 | 현재도 필수. W에는 기사 보관본·미디어·업로드 계정 runbook이 함께 있음 | **유지**. W 전체 복사 및 기존 계획의 무차별 text-only 이관은 제외. 명시적으로 허용된 brand PNG/OFL font 취급은 “모든 바이너리 금지”와 구분 | 실제 publish 대상 Git blob/링크 target까지 검사하고 원본-이관본의 허용 변경을 비교. 원문·개인 정보는 비공개 비교에만 사용 |
| ③ 공백 경로·검사기 자기 검사·OS 중립 홈 경로·정상 대형 파일 반례, 기존 test 약화 금지 | 현 코드도 절대경로·로컬 데이터가 많아 그대로 필요 | **유지**. 임의 2 MiB 상한·파일명 면제·검사 생략은 제외 | 기존 checker/test 수정은 허용된 결함 보정. 최신 review가 지적한 symlink target 누락도 같은 범위. 크기 기준으로 안전을 대체하지 않음 |
| ④ 개인 로컬경로·세션·환경정보 공개 제외, 필요한 test/CI·독립 검토 후 PR, merge/readback 또는 승인 차단을 정직하게 보고 | 현재도 필수. 소스의 경로 설정과 개인 운영 기록 분리 필요 | **유지**. 공개 문서에 실제 Aside session/프로필/이메일을 남기는 것 제외. 이번 감사에서 PR·merge 실행은 요청 범위 밖 | 기존 workflow·manifest를 바꾸지 않고 가능한 검증부터 추가. CI에서 증명할 수 없는 설치/렌더 조건은 구체적으로 남기며 성공/완료로 보고하지 않음 |

`nonGoals`는 탐색·게시·학습 신규 구현, CI workflow/active manifest 변경, 원본·대화 삭제/채널 조작/비밀 공개, default branch direct/force push다. 이 경계를 그대로 유지한다. 20개 branch의 discover/cluster/score/facts 신기능을 Run A 보정에 합치는 것은 피한다.

| T1 제품 검증 | 현재 요구/근거 | 현 운영 적용 및 이번 감사 결과 |
|---|---|---|
| V1 syntax | allowlisted pipeline Python `py_compile` | 필요. 후보 `test/pipeline.test.mjs`가 실제 Python 파일 전부와 episode checker를 compile함. 역사적/이번 npm PASS에 포함 |
| V2 episode contract | 3 choices, answer 0..2, scene registry, narration/split 일치, source IDs | 필요. 후보가 `scripts/check_episodes.py`를 실행함. 현재 `episodes_n16.py`·신규 포맷까지 증명한 것은 아님 |
| V3 typecheck | `tsc --noEmit` | renderer 이관에서 필요. 최신 review에서 candidate-bound 실행 증거 누락. 이번 감사에서는 실행하지 않음 |
| V4 compositions | Remotion compositions; EP001/S001 및 THUMB/PEEPTEST 차단 | 필요. 현 W `Root.tsx`에는 EP001/S001·q001–q017·v4 등록이 있어 허용 목록과 그대로 같지 않음. 새 toon entry는 별도 |
| V5 still | COVER 전부 + CH-ICON | 해당 compositor 이관에 유지. 구형 COVER가 없는 첫 caption 함수 단위에는 적용 대상이 아님. 이를 Run A 전체에서 삭제한 것으로 취급하지 않음 |
| V6 mobile safe area | AUDIT render, 모든 `n=0`, mix_master.wav 없이 동작 | 해당 compositor에 유지. `--muted`만으로 audio fetch가 사라지지 않으므로 AUDIT audio=null 필요. npm 단위 테스트 PASS만으로 실제 렌더 성공을 주장할 수 없음 |

**제외할 것은 오래된 작업 방식이지 acceptance 증거가 아니다.** 구형 제작 폴더가 더 이상 운영 기준이라는 가정, 이미 취소된 다른 run을 다시 실행해야 한다는 가정, “42건을 모두 별도 티켓/새 gate로 만든 뒤 시작”하는 절차는 도입하지 않는다. V3–V6의 CI 실행에 필요한 compositor 설치·폰트·브라우저가 기존 workflow에서 준비되지 않는 제약은 사실이다. test 내부에서 승인된 offline 실행 경로를 만들 수 있는지 먼저 확인하고, 불가능한 요구만 특정해 범위/계약 판단을 받는 순서다. `npm test` 안에서 인터넷 설치를 몰래 시도하거나 CI workflow를 수정하여 기존 계약이 충족됐다고 주장하지 않는다.

### 1.3 원본 42 findings의 위치와 처리 의미

원문 배열의 **1부터 시작하는 순번**이다(원문에 finding ID 없음). 31 MAJOR / 6 MINOR / 5 INFO. 중복된 reduction 결과도 원문 순번을 보존했다. 42개가 모두 서로 다른 버그라는 뜻은 아니다. 아래는 원본 summary의 요약이며, 원문 detail은 위 artifact에서 확인할 수 있다.

| # | 등급 | 원본 path | 요지 |
|---|---|---|---|
| 1 | MAJOR | `compositor/package-lock.json` | Reproducibility of the compositor dependency tree remains unverified |
| 2 | MAJOR | — | Required T1 verification coverage remains incomplete |
| 3 | MAJOR | — | Referenced acceptance and the CI restriction require an explicit contract resolution |
| 4 | MAJOR | — | Independent migration and public-safety acceptance remain unestablished |
| 5 | MAJOR | — | Exact-head npm success does not establish the remaining acceptance checks |
| 6 | MAJOR | — | Compositor acceptance remains unresolved despite the exact-HEAD npm test PASS. |
| 7 | MAJOR | `compositor/src/Quiz.tsx` | T1 rendering acceptance remains unresolved |
| 8 | MAJOR | `compositor/src/SafeAudit.tsx` | Audit measurements can precede final font layout |
| 9 | MAJOR | — | Rendering acceptance remains unproven at the candidate HEAD |
| 10 | MAJOR | — | The npm test PASS does not establish complete T1 acceptance. |
| 11 | MAJOR | — | Required compositor verification remains unresolved |
| 12 | MAJOR | `compositor/src/type2/QuizType2.tsx` | The Type2 adapter lacks established allowlist provenance |
| 13 | MAJOR | `compositor/src/type2/Type.tsx` | The additional type2 scene suite lacks established allowlist coverage. |
| 14 | MAJOR | `docs/OPERATIONS.md` | The required document redactions cannot be independently verified. |
| 15 | MAJOR | — | T1 typecheck and rendering acceptance remains unexecuted. |
| 16 | MAJOR | `pipeline/audio/synth.py` | Preservation of the migrated audio engine remains unverified |
| 17 | MAJOR | `pipeline/make.py` | Persistent ASR failures do not stop the build. |
| 18 | MAJOR | — | The T1 verification deferral leaves an acceptance conflict unresolved. |
| 19 | MAJOR | — | Required T1 verification remains unresolved |
| 20 | INFO | `research/agent1_case.jsonl` | The attached allowlist resolves inclusion of these research indexes. |
| 21 | MINOR | `research/agent2_law.jsonl` | Matching endpoint editions does not establish an unchanged intervening history. |
| 22 | MINOR | `research/agent2_law.jsonl` | A2-112 gives an incident year inconsistent with the summary. |
| 23 | INFO | `research/agent2_summary.md` | The attachment resolves inclusion of the existing research index. |
| 24 | MAJOR | `research/agent3_comparables.jsonl` | Source preservation remains unverified for the shown research import. |
| 25 | MAJOR | — | Independent source-preservation verification remains incomplete for these imports. |
| 26 | INFO | `research/sources_all.csv` | Attached evidence resolves the research-index scope interpretation. |
| 27 | INFO | `research/sources_all.csv` | Attributed evidence supports inclusion within the existing scope. |
| 28 | INFO | `research/viral_candidates.json` | The displayed index records fit the existing migration scope. |
| 29 | MAJOR | `scripts/check-public-safe.mjs` | Symlinks can publish personal home paths without a violation |
| 30 | MINOR | `test/audio-policy.test.mjs` | The Root test forbids a correct implementation of the requested behavior |
| 31 | MAJOR | — | The stated T1 deferral leaves an unresolved acceptance conflict |
| 32 | MAJOR | `test/pipeline.test.mjs` | The proposed V3–V6 deferral leaves T1 acceptance unresolved. |
| 33 | MAJOR | — | The required independent migration comparison remains unsupported. |
| 34 | MAJOR | `#verification-output/test/stdout` | The npm PASS does not establish the remaining T1 gates. |
| 35 | MAJOR | — | Required T1 execution remains incomplete. |
| 36 | MAJOR | — | Independent public-safety and redaction acceptance remains unsupported. |
| 37 | MAJOR | `compositor/src/type2/Type.tsx` | Authorization for the additional Type2 suite remains unresolved. |
| 38 | MAJOR | `scripts/check-public-safe.mjs` | The scanner can miss personal paths published as symlink targets. |
| 39 | MAJOR | `pipeline/make.py` | Persistent ASR failures can leave the build successful. |
| 40 | MINOR | `research/agent2_law.jsonl` | Matching endpoint editions does not establish intervening continuity. |
| 41 | MINOR | `research/agent2_law.jsonl` | The research index conflicts with its summary on the incident year. |
| 42 | MINOR | `test/audio-policy.test.mjs` | Source-spelling assertions reject valid AUDIT implementations. |

보정 묶음은 ① V3–V6/설치/원본 비교/전체 tracked-tree 증거 부족, ② Type2 허용 범위 근거, ③ font readiness·ASR 재시도 실패·symlink 검사·audio 테스트의 실제 결함, ④ 연구 인덱스의 연도/서술 모순이다. INFO 20/23/26/27/28은 허용 범위가 확인됐다는 기록이다. 8번 font race는 원본 review의 `omittedItems`에 주변 font-readiness 경로를 충분히 조사하지 못했다는 한계도 있으므로 재현/도달성 확인부터 해야 한다. 29/38은 scanner false negative 지적이며 실제 후보에 비밀 유출이 관측됐다는 뜻은 아니다.

## 2. R의 미병합 task/* 브랜치 20개

### 2.1 측정 방법과 테스트의 한계

`git for-each-ref refs/heads/task/`, `git merge-base dev <branch>`, `git diff --numstat <parent> <branch>`, `git ls-tree -r <branch>`로 확인했다. 모두 dev에 미병합이다. **공통 integration base는 647aa171**이며, 표의 parent는 작업 커밋의 실제 첫 부모다. `+/- LOC`는 parent→branch의 텍스트 diff다(주석·JSON·테스트 포함). 누적 LOC는 dev→branch의 diff다. 서로 기반을 물려받은 branch가 많으므로 누적 합계를 더해 독립 코드 양으로 해석하면 안 된다.

각 head를 `~/.agent-control-plane/scratch/migration-audit-1ukjr_y6/<head>`에 `git worktree add --detach`한 뒤 `CI=1 npm test`를 실행했다. 설치나 외부 API 호출 없이 Node의 기존 mock/fixture 테스트를 사용했다. 종료 후 `git worktree remove --force`는 **이 감사가 생성한 scratch worktree에만** 적용했다. 원래 checkout·branch ref는 보존했다.

테스트 경로 약어(각 branch의 보유 테스트 전체를 다음 표에 열거):

| 약어 | 실제 파일 |
|---|---|
| S | `test/smoke.test.js` |
| D | `factory/discover/adapters.test.js` |
| H | `factory/lib/http.test.js` |
| A | `factory/lib/access-policy.test.js` |
| R | `factory/lib/robots.test.js` |
| C | `factory/cluster/cluster.test.js` |
| F | `factory/facts/facts.test.js` |
| Q | `factory/score/score.test.js` |
| X | `factory/score/disambiguation.test.js` |
| L | `factory/score/roles.test.js` |
| E | `factory/score/evaluate-ranking.test.js` |

PASS는 exit 0이며 skip을 포함한다. discover의 **17개 recorded fixture**는 isolated tree에 `local/fixtures/<source>`가 없어 skip됐다. score 계열의 추가 **1개 T4 평가**도 비공개 `local/fixtures/eval/t4_eval.json`이 없어 skip됐다. R8/R11의 manifest는 population 17, used 5, k=7, 고정 digest를 요구한다. 따라서 synthetic PASS는 실제 수집기의 현재 웹 호환성이나 실측 T4 ranking 성공을 증명하지 않는다.

전체 branch 결과는 **15개 exit 0 / 5개 실패**다. 설치·모델 다운로드·실제 Keychain 조회 없이 기존 테스트만 실행했다.

### 2.2 브랜치별 고유 변경과 base

아래 전체 ref 이름과 head로 재조회할 수 있다. 파일 옆 숫자는 `+추가/-삭제`다.

| 작업 / head | 전체 branch ref | 첫 부모 | 고유 변경 파일·LOC | dev 대비 누적 |
|---|---|---|---|---|
| B3 `c9cdf353` | `task/task0263035119384155a56b0bcb-b3-factory-score-hook-score-and` | `647aa171` | `config/scoring.json` +23/−0<br>`factory/score/index.js` +67/−0<br>`factory/score/score.test.js` +89/−0<br>`prompts/expectation-gap.md` +16/−0 | 4 files changed, 195 insertions(+) |
| R6 `1fd9d8db` | `task/task255cbee92ff245959c849797-r6-factory-cluster-credited-wire` | `430ed08a` | `factory/cluster/cluster.test.js` +51/−0<br>`factory/cluster/index.js` +23/−4 | 10 files changed, 878 insertions(+) |
| B1c `06ecb042` | `task/task50f48de0a9e8410e8f0c46fe-b1c-factory-discover-correction` | `0aa22ee3` | `factory/discover/adapters.js` +46/−29<br>`factory/discover/adapters.test.js` +41/−2<br>`factory/discover/queries.json` +13/−0<br>`factory/lib/access-policy.js` +23/−0<br>`factory/lib/access-policy.test.js` +28/−0 | 11 files changed, 520 insertions(+) |
| R4 `8f872910` | `task/task5d8af9a55d604346a1f352ca-r4-factory-facts-archive-outside` | `eaa14a50` | `factory/facts/facts.test.js` +46/−4<br>`factory/facts/index.js` +54/−12<br>`prompts/factsheet.md` +7/−0 | 17 files changed, 1078 insertions(+) |
| R9 `99dd4682` | `task/task5e9180923552436ebacbc4a6-r9-factory-cluster-adjacent-bigr` | `1fd9d8db` | `factory/cluster/cluster.test.js` +71/−2<br>`factory/cluster/index.js` +31/−10 | 10 files changed, 968 insertions(+) |
| B4 `088dbee5` | `task/task65c3675ca3fa4c9c81def555-b4-factory-facts-article-archive` | `647aa171` | `factory/facts/facts.test.js` +41/−0<br>`factory/facts/index.js` +97/−0<br>`prompts/factsheet.md` +20/−0 | 3 files changed, 158 insertions(+) |
| R12 `08f3d461` | `task/task74ba7b2e7f604d90b8071a87-r12-factory-lib-robots-rfc-9309` | `0d96a625` | `factory/lib/robots.js` +19/−4<br>`factory/lib/robots.test.js` +60/−0 | 12 files changed, 627 insertions(+) |
| R8 `25877261` | `task/task7765f863c9184ebc865f9857-r8-factory-score-party-role-befo` | `e01b6f0d` | `config/t4-eval-manifest.json` +9/−0<br>`factory/score/evaluate-ranking.js` +31/−11<br>`factory/score/evaluate-ranking.test.js` +59/−0<br>`factory/score/index.js` +9/−2<br>`factory/score/roles.test.js` +15/−0<br>`factory/score/score.test.js` +12/−15 | 19 files changed, 1143 insertions(+) |
| B1 `0aa22ee3` | `task/task876529687d0c46258b752c5e-b1-factory-discover-heat-signal` | `647aa171` | `.gitignore` +11/−0<br>`factory/discover/adapters.js` +131/−0<br>`factory/discover/adapters.test.js` +80/−0<br>`factory/discover/cli.js` +33/−0<br>`factory/lib/http.js` +41/−0<br>`factory/lib/http.test.js` +47/−0<br>`factory/lib/robots.js` +40/−0<br>`factory/lib/secrets.js` +17/−0 | 8 files changed, 400 insertions(+) |
| R1 `bf08d04a` | `task/task8798a34253554512ac65c09d-r1-factory-lib-secrets-keychain` | `06ecb042` | `factory/lib/http.test.js` +39/−6<br>`factory/lib/secrets.js` +4/−5 | 11 files changed, 552 insertions(+) |
| R11 `da08a47a` | `task/task96f43446474f45e5965ab071-r11-factory-score-order-invarian` | `25877261` | `factory/score/index.js` +33/−0<br>`factory/score/roles.test.js` +28/−0 | 19 files changed, 1204 insertions(+) |
| R1b `0d96a625` | `task/task97fbbad5e63245eda8471d35-r1b-factory-lib-test-keychain-st` | `bf08d04a` | `factory/lib/http.test.js` +2/−2 | 11 files changed, 552 insertions(+) |
| B3c `88089252` | `task/task98cef40158cd4016b223af36-b3c-factory-score-correction-red` | `9f7ed020` | `config/scoring.json` +8/−3<br>`factory/score/disambiguation.test.js` +31/−0<br>`factory/score/index.js` +11/−2 | 15 files changed, 874 insertions(+) |
| R2 `1be7a99d` | `task/task9eb0b642f15846ac9d031e85-r2-factory-cluster-provenance-ba` | `c0a84c89` | `factory/cluster/cluster.test.js` +80/−5<br>`factory/cluster/index.js` +46/−8 | 10 files changed, 747 insertions(+) |
| R10 `fdd6533a` | `task/taskada5b2e2cefe4afb9b693b19-r10-factory-facts-claims-support` | `48c41ab4` | `factory/facts/facts.test.js` +26/−0<br>`factory/facts/index.js` +41/−1 | 17 files changed, 1202 insertions(+) |
| R3 `521988ec` | `task/taskdfdd819a198443bdb581fb10-r3-factory-score-red-line-scan-o` | `88089252` | `factory/score/disambiguation.test.js` +30/−0<br>`factory/score/evaluate-ranking.js` +27/−0<br>`factory/score/index.js` +2/−2<br>`factory/score/score.test.js` +28/−13 | 16 files changed, 946 insertions(+) |
| B2 `7739f8d4` | `task/taske4fd05e680e2435198e3a030-b2-factory-cluster-case-clusteri` | `647aa171` | `factory/cluster/cluster.test.js` +79/−0<br>`factory/cluster/index.js` +155/−0 | 2 files changed, 234 insertions(+) |
| R7 `48c41ab4` | `task/taske8a48f5e251949a7a2c5454d-r7-factory-facts-negation-and-co` | `8f872910` | `factory/facts/facts.test.js` +28/−0<br>`factory/facts/index.js` +31/−1 | 17 files changed, 1136 insertions(+) |
| R2b `430ed08a` | `task/taskef0ad8a994684d96b2ccd249-r2b-factory-cluster-unmapped-nav` | `1be7a99d` | `factory/cluster/cluster.test.js` +50/−0<br>`factory/cluster/index.js` +13/−2 | 10 files changed, 808 insertions(+) |
| R5 `e01b6f0d` | `task/taskf553424608b644348aef87d4-r5-factory-score-red-line-role-s` | `521988ec` | `factory/score/index.js` +45/−4<br>`factory/score/roles.test.js` +49/−0 | 17 files changed, 1036 insertions(+) |

### 2.3 실행 결과·현 운영 중복·판정

`reuse`는 검증된 일부 코드/반례를 선별 재사용할 가치가 있다는 뜻이며 merge 승인이 아니다. `preserve only`는 이력·시험 자료로 보존하되 현재 이관에 적용하지 않는다는 뜻이다. `drop`은 이관 후보에서 제외한다는 평가일 뿐 ref 삭제가 아니다. **이번 평가에서는 branch를 삭제/폐기하지 않으며, 최종 계열에 이미 흡수된 초기 branch도 preserve only로 남긴다.**

| 작업 | 보유 테스트 | npm test: pass / fail / skip (exit) | 현 운영과의 비교·판정 |
|---|---|---|---|
| B3 | Q S | 4 / 1 / 1 (1) | `topic_score.rank`와 가중 점수·레드라인이 겹침. ordinary control을 오차단하는 실패. **preserve only**; R11로 수정 계보 보존. |
| R6 | C D H S | 65 / 0 / 17 (0) | 전재/통신사 credit을 같은 출처로 처리. 현 `canonical_sample`의 방송사·중복 제거와 일부 겹치나 기사 독립성은 다름. R9에 포함. **preserve only**. |
| B1c | D A H S | 47 / 0 / 17 (0) | 판결 검색 query·API별 접근 정책. 현재 Naver/YouTube/PublicHTTP와 겹침. R12에 포함. **preserve only**. |
| R4 | C D F H Q S | 57 / 1 / 18 (1) | checkout 밖 raw archive, URL별 provenance, 구형/선고 분리. 현 `source_snapshots`/facts와 겹치며 보관 위치는 다름. 후속 R10이 대체. **preserve only**. |
| R9 | C D H S | 71 / 0 / 17 (0) | 인접 bigram·URL/outlet/origin 결합·완결된 판결문만 인정. 현 코드에 범용 `clusterRows/confirm` 동등 API 없음. **reuse**: 출처 독립성 반례/소함수부터, 정규식의 미확정은 held 유지. |
| B4 | F S | 2 / 0 / 0 (0) | 초기 기사 archive/claim trace. 현 사실표·SHA256 검수와 목적 중복, 초기 archive 정책은 R4/R10이 보강. **preserve only**. |
| R12 | D A H R S | 55 / 0 / 17 (0) | RFC 9309 group 선택/경로 precedence 테스트. 현 Python `PublicHTTP`의 robots와 겹치나 JS API는 별개. **reuse**: 반례/알고리즘 단위; Node 수집기 전체 교체는 별도 비교 필요. |
| R8 | C D H X E L Q S | 66 / 0 / 18 (0) | 정치·공인 party role 및 T4 manifest. 현 H3의 정치 소재 허용 방향과 옛 일괄 필터가 일치하지 않을 수 있음. R11 이전. **preserve only**. |
| B1 | D H S | 44 / 0 / 17 (0) | 17개 heat adapter·HTTP retry/robots/keys. 현재 `topic_score`/`topic_gap`에 운영 수집기 존재. 실제 fixture 미검증, 후속 보정 있음. **preserve only**. |
| R1 | D A H S | 46 / 2 / 17 (1) | Naver Keychain-only는 현 Python Naver와 중복. stub의 service 인덱스 오류로 2개 실패, R1b가 보정. **preserve only**; 실패를 운영 Keychain 오류라고 해석하지 않음. |
| R11 | C D H X E L Q S | 67 / 0 / 18 (0) | 문장 순서 불변 party involvement 판정. 현 순위 percentile/상관 분석과 weighted hook scoring은 비동등. 실측 T4 미실행·정치/공인 정책 불일치 가능. **preserve only**, 반례 참조 가능. |
| R1b | D A H S | 48 / 0 / 17 (0) | stub에서 service 인자 `args[2]` 선택 보정만. R12 포함. **preserve only**. |
| B3c | C D H X Q S | 57 / 0 / 18 (0) | 피해자·관계·compound role 필터 수정. 현 `gates.redline_gate`/topic의 excluded decision과 겹침. 후속 R3/R5/R8/R11 있음. **preserve only**. |
| R2 | C D H S | 58 / 0 / 17 (0) | 출처·사건 동일성·held 도입. 현 title match/방송사 dedup과 부분 중복. R9 이전. **preserve only**. |
| R10 | C D F H Q S | 59 / 1 / 18 (1) | 주체·항목·값·단위가 같은 문장 근거에 묶여야 채택. 현 `fact_gate`의 exact answer/source hash 검사에 없는 보강. **reuse**: F verifier/반례만; 전체 branch는 상속된 score 실패로 미통과. |
| R3 | C D H X Q S | 59 / 0 / 18 (0) | article lead까지 레드라인·T4 assertion. 현재 사실표·내레이션 필터와 겹침, R11 이전. **preserve only**. |
| B2 | C S | 8 / 0 / 0 (0) | clustering·2 independent publishers 확인의 초기형. 범용 함수는 현 운영에 없으나 후속 provenance 보강 전. **preserve only**. |
| R7 | C D F H Q S | 58 / 1 / 18 (1) | 부정/대조절 claim support. 현재 literal facts 대조에 없는 의미 보강이나 R10에 포함. **preserve only**. |
| R2b | C D H S | 62 / 0 / 17 (0) | 미매핑 Naver oid를 독립 출처로 세지 않음. 현 원문 URL·publisher 수집의 보강 반례, R9 포함. **preserve only**. |
| R5 | C D H X L Q S | 62 / 0 / 18 (0) | 공인·compound nouns·가해/피해 역할 분리. 현재 redline 검수와 목적 중복. R11 이전. **preserve only**. |

실패 상세: B3/R4/R7/R10은 `factory/score/score.test.js:35`의 `ordinary controls pass and article metadata is also filtered`, 실제 `true`/기대 `false`다. facts 수정 branch에 남아 있는 옛 score 테스트에서 발생했다. 별도 격리 worktree에서 `node --test factory/facts/facts.test.js` 재실행: R4 **3/3**, R7 **4/4**, R10 **5/5**, skip 0. R1은 `http.test.js:41,62`의 stub 오류(`keychain-id` 대신 synthetic `keychain-secret`, missing rejection)이며 R1b의 `+2/−2`로 바로잡힌다. 실제 Keychain을 읽어 확인하지 않았다.

이 계열들은 **현재 W에 이미 합쳐진 Python 구현이 아니다**. JavaScript `factory/lib/{http,robots,secrets}.js`와 W의 Python `factory/lib/{frame_qa,audio_mix}.py`는 디렉터리 이름만 같고 역할·API가 다르다. 같은 이름을 근거로 덮어쓰면 안 된다. reuse로 평가한 R9/R10도 LLM/검색 주입·보수적인 lexical 검증이며 사실성의 자동 보증이 아니다.

## 3. W 현 운영 코드 인벤토리

### 3.1 Git과 디스크의 차이

로컬 Git은 운영 환경의 완전한 재현본이 아니다. 감사 시 tracked 파일은 factory 178, production 545, channel 10, episodes 1,093, research 2,370, upload 388개 등이다(자료 포함, acceptance 고정 수치가 아님). `.gitignore`는 text/code allowlist와 미디어·모델·venv·node_modules·cache·render 결과 제외, 개별 secret-screen 제외를 함께 사용한다. `REPO.md`의 1,000,000-byte/UTF-8 등록 기준은 Run A public-safe 검사에 크기 제한을 추가할 근거가 아니다.

- 감사 시작부터 tracked 수정: `factory/review_gates.py` +20/−2, `factory/REVIEW_CHECKLIST.md` +29/−0, `upload/ledger.json` +2/−2.
- 미추적 운영 코드: `factory/lib/{frame_qa,audio_mix}.py`, `factory/THIRD_PARTY.md`, `factory/tests/{test_cas_adoption,test_topic_score}.py`, `factory/topic_score.py`, `factory/topic_gap.py`, `channel/analytics/{api_pull,oauth_setup}.py` 등. HEAD만 복사하면 빠진다.
- `production/lf_toon/`, `episodes/review_full/`은 활동 중 writer 경로로 Git에서 명시적 제외. 별도 저장소 `research/tools/stickman-video-director/`, `tts_lab/engines/melotts/src/`도 제외. 감사에서 이 경계·설정을 바꾸지 않았다.
- checklist 디스크본은 H1–H13 및 미적용 B2 제안을 포함하지만 `review_gates.ITEMS`는 A1–G2다. H 전체가 자동 구현됐다고 간주하면 안 된다. 새 `FRAME_QA`는 advisory이며 readiness를 막지 않는다.

### 3.2 모듈·entry point·의존 관계

| 영역 | entry point / 핵심 모듈 | 의존·입출력 |
|---|---|---|
| Shorts orchestration | `factory/short.py qNNN --no N`, `--check <package>` | W/.venv로 재실행, `episodes/quiz/episodes_n16.py` import, fresh/prepare_v52/gates/review_gates/render.cjs 조합. `upload/pkg/`에 새 패키지·QA·READY·media. **--check도 qa/READY를 쓰므로 원본에서 감사용 실행하지 않음** |
| 준비/음성 | `factory/{fresh,prepare_v52,build_hero}.py` | NumPy/SciPy/soundfile/Supertonic/MLX Whisper, research/raw*, S001 TTS lexicon·layout.chunks, episode make/align, master/AAC/fonts. prepare_v52는 `FACTORY_WORKSPACE`, `FACTORY_PUBLIC`, `FACTORY_PREPARED` 사용. fresh에는 Blender hero 경로가 아직 있음 |
| legacy gates | `factory/gates.py` | NumPy/Pillow/OpenCV/FFmpeg, short, `episodes/quiz/out/v3/qa.py`, `v51_support/align_v51.py`, `v52_q013_q014_support/alignment_word_clock.py`. 번호·제목·empty panel·facts·redline·tsc·ASR·audio parity·서명/READY. ledger/source snapshot 필요 |
| 공통 review | `factory/review_gates.py`, `figure_shapes.py`, `ocr_vision.swift`, `gate_calibration.json`, `REVIEW_CHECKLIST.md`, `upload_precheck.md` | A1–G2, frame/audio/ASR/OCR, code/input/artifact SHA256. 입력 부족·자동 FAIL·CTO 서명 구분. Pillow/NumPy, 지연 import OpenCV/MLX Whisper, FFmpeg/ffprobe, macOS Vision Swift 또는 한국어 Tesseract. 필요 시 HERE/.ocr_vision compile |
| long-form QA | `factory/longform_qa.py VIDEO --shots … --script … --facts …` | review_gates + gates.finalize_review. review_runs에 새 결과, --resume은 기존 결과 갱신. cache도 source/evidence hash 확인. 렌더/업로드 없음 |
| 회귀·보정 | `factory/{regression,review_regression,calibrate_review}.py` | 승인/불합격 media·보존 측정치 필요, review_runs 생성. 이번에는 전체 렌더/ASR 보정 실행하지 않음 |
| frame/audio library | `python -m factory.lib.frame_qa VIDEO OUT`, `python -m factory.lib.audio_mix --voice … --out NEW.wav --words …` | 165/179 LOC. NumPy/Pillow, NumPy/SciPy + frame_qa, FFmpeg/ffprobe. 통계·contact sheets·LUFS/TP, 새 PCM mix/duck/limiter. 덮어쓰기 거부. MIT 고지/THIRD_PARTY 보존 필요 |
| topic research | `factory/topic_score.py {collect,naver,sources,enrich,shorts,gap,rank}`, `topic_gap.py` | urllib/robotparser/fcntl + yt-dlp. robots/redirect·중복·own-channel·missing=null, Naver API, sentence-demand gap·headline/comment 표본·percentile/correlation. research/topic_scores에 쓰기. live 수집 명령 미실행 |
| 분석 loop | `channel/analytics/{collect_parse,analyze}.py` | stdlib CLI. Studio notes→daily JSON, features join→descriptive 분석. 기간 분리·결측 보존. daily/features는 공개 코드와 분리 |
| 인증 analytics | `channel/analytics/{api_pull,oauth_setup}.py` | google-auth/google-api-python-client/google-auth-oauthlib, Keychain, readonly YouTube/Analytics scope. **main guard 없이 import 때 API/인증/쓰기가 실행**됨. oauth_setup은 localhost 8765 OAuth·Keychain 갱신. 실행/import하지 않음 |
| Shorts Remotion | compositor package studio/render→`src/index.ts`→`Root.tsx`; `factory/render.cjs` | React 18.3.1, Remotion/CLI/three 4.0.538 계열, TS 5.9.3, Three 0.186.1, fiber 8.18.0, postprocessing 6.39.5, react-peeps, Pretendard. package-lock 존재. public render.json/audio/fonts/plates. factory vendor TSX는 compositor 절대 import |
| offline glue | `factory/{render.cjs,offline_chromium.sh}`, compositor `src/v4/offline.cjs`, `src/v4spike/chromium.sh` | compositor node_modules createRequire, renderer 내부 downloadFile을 file:// 전용으로 교체, Chromium host resolution 차단. VIDEO/COVER/EMPTY/AUDIT 렌더. 패키지 내부 API 의존으로 버전 변경 시 검증 필요 |
| toon | `production/lf_toon/src/{entry.tsx,lf2/entry.tsx,n18/entry.tsx}`, ToonRig/motion/sets/Captions/camera2d/expressions | Remotion/React TS, timeline/shots/captions JSON, fonts/audio; prepare/align/finalize/package와 proof/full media. 독립 package.json은 없고 compositor 의존 환경 활용. 현재 Git 제외, 활동 중 writer와 함께 이동 불가 |
| 기존·실험 제작 | production의 astra_12min/astra_preserved/blender/compositor_pilot/terra_toon_recovery/assets, audio/{synth,synth2}.py | bpy·glb/blend/texture, Pillow·NumPy·SciPy·soundfile·Supertonic·Whisper·FFmpeg. 에피소드 코드·snapshot·old proof가 섞임. 파일 존재만으로 현 기본 경로라고 단정하지 않음 |
| TTS·자료·발행 | tts/tts_lab/episodes/research/references/upload | 라이선스·실험·대본·사실표·원문·준비/산출 media·원장. 코드와 민감/저작권 자료 혼재. 폴더 전체 이관 금지 |
| 로컬 등록 보호 | repo_check.py, .git/hooks, .gitignore | staged text/secret screen, report는 .git 내부. 이번 감사에서는 exclusions를 갱신할 수 있는 screen/check를 재실행하지 않음. 과거 scan은 새 파일 안전을 증명하지 않음 |

전체 Python 의존성을 고정한 루트 pyproject/requirements/lock은 확인되지 않았다. 실행 환경: W/.venv **Python 3.12.12**, **Node 22.23.2**, **npm 10.9.8**, **FFmpeg 8.1**. Node 20·Ubuntu·fresh install 재현성은 이번 실행 범위가 아니다.

`factory/lib + review_gates + REVIEW_CHECKLIST`만 바로 옮기기에는 의존이 크다: `longform_qa → gates → short → episodes_n16`, `gates → qa/align_v51/alignment_word_clock`. review_gates는 figure_shapes·Swift OCR·calibration·precheck를 읽고 코드 위치를 input hash에 넣는다. **파일 이동으로 절대경로 기반 digest가 바뀌므로 기존 CTO signoff를 그대로 재사용할 수 없다.**

### 3.3 외부 경로·media·secret boundary

| 경계 | 실제 참조와 근거 | 이관 의미 |
|---|---|---|
| 절대 workspace | `/Users/isaac/projects/verdict-kr/work` (astra/blender/assets/recovery); factory/vendor의 QuizPanels/HookV51Seed/ObjectSets는 `…/production/compositor/src/*` import | source root와 asset root 분리 필요. 경로 문자열만 바꾸고 import/동등성을 생략할 수 없음 |
| 상대 root | short.W, review_gates.ROOT/HERE는 __file__ 기반. gates는 episode 폴더를 sys.path에 추가; fresh는 S001/tts.py·layout.py·raw*·prepared bundle 읽음 | code 이동과 data 이동을 분리. 위치만 바꿔도 venv/content 검색 경로가 달라짐 |
| 모델·실행기 | `/Users/isaac/.cache/huggingface/hub/models--mlx-community--whisper-large-v3-turbo/snapshots`, Path.home()/.cache/…, `.cache/supertonic3`, `/Applications/Blender.app/Contents/MacOS/Blender`, `/opt/homebrew/bin/yt-dlp` | 모델/cache/앱은 repo 밖. final ASR는 local weights/HF offline env 사용 |
| 폰트·OCR·브라우저 | `/System/Library/Fonts/AppleSDGothicNeo.ttc`, Arial/Menlo; factory/.ocr_vision, swiftc, Tesseract kor; compositor/node_modules/.remotion/chrome-headless-shell/… | macOS/Linux 차이. 폰트 lock/install 검증과 실제 font readiness 별도 필요 |
| 임시/설치 경로 | `/tmp/v4spike-npm-cache`, `/tmp/verdict-n18-npm-cache`, `/tmp/claude-501/*`, `~/Library/Application Support/Blender/…` | 임시 진단/설치 자료를 운영 source·자산으로 잘못 분류하지 않음 |
| Aside·Studio | upload/upload_one.sh:8, aside_task.sh:10: `~/.aside/u/0/sessions/*_<SID>/files`; channel/채널운영.md:62 recipe | 계정·세션·profile 경계. 이 파일들은 기존 secret screen 제외 대상. .aside 내용/쿠키/profile을 읽지 않았으며 이관 제외 |
| Naver locator | `myeotnyeon.naver.client_id`, `myeotnyeon.naver.client_secret`, factory/topic_score.py:51–53 | Keychain 값→메모리→request header. W는 account selector 없지만 JS R1/R12는 `-a myeotnyeon`도 요구. **같은 서비스명만으로 조회 동등성 없음**. 비밀 실조회는 하지 않음 |
| YouTube OAuth locator | `myeotnyeon.youtube.oauth_client_json`, `myeotnyeon.youtube.oauth_refresh_token`, channel/analytics/* | readonly scope. oauth_setup은 local account 인자로 저장하고 read helper는 account selector 없음. config/token/계정 데이터 export 금지 |
| media refs | Root staticFile ep001/render.json·s001·q001…q017·mix_master.wav·fonts/plates, factory recipe.public/master/AAC/hero, toon timeline/audio/proof/full/render_cache | repo에는 허용 source/manifest만. W media/원문 위치 유지. 음악 라이선스 텍스트가 존재해도 음악 공개 권한이 생기지 않음 |
| private data | research/raw*/*.txt, facts/source matrix, upload/pkg의 research/recipe/qa JSON, daily/features, ledger | hash/provenance에 원문/절대경로가 포함될 수 있음. JSON/Markdown이라는 이유로 공개 허용하지 않음. branch facts 외부 archive는 현 W raw 정책과 다름 |

§5는 raw 기사·음악/생성 audio/media·upload 전체·channel logs·references·owner planning 원본·EP001 tree·Blender scripts/assets·public/{ep001,plates,s001,*/mix_master.wav}·out/node_modules/tts/tts_lab/.venv·Studio/Aside/Chrome profile을 제외한다. **W의 text-only Git 범위와 공개 허용 목록은 다르다.** 이 경로 인벤토리는 public-safe PASS 증명서가 아니다.

### 3.4 이번 운영 테스트 결과

| W 기준 명령 | 결과 | 범위/한계 |
|---|---|---|
| `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m unittest discover -s factory/tests -p 'test_*.py'` | **51 PASS**, exit 0 | review/source signoff/topic/CAS frame·audio. 일부 local package/source fixture 필요, portable clone 증거 아님 |
| `PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B -m unittest discover -s channel/analytics -p 'test_*.py'` | **6 PASS**, exit 0 | parser/분석. 인증 API 미호출 |
| `(cd production/compositor && node --experimental-strip-types --test tests/endTransition.test.ts)` | **30 PASS**, skip 0, exit 0 | 경계/JSON 테스트, 전체 render/tsc 아님 |
| `node --experimental-strip-types --test production/lf_toon/tests/camera2d.test.ts` | **7 PASS**, skip 0, exit 0 | 카메라/표정 결정성. 제외 경로 source 읽기만 수행 |
| `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=factory .venv/bin/python -B -m unittest discover -s factory -p 'test_gates.py'` | **6 PASS / 1 FAIL**, exit 1 | reservation_owner_and_published_video_identity:24는 no16/q013을 video_id 없이 PASS라 기대하나 현재 ledger는 scheduled. 원장·테스트 미수정 |

전체 제작·ASR·OAuth·Naver 실측·업로드·검수 서명·CI readback은 실행하지 않았다. 기존 실패를 가리기 위해 fixture/기대값/원장을 바꾸지 않았다.

## 4. 첫 이관 단위: 현 factory가 사용하는 자막 분할 함수

**권장: `episodes/S001/layout.py → pipeline/tools/layout.py`의 import API, 특히 `chunks(text, maxline=11)`.** stdlib(json/pathlib/re)만 사용하고 factory/fresh.py:65,96이 새 제작 자막에 실제 호출한다. §5·T1에 명시된 파일이므로 기존 계약 안에서 진전할 수 있다. 이 단위 PASS를 전체 Run A 완료로 보고하지 않는다.

f975ad3d 후보에는 이미 pipeline/tools/layout.py가 있다. W 원본과 `git show f975ad3d:pipeline/tools/layout.py`를 diff한 결과 **import os 추가와 HERE의 EPISODE_DIR 매개변수화뿐**이다. chunks/wrap/weight/tc 구현은 같다. 새 이관을 중복 생성하기보다 기존 후보를 현재 운영과 대조·보정한다.

### 4.1 Owned paths

| 경로 | 역할 |
|---|---|
| repo `pipeline/tools/layout.py` | 허용된 원본 및 경로 설정. import 때 파일 쓰기 없음 |
| repo `test/layout.test.mjs` (향후 제안) | 기존 npm test에 잡히는 behavior test: 한국어 장문/짧은 tail/구두점/개행/무공백·maxline별 고정 출력. 새 runner/CI 없음 |
| repo 기존 `test/pipeline.test.mjs` | V1 compile 유지. V2·다른 T1 검증 삭제/skip 금지 |
| W `factory/fresh.py` (향후 local consumer 전환만) | 현재 spec_from_file_location의 module path에 `FACTORY_LAYOUT_MODULE` 선택 설정 제안. 없으면 기존 W/episodes/S001/layout.py. **이번 감사에서는 수정하지 않으며 이 파일을 Run A 공개 allowlist에 추가한 것으로 취급하지 않음** |
| W 원본 layout·에피소드·media·ledger | 그대로 보존. main은 HERE 아래에 쓰므로 동등성 비교에서 실행하지 않음 |

lib/review_gates/checklist·서명·short orchestration·toon·ledger/raw/audio/font를 같이 옮기지 않는다. 이는 실제 의존과 원래 허용 목록에 따른 축소다. source의 공개 이관은 현 계약 내 보정이고, local consumer 전환은 별도 운영 변경이다.

### 4.2 검증 및 동일 입력→동일 출력 테스트

향후 보정 checkout root를 `M`, scratch root를 `SCRATCH`로 설정한다. 다음은 **이관 후 실행할 제안**이며 이번에 parity PASS했다고 주장하지 않는다.

```sh
cd "$M"
npm test
node --test test/layout.test.mjs
PYTHONPYCACHEPREFIX="$SCRATCH/pyc" python3 -m py_compile pipeline/tools/layout.py
```

동등성은 동일 Python·입력·maxline에서 반환값을 바이트 단위로 비교한다. 경로/시각을 지우는 느슨한 qa.json 비교 대신 실제 운영에서 사용하는 함수 출력을 비교하며 main을 호출하지 않는다:

```sh
"$W/.venv/bin/python" -B - "$W" "$M" <<'PY'
import hashlib, importlib.util, json, pathlib, sys
w, m = map(pathlib.Path, sys.argv[1:])
def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj
old = module('layout_before', w/'episodes/S001/layout.py')
new = module('layout_after', m/'pipeline/tools/layout.py')
texts = ['', '판결은, 징역 8개월에 집행유예 2년.',
         '공백없는긴문장입니다'*5, '첫 문장, 다음 문장? 아주 짧은 끝.',
         '구형과 선고를 구분합니다.\n같은 사실을 보존합니다.']
doc = json.loads((w/'episodes/S001/script_text.json').read_text())
texts += [s for cue in doc['cues'] for s in cue['narration']]
def output(mod):
    value = {'chunks': [[s,n,mod.chunks(s,n)] for s in texts for n in (8,11,14)],
             'wrap': [[s,n,mod.wrap(s,n)] for s in texts for n in (8,11,14)],
             'weight': [mod.weight(s) for s in texts],
             'tc': [mod.tc(f) for f in (0,1,29,30,31,1799,1800,108000)]}
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':')).encode()
a, b = output(old), output(new)
assert a == b, 'caption API output changed'
print('layout parity PASS', hashlib.sha256(a).hexdigest())
PY
```

공개 unit test에는 private W 경로/원본을 넣지 않고 synthetic input과 고정 기대 문자열을 사용한다. 위 private parity는 source 이관 비교다. V3–V6는 이 순수 함수 단위에 적용되지 않지만 **Run A 전체 acceptance에서는 유지**한다.

### 4.3 전환·rollback (제안만, 미실행)

1. 기존 후보 layout을 현 원본과 위 방식으로 비교한다. HERE 매개변수화 외 차이가 생기면 해당 제품 차이만 보정한다. source hash와 repo commit을 확인한다.
2. source/behavior test는 현 npm test로 검증하고 workflow/manifest는 바꾸지 않는다. 작은 단위 PASS와 Run A 남은 BLOCK을 함께 보고한다. 이번 감사는 PR/merge를 실행하지 않았다.
3. 향후 fresh에 module 선택 설정을 추가한 뒤 **다음 새 scratch/package 작업만** `FACTORY_LAYOUT_MODULE="$M/pipeline/tools/layout.py"`로 실행한다. 기존 패키지·READY·서명·원장을 재작성하지 않는다. 공개 repo에는 개인 M/W 값을 저장하지 않는다.
4. old/new 선택 양쪽에서 반환값 일치를 확인하고 새 작업의 선택만 전환한다. M은 검증한 commit에 고정하며 실행 중 checkout을 갱신하지 않는다.
5. **rollback은 FACTORY_LAYOUT_MODULE 해제**로 원래 W/episodes/S001/layout.py를 다시 선택한다. 원본 보존으로 data 이동/DB migration/영상 복구가 필요 없다. 진행 중 작업은 마친 뒤 다음 새 작업부터 바꾼다.

baseline SHA256: layout.py `73a0b83831bec9b9ecd041817081025c229e208d180d1aa63d56a34fa144d6bc`; fresh.py `07630e667064fc1b254078b85c42a19b4980e658cb5cee7792258f7199dc22e0`.

후속 library 단위는 독립 CLI frame_qa.py부터 고려할 수 있다. 하지만 factory 경로의 §5 포함 근거는 아직 없고, gate 전체는 위치 기반 hash/서명/legacy imports를 분리해야 한다. 이번 감사는 그 분리 구현이나 acceptance 축소를 실행하지 않았다.

## 5. CommitLore context/guard

CommitLore **1.7.5**. W에 연결된 MCP와 checkout별 CLI로 `context/limits/ruled-out/warnings --json --no-index`를 읽었다. init/index rebuild/doctor --fix/fetch/sync/capture/commit은 하지 않았다.

| vantage / 경로 | context | guard 및 한계 |
|---|---|---|
| W main@8f31ce88 전체 | active **claim** `r-1cffa1cb2f11`, provenance drafted, 2026-11-06T10:12:06+09:00. 경로 REPO.md·DECISIONS.md·PROJECT_STATUS.md. `Limit: Media and the active full-film writer paths production/lf_toon/ and episodes/review_full/ are excluded from Git.` | local REPO.md/.gitignore와 일치. directive/검증된 서명 명령이 아니라 claim. 전체 limits 1, ruled-out 0, warnings 0 |
| W factory/lib·review_gates.py·REVIEW_CHECKLIST.md·production·channel·audit 문서 | 각 active record 0, history ready, coverage complete, notes absent | “운영 동작 보존·독립 offline library 추출·media/full-film/credentials local 유지” proposal: 각 exit 0, matched=false, matches=[], incomplete=false. path-empty 결과로 문서의 전체 제한을 무시하지 않음 |
| W plan/audit MCP before_change | active_decisions=[], verification_gaps=[] | appendix 및 plan 링크만 추가 proposal: revival match 없음 |
| W episodes/S001/layout.py·factory/fresh.py | 각 context 0, history ready, coverage complete, notes absent | “layout caption API의 동일 출력, 가역적 local module 선택, 원본/media 보존” proposal: 각각 exit 0, matched=false, matches=[], incomplete=false |
| R task/…r12@08f3d461 전체·위 주요 path | context/limits/ruled-out/warnings 0, history ready, coverage complete, notes absent, upstream 없음 | 같은 extraction proposal 각 guard exit 0, match 없음. 현재 HEAD에서 도달하는 기록에 한정 |
| Run A f975ad3d detached scratch (worker repo) | record 0이나 **exit 3, notes=unfetched**, history ready, coverage complete, ref=null | “현 allowlist 내 T1/public-safe 보정 및 layout 추출” proposal: **exit 3, incomplete=true**, match 없음. upstream notes 누락 가능. “제약 없음”이라고 결론 내릴 수 없으며 읽기 전용 범위상 fetch/설정 보정하지 않음 |

Guard는 advisory이고 빈 match가 기각된 접근 부재의 증명은 아니다. W/R의 upstream 없는 local vantage와 Run A detached vantage를 구분했다. 20개 local branch 전체 log에서도 추가 결정 trailer 기록을 찾지 못했으나 worker의 unfetched notes까지 없다고 단정하지 않는다. 기존 계획의 “매 변경 CommitLore 필수”와 manifest의 **preferred**는 다르다. 기록을 만들어내지 않으며 새 결정 기록/커밋을 생성하지 않았다.

첫 단위의 W 원본/consumer 기록은 위와 같이 확인했다. destination의 향후 HEAD 기록도 실행 전에 확인해야 한다. 이번 guard의 빈 결과가 달라진 HEAD에 대한 영구 허가가 되지는 않는다.

## 6. 산출물과 남은 공백

- 감사 결과는 이 문서 한 곳에 둔다. 기존 plan에는 링크만 추가하고 비교표를 중복하지 않는다.
- 운영 코드/media/ledger/branch/ACP 상태는 보존. 감사 생성 scratch worktree는 모두 제거했다.
- complete private handoff/design 및 당시 전체 원본 비교, V3–V6 설치/실행/CI 증거, 실제 recorded fixture/T4 실측, worker unfetched notes는 남은 공백이다. 이를 PASS로 쓰지 않는다.
- 이 감사는 접근 가능한 기록·분리된 상태·branch별 테스트·운영 의존/경계·전환 제안을 제공한다. Run A 완료·BLOCK 해제·생산 전환을 수행한 결과가 아니다.
