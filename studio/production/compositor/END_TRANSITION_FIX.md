# End transition: RED → GREEN

2026-10-31. 모든 프레임은 0부터 시작한다. 작업과 임시 파일은 W 안에만 생성했다. 네트워크·업로드·전체 영상 재렌더 없이 경계 PNG만 렌더했다. 기존 영상과 production의 `render.json`은 수정하지 않았다.

## 원인 — 확인된 사실

- v3의 `src/Root.tsx`의 `Q003` 등은 `Quiz`를 사용한다. v52 최종본의 진입점은 `src/v52/indexFinal.ts` → `RootFinal.tsx`의 `V52-Q012/Q015/Q016/Q017`이다. f60 이후 `Quiz hookStyle="v51"`로 이어진다.
- `Quiz.tsx`의 `R`이 `reveal`의 판사/판결 화면, `reason`의 이유 패널, `outro`의 패널 엔드 카드를 선택한다. q003의 직전 장면은 판사 그림이 아니라 `Reason`이다. v52 네 편의 직전 장면은 `Reveal`이다.
- 문제의 주차장은 하위 장면 누출이 아니다. **`Outro` 자신이 `<NightLot glow={0.5}/>`를 즉시 그린다.** 구현은 `src/components/toon.tsx`의 `NightLot`이다. 이것은 v52 `EndV51`의 사진 배경과도 별개다.
- 원래 `Sequence`는 `[c.from, c.from+c.dur)`에 표시된다. 직전 장면 종료와 outro 시작은 데이터에서 인접한다. 시퀀스 사이에 빈 프레임이 있는 문제가 아니다.
- 그러나 v3의 outro 문구에만 `usePop(a.s1, 11)` 기반 opacity가 적용된다. 배경에는 적용되지 않는다. q003은 `outro.from=871`, `a.s1=3`이므로 f871–874에는 문구가 0이고 f875–878은 부분 투명하다. 카드가 처음 완전히 불투명해지는 프레임은 f879다. 직전 `reason`은 이미 f871에 사라진다.
- v52의 전체 화면 `EndV51`은 `doc.durationInFrames-45`에서 별도 early return으로 시작한다. 이는 기존 outro 시작과 다르다. v52 제작 스크립트 `episodes/quiz/v52_support/prepare.py`는 내레이션 앞 4프레임을 cue 시작으로 사용한다. `final_docs.py`는 마지막 길이도 조정한다. 따라서 기존 outro가 먼저 노출되고, 나중에 전체 화면 카드가 덮는다. q015 최종본은 N=705로 짧아져 차이가 1프레임이다.

| 최종본 | 마지막 콘텐츠 표시(수정 전, 끝 제외) | 기존 outro 시작 | 전체 화면 카드 시작 | 잘못 끼는 기존 outro |
|---|---|---:|---:|---|
| v52_q012 | Reveal [811,917) | 917 | 967−45=922 | f917–921 |
| v52_q015 | Reveal [523,659) | 659 | 705−45=660 | f659 |
| v52_q016 | Reveal [672,841) | 841 | 890−45=845 | f841–844 |
| v52_q017 | Reveal [503,623) | 623 | 672−45=627 | f623–626 |
| v3_q003 | Reason [714,871) | 871 | 해당 없음 | f871–874 배경만, f875–878 불완전 카드 |

CTO가 확인한 5건을 원래 소스의 경계 렌더에서 재현했다. 기존 `upload/` 영상의 동일 경계도 디코딩해 `end_fix_check/original_*.jpg`에 남겼다. 현재 코드/데이터와 원본에서 이 현상이 일치한다. 디코딩 원본과 새 PNG 사이의 픽셀 동일성을 주장하지는 않는다(H.264 및 축소 경로가 다름).

## 수정

- `src/endTransition.ts`: 순수 함수 `getEndTransition`에서 카드 준비 시점과 실제 장면 표시 범위를 함께 계산한다. 입력 cue와 내레이션 앵커는 변경하지 않는다.
- v3: 기존 spring과 동일한 fps/config로 카드 opacity가 처음 1 이상인 시점을 구한다. 직전 콘텐츠의 표시 종료와 outro의 표시 시작을 그 시점으로 맞춘다. q003은 Reason을 f878까지 유지하고 f879에 준비된 엔드 카드로 전환한다. 초기 문구 fade 구간을 건너뛰는 것이 의도한 동작 변경이다.
- v5/v51/v52: 직전 콘텐츠를 기존 전체 화면 카드 시작점까지 유지한다. 해당 스타일에서는 중간의 패널 outro를 표시하지 않는다. 기존 `EndV5/EndV51` 시작과 애니메이션 기준점은 그대로다.
- `Quiz.tsx`: 패널, type2 전체 화면 여부, type2 장면에 같은 표시 범위를 적용한다. `Sequence`의 로컬 프레임 원점은 원래 `c.from`으로 유지하고 표시 조건과 종료만 바꿔, 기존 텍스트·애니메이션 앵커를 보존한다.
- `tests/endTransition.spec.ts`, `package.json`: 회귀 검사와 `npm run test:end-transition`을 추가했다. 알 수 없는 scene 조회를 반영해 `R`의 타입도 `Partial<Record<...>>`로 바로잡았다.

배경 자산 교체나 색상 덮기로 해결한 것이 아니다. **이전 콘텐츠 종료와 실제 엔드 카드 시작을 하나의 인계 시점으로 일치시켰다.** 기존 음성·자막·전체 길이와 이미 저장된 영상은 그대로다. 일반 v3 엔드 카드에 원래 포함된 주차장 배경은 문구가 준비된 뒤에는 계속 보인다.

검토용 소스 diff: [end_fix_check/source.diff](end_fix_check/source.diff). 원래 소스: `end_fix_check/before_source/src/`.

## RED / GREEN

먼저 원래의 `from/dur` 표시 로직을 함수로 추출한 상태에서 검사했다. 이 단계에서는 표시 범위를 고치지 않았다. 별도의 before 렌더는 추출 전 원래 `Quiz.tsx` 사본을 사용했다.

- RED: **30개 중 29개 실패, 정상 정렬 fixture 1개만 통과**, exit 1. [test_red.txt](end_fix_check/test_red.txt)
- GREEN: **30개 모두 통과**, exit 0. [test_green.txt](end_fix_check/test_green.txt)
- 현재 public의 v3 17개, v5/v51/v52 각 4개 및 정상 정렬 불변 검사를 포함한다.
- 각 outro 직전부터 영상 끝까지 프레임별로 콘텐츠 또는 준비된 카드가 있는지, 전체 화면 카드 전에 기존 outro가 표시되지 않는지 확인한다. 파일 수나 문서 형식 검사가 아닌 실제 표시 동작 검사다.
- `./node_modules/.bin/tsc --noEmit`: exit 0. [typecheck.txt](end_fix_check/typecheck.txt)는 오류가 없어 빈 파일이다.

## 경계 검증

실제 `Quiz` 컴포넌트와 각 최종 production JSON을 사용했다. v52 wrapper는 해당 구간에서 `Quiz hookStyle="v51"`와 동일하다. 검증 진입점은 훅 구간을 포함하지 않는 `EndBoundary`다. 오디오는 `null`로 둔 무음 PNG 검사이며 오디오 렌더를 하지 않았다.

Remotion `renderFrames`, scale=.25, **270×480**, 모든 프레임을 연속 렌더했다. 아래 범위만 before/after 각각 검사했다(총 231장씩). 프레임마다 픽셀 배열을 비교하고 스트립 7개를 직접 검토했다. 붉은 프레임 라벨은 변경된 프레임이다.

| 대상 | 렌더 범위(양끝 포함) | 변경 프레임 | 다른 경계 프레임 |
|---|---|---|---|
| [v3_q003](end_fix_check/strip_v3_q003.jpg) | f856–886 (31장) | f871–878 | 픽셀 동일 |
| [v52_q012](end_fix_check/strip_v52_q012.jpg) | f902–937 (36장) | f917–921 | 픽셀 동일 |
| [v52_q015](end_fix_check/strip_v52_q015.jpg) | f644–675 (32장) | f659 | 픽셀 동일 |
| [v52_q016](end_fix_check/strip_v52_q016.jpg) | f826–860 (35장) | f841–844 | 픽셀 동일 |
| [v52_q017](end_fix_check/strip_v52_q017.jpg) | f608–642 (35장) | f623–626 | 픽셀 동일 |
| [정상 정렬 fixture q012](end_fix_check/strip_aligned_control_q012.jpg) | f902–932 (31장) | 없음 | 31장 전부 픽셀 동일 |
| [정상 정렬 fixture q017](end_fix_check/strip_aligned_control_q017.jpg) | f608–638 (31장) | 없음 | 31장 전부 픽셀 동일 |

변경된 22개 프레임 모두 이전 콘텐츠가 유지된다. 같은 에피소드의 주차장 프레임을 기준으로 상단 패널의 고정 ROI도 비교했다. 수정 전에는 기준과 MAE<10, 수정 후에는 MAE>25다. 이 수치는 해당 경계의 보조 확인이며 다른 에피소드를 확정하는 범용 탐지기로 사용하지 않는다. 픽셀 결과/ROI 수치는 [boundary-results.json](end_fix_check/boundary-results.json), 요약은 [pixel-compare.txt](end_fix_check/pixel-compare.txt)에 있다.

### 정상 대조군의 한계

**요청한 실제 정상 에피소드 2개는 확보하지 못했다.** 현재 public의 v3/v52 데이터는 모두 동일한 선행 outro 문제를 가진다. 후보 v3_q001 f733–736, v3_q004 f739–742도 원본에서 배경만 나오는 것을 직접 확인해 정상 대조군에서 제외했다. 증거: [q001](end_fix_check/rejected_control_v3_q001.jpg), [q004](end_fix_check/rejected_control_v3_q004.jpg).

따라서 q012/q017의 복사본에서 `durationInFrames=outro.from+45`, `outro.dur=45`로 정상 정렬한 **합성 데이터 대조군**을 사용했다(원본 JSON은 수정하지 않음). before 렌더에서 깨끗한 전환임을 먼저 확인했고, after와 62프레임 모두 픽셀 동일했다. 이는 정상 정렬 입력의 무변경 증거이며, 이미 게시된 정상 영상 2편을 검증한 결과로 해석하면 안 된다. 실제 정상본을 지정받으면 해당 경계의 추가 비교가 필요하다.

렌더 종료 시 offline Chromium adapter에서 `Target.closeTarget` 정리 경고가 기록됐지만, 두 프로세스는 exit 0이고 231장씩 모두 생성·비교됐다. 전체 영상에 대한 무변경/오디오 품질 검증을 수행했다는 뜻은 아니다.

## CTO가 원본 실제 프레임으로 확인할 목록

- 기존에 확정된 v3_q003 및 v52_q012/q015/q016/q017: 위 표의 경계. 이번 변경은 템플릿 수정이며 이미 게시된 파일을 교체하지 않았다.
- **heuristic hit는 미확정 유지:** v3_q005 f869, v3_q007 f967, v3_q009 f1080. 데이터 검사로 위험을 예측할 수 있지만 이번 작업에서 이 세 원본 프레임은 판독하지 않았다. CTO의 실제 프레임 확인 전 확정 목록에 넣지 않는다.
- 추가로 이번에 로컬 원본 확인한 v3_q001 f733–736, v3_q004 f739–742: 게시본과 같은 파일인지 CTO 확인 권장. 정상 대조군으로 사용하면 안 된다.
- 나머지 v3_q002/q006/q008/q010/q011/q012/q013/q014/q015/q016/q017 및 v5/v51: 현재 템플릿/데이터상 같은 위험이 있어 게시 여부에 맞춰 실제 원본 경계 확인 권장. 원본 판독 전에는 확정하지 않는다. 특히 `upload/v3_q006.mp4`는 1195프레임인데 현재 public q006은 998프레임이므로 현재 JSON의 프레임 번호를 과거 게시본에 적용하면 안 된다.

의도·유입 경로에 관한 추정: NightLot은 초기 교통 사건용 그래픽을 공통 outro로 재사용한 흔적으로 보이지만, 그 선택의 의도/담당자는 확인하지 못했다. W는 Git 저장소가 아니어서 CommitLore 기록도 조회 불가였다. 이 추정은 위의 재현·수정 근거에 사용하지 않았다.

## 재현 명령

`production/compositor`에서 실행한다. 설치된 패키지만 사용하며 네트워크는 필요 없다.

```sh
npm run test:end-transition
./node_modules/.bin/tsc --noEmit
TMPDIR="$PWD/end_fix_check/tmp" node end_fix_check/render-boundaries.cjs before
TMPDIR="$PWD/end_fix_check/tmp" node end_fix_check/render-boundaries.cjs after
python3 end_fix_check/compare-boundaries.py
python3 end_fix_check/extract-originals.py
```

`before_source/src/Quiz.tsx`는 원래 코드이고 after는 현재 production 소스다. PNG는 `end_fix_check/before/`, `after/`; 스트립은 `end_fix_check/strip_*.jpg`에 있다. 재생성 가능한 대용량 bundle과 임시 Chromium 파일은 검증 후 제거했다.
