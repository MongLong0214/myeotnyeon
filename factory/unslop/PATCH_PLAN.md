# 스타일 적용 위치 — 후속 패치 제안

2026-11-06. **이 문서는 패치 계획이며 아래 코드는 이번 작업에서 변경하지 않았다.** `shorts-batch1107`, `lf-full-*`, 해당 입력·출력·타임라인·원본 패키지를 덮어쓰지 않는다. 먼저 별도 시안 복사본에서 적용하고 기존 renderer와 엔트리는 그대로 둔다. 새 CI·스캐너·서명 절차를 만들지 않는다.

## Shorts: q014 comedy를 기준으로 연결

현재 진입은 `episodes/quiz/q014/fight_revision/comedy/entry.tsx`의 `Video`다. f0–60은 외부 `HookV52`, 이후는 `Quiz(...hookStyle="v51")`다. 따라서 `Header`만 바꾸면 도입과 엔드 카드가 그대로 남는다. `upload/pkg/q014_n15*`와 `factory/vendor/QuizPanels.tsx`는 별도 사본이므로 원본 영상의 경로라고 가정하지 않는다.

| 기준 파일·함수 | 후속 시안에서 바꿀 내용 | 보존할 것 |
|---|---|---|
| `episodes/quiz/q014/fight_revision/comedy/QuizPanels.tsx` — `Caption`, `HL` | 70px/800/stroke12를 STYLE의 64px/700/stroke6으로. 정규식 자동 강조 대신 cue별 선택 어구를 받도록 하고, 명시가 없으면 전부 흰색 | `from_ <= frame < to`, 문장·숫자·귀속·부정어, 실제 발화 경계 |
| 같은 파일 — `Header` | 본문 상시 브랜드·회차·사건 제목·질문/정답 배지를 제거. 질문 순간에만 필요한 문구를 렌더 | 질문·정답 공개 시점과 심급 표기 |
| 같은 파일 — `Quiz`, `PANEL`, `R` | 1000×900 장면을 960×864 둥근 패널로 고정하는 wrapper를 장면 역할별 stage로 분리. 바깥 scene radius26 제거. 재연 고지를 stage 밖 한 곳에서 렌더 | `transition.ranges`, `Sequence` 시간·오디오·hookStyle 분기. 기존 safe area는 내용에 유지 |
| 같은 파일 — `Weigh` | `CourtComedy` 위에 항상 얹는 A/B/C 버튼 제거. 선택지의 노출을 질문 비트에 한정 | 법원이 본 근거와 피고인/법관 구별 |
| 같은 파일 — `Tag`, `Reason`, `Reveal`, `Outro` | 중복 tag/도장/CTA를 줄임. 판결 숫자는 한 곳에 두고 검찰 구형·1심/항소심 선고를 명시. 철창과 법관이 겹치는 재구도도 수정 | 금지선을 지키는 실제 근거 표시는 삭제하지 않음 |
| `episodes/quiz/q014/fight_revision/comedy/ComedyLogic.tsx` — `RecorderComedy` | 긴 제목·CCTV 설명 띠·자체 재구성 띠 제거. 얼굴·휴대폰을 세로 구도로 다시 배치 | 녹음 시도의 검찰 귀속, 독립 비유임을 밝히는 공통 고지 |
| 같은 파일 — `CourtComedy` | ‘판사가 본 사정’·긴 비유 설명·하단 반복 띠를 제거하고 표정/휴대폰에 집중. 실제 소품의 ‘증거’는 필요할 때만 | 법원 판단과 단순 비유의 구별 |
| `entry.tsx` — `Video`; `production/compositor/src/v52_candidates/HookRevised.tsx` — `HookV52`; 로컬 `HookV51Seed.tsx` — `EndV51` | 시안에서는 이 컴포넌트들도 복사해 연결. 도입 제목 하나, 결말 가짜 버튼 제거. 전역 원본은 편집하지 않음 | 오디오 중복 방지, hook/end 경계와 전체 길이 |
| `production/compositor/src/theme.ts`, `fonts.ts` | 시안은 기존 Pretendard 700을 재사용하고 STYLE 값만 로컬로 적용. 공유 팔레트·폰트 정의의 전역 변경은 피함 | 다른 에피소드와 실행 중인 렌더 |

`render.json`의 자막과 대본은 **완성 MP4와 먼저 대조**한다. 현재 파일을 읽었다는 사실만으로 그 파일의 모든 문구가 배포 MP4와 일치한다고 가정하지 않는다. 예컨대 녹음의 완료/시도 표현은 문체가 아니라 사실 차이다. 이번 목업은 렌더된 프레임의 실제 자막을 기준으로 만들었다.

`Type2Caption`/`PremiumChoices` 분기는 q014의 현재 일반 `Caption` 분기와 별개다. 전역 교체로 처리하지 않는다. q013의 comedy·`production/compositor/src/v52_n16/QuizPanels.tsx`와 `factory/vendor/QuizPanels.tsx`로의 확산은 이 시안 이후의 별도 변경 대상이다. q020은 이번에는 읽기·목업 대상이며 batch 제작 파일을 수정하지 않는다.

## 롱폼: 공유 Captions와 wrapper

| 기준 파일·함수 | 후속 시안에서 바꿀 내용 | 보존할 것 |
|---|---|---|
| `production/lf_toon/src/Captions.tsx` — `Caption` | proof58/full54, 800, stroke10, 단어 정규식 강조를 STYLE의 56/52, 700, stroke5와 수동 강조로 변경. `layout`별 자막 영역과 두 줄 배치를 명시 | `start <= time < end`, 날짜 숫자 변환, 타임라인 원문, `proof/full` 호출 호환 |
| `production/lf_toon/src/entry.tsx` — `Film` | proof의 사건명·phase·날짜 상시 헤더를 사건/시간 전환 때만. n18 전용 작은 재연 고지를 LF2에도 포함하는 공통 고지로 정리 | `LF2`/`N18`의 연기와 사건 주체. 검찰/경찰 판단 표시가 필요한 구간 |
| 같은 파일 — `loadFonts` | 자막 700은 이미 로드한다. 고지 500이 필요하면 시안에 기존 compositor의 Medium 파일을 복사하고 FontFace를 추가 | 새 폰트 다운로드·설치 없음 |
| `production/lf_toon/src/lf2/entry.tsx`, `src/n18/entry.tsx` — 각 `Film`과 폰트 로딩 | 두 full 엔트리가 공유 `Caption`을 import하므로 **원본 수정 금지**. 후속 시안 복사본만 새 Caption에 연결하고 짧은 재연 고지를 확인 | 실행 중인 `lf-full-*`의 소스·폰트·출력 |

공유 `Captions.tsx` 한 파일을 즉시 고치면 실행 중인 full 렌더까지 영향을 받을 수 있다. 후속 적용은 복사본의 import를 로컬 Caption으로 연결해 비교하는 방식으로 시작한다. 이번 작업에서는 그 복사본이나 코드를 생성하지 않았다.

## 후속 구현에서 볼 장면

q014의 f180(검찰 귀속), f420(선택지), f540(증거 비유), f780(구형/선고), f900(CTA)와 q020 f375(구형)를 비교한다. 롱폼은 두 proof의 행동·숫자·고지 장면을 1080p와 360p로 본다. 실제 발화와 자막 교체, 두 줄 넘침, 안전 영역, 피해자 비식별을 확인한다. 이는 필요한 영상 검토이지 새 자동 게이트 제안이 아니다.

`factory/REVIEW_CHECKLIST.md`의 B2 아래에는 이번 진단을 반영한 **미적용 수동 제안**만 덧붙였다. 기존 B2의 자동 판정이나 서명 요건을 확대하지 않았다.
