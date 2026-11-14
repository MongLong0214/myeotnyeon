# youtube-agent-skill (Jakeschincariol) 분석 — utillayer판과의 차이 (2026-11-08)

대상: 커밋 a2feb21 (2026-09-16, v1.0.0, MIT © 2026 Jake Schincariol). 클론 `src/`는 로컬 전용이다. 상위 `.gitignore`가 `*.py`/`*.md`를 허용하므로 `git add -A`를 쓰지 않는다. 하위 에이전트의 쓰기가 막혀서 CTO가 저장했다.

## 결론: Jakes가 원본이고, utillayer는 그 파생 재업로드판
- 생성 시점은 Jakes가 09-16, utillayer가 10-24다. utillayer LICENSE에는 두 저작권자가 함께 적혀 있다.
- utillayer CHANGELOG에 "rewritten in the pack's own words"라고 적혀 있다.
- 훅 공식 21개는 이름·순서·정규식까지 모두 같다. 가중치(0.6 평균 + 0.4 최저)도 같다.
- Jakes에만 있는 기능은 없다. utillayer판이 상위호환이다(sourcekit, scriptcheck, shorts.py, 테스트 42개).

## Jakes판 결함 (실측)
- **hookscore:** 단어 정규식이 `[a-z0-9]`뿐이다. 그래서 한국어 훅은 전부 WEAK(25)가 된다.
- **"74개 훅으로 보정":** 데이터를 공개하지 않아 검증할 수 없다. utillayer는 이 주장을 지웠다.
- **출처 없는 수치:** 예문에 출처 없는 퍼센트와 배수가 있다("97%", "62%", "4배").
- **title.py:** 한국어를 인식하지 못한다. 문서는 썸네일 3단어라고 하는데 코드는 4단어를 넘어야 경고한다.
- **swipe.py:** 조회수 누락을 0으로 넣어 중앙값을 끌어내린다. 실측에서 100배 왜곡이 났다. 쇼츠와 롱폼을 한 중앙값으로 섞는다.
- **retention.py:** `max(x) ≤ 100.5`만 보고 축을 판별한다. 그래서 100초 이하 영상의 초 단위 CSV를 퍼센트로 오인한다.
- **쇼츠 커터:** 코드가 없고 프롬프트뿐이다.

## 채택
| # | 판정 | 노력 | 대상 | 내용 |
|---|---|---|---|---|
| J1 | Adopt | S | `factory/lib/retention.py` L146 | 우리 채택본에도 같은 축 오판 폴백이 있다. 헤더 없는 CSV이고 duration이 100 이하이면 초 단위로 보거나 `--unit` 인자를 필수로 받는다. 실측에서 훅 누수가 42 대 26으로 틀렸다. API 경로는 영향 없음 |
| J2 | Adopt | S | `factory/shorts_rules.py:105`, `factory/FACTCHECK_PROMPT.md:3` | 출처 표기에 `© 2026 Jake Schincariol`을 추가한다(MIT 고지 일관성) |
| J3 | Adopt(규칙) | S | `factory/REVIEW_CHECKLIST.md` | 훅 예문과 템플릿에 출처 없는 퍼센트나 배수를 넣지 않는다 |
| J4 | Try | S | `factory/shorts_rules.py` (보고만) | 쇼츠 루프 검사: 마지막 문장이 첫 문장을 다시 부르는지 본다. 근거가 없으니 리텐션 데이터로 확인할 때까지 보고만 한다 |
| J5–J7 | Skip | — | — | Jakes판 도구 6개, 바이럴 배수(topic_score에 이미 있음), "74개 보정" 인용 |

포팅할 코드는 없다.
