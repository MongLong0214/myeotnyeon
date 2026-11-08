# 몇년나옴 — 자막·UI·문장 스타일 제안

2026-11-06. **정적 시안 기준이며 제작 코드에는 미적용.** 아래 수치는 우리 채널의 시작값이다. Extol 실측이나 검증된 최적값으로 인용하지 않는다. 판단 근거는 [진단](DIAGNOSIS.md), 스킬 출처와 상충 규칙은 [조사](SKILLS_DIGEST.md)에 있다.

## 방향

사건을 보는 화면이다. 캐릭터의 행동과 판단을 바꾸는 물건을 크게 보여준다. 문구는 말하듯 쓰고, 법적 주체와 숫자는 정확히 붙인다. 장면의 벽·바닥·조명이 배경이 되며, 영상 전체를 하나의 카드나 종이 띠에 담지 않는다.

1. **장면 하나, 자막 하나.** 상시 사건 제목·회차 배지·비유 해설·출처 띠를 동시에 쌓지 않는다.
2. **강조는 드물게.** 기본 자막은 흰색, 중요한 어구만 한 번 강조한다.
3. **구도가 호흡을 만든다.** 와이드·얼굴·손과 소품·판결 수치를 역할에 맞게 바꾼다.
4. **한국어는 짧고 구체적으로.** 의미 없는 예고·메타 해설·번역투를 덜어낸다.
5. **재연·귀속·비식별은 유지한다.** 작게 정리하되 없애거나 읽을 수 없게 만들지 않는다.

## 자막 규격

| 역할 | Shorts 1080×1920 | 롱폼 1920×1080 |
|---|---|---|
| 기본 서체 | 기존 Pretendard Bold 700 | 기존 Pretendard Bold 700 |
| 기본 크기 | 64px, 긴 구절은 60px까지. 더 줄이기 전에 나눈다 | 56px, 긴 구절은 52px까지 |
| 줄간격·자간 | 1.18 / 0. 최대 두 줄 | 1.18 / 0. 한 줄 우선, 필요 시 두 줄 |
| 글자색 | `#FFFDF6` | `#FFFDF6` |
| 외곽선 | CSS `-webkit-text-stroke:6px #1E1712; paint-order:stroke fill` | CSS stroke 5px, 같은 색과 paint-order |
| 그림자 | `0 2px 3px rgba(30,23,18,.5)` 한 겹 | 동일한 중립색 한 겹 |
| 자막 영역 | x110–870, top1352, 두 줄 포함 y1520 이내 | x180–1740, 한 줄 top900 / 두 줄 top838, 하단 약970까지 |
| 강조 | `#F2C14E` 한 어구. 기본은 강조 없음 | 같은 원칙 |

외곽선 수치는 CSS 전체 stroke 폭이다. 글자 바깥으로 6px씩 더한다는 뜻이 아니다. 두꺼운 검정 덩어리나 여러 겹 그림자를 만들지 않는다. 장면이 밝아도 대비는 확보하고, 단어 뒤 검정 pill을 새로 붙이지 않는다.

자막을 위해 Pretendard를 버리거나 세리프·손글씨·모노를 짝지어 넣지 않는다. Black Han Sans는 필요한 도입 제목 또는 판결 숫자에만 제한적으로 남길 수 있다. 큰 제목도 매 컷 반복하지 않는다.

### 끊기와 호흡

- 한 자막은 한 발화 덩어리다. Shorts 한 줄은 대략 한글 8–11음절부터 배치하되 **실제 폭**을 우선한다. 숫자·라틴 문자·띄어쓰기를 음절 수만으로 판단하지 않는다.
- 조사와 앞말, `검찰 구형`, `항소심 선고`, `징역 6년`을 떼지 않는다. 긴 문장은 세 줄·말줄임표 대신 다음 cue로 나눈다.
- 단어별 튀어나오기·매 단어 색칠·타자 효과를 기본값으로 쓰지 않는다. 발화 구절이 시작할 때 안정적으로 나타나고 끝나면 교체한다.
- 의미가 이어지는 두 cue를 컷마다 억지로 새 문장으로 만들지 않는다. 반대로 자막을 컷 변경 때문에 도중에 지우지 않는다. 음성의 실제 단어 경계가 기준이다.
- 문장이 짧다고 항상 빨리 없애지 않는다. 판결 숫자나 의미를 바꾸는 부정어는 읽는 시간을 준다. 이번 정적 목업은 체류 시간·싱크·전환 검증 결과가 아니다.
- 위치는 장면 시작 때 결정한다. 기본 하단축을 유지하고, 중요한 손·소품과 겹칠 때만 안전 영역 안에서 조정한다. 단어마다 이동·회전하거나 일부러 정렬을 틀지 않는다.

### 강조 단어

정규식으로 모든 숫자·‘반성’·‘집행유예’를 자동 노랑 처리하지 않는다. 해당 장면에서 판단을 바꾸는 어구 하나를 편집자가 지정한다. `20년`만 떠다니게 하지 않고 같은 cue에서 **검찰 구형**임을 읽게 한다. 다음 선고 장면도 `항소심 선고 / 징역 12년`처럼 주체·심급과 함께 보인다. 이 숫자는 q020 원 대본의 예시이며 다른 사건의 기본값이 아니다.

강조가 필요하지 않은 cue는 전부 흰색으로 둔다. 색 대신 인물 표정·손의 행동·중요한 소품의 크기로 강조해도 된다. 색만으로 검찰·법원·가해자·피해자를 구별하지 않는다.

## 제목·고지·라벨

- 도입에는 사건을 이해시키는 제목 하나만 쓴다. 본문에서는 브랜드+회차+사건명+질문을 계속 반복하지 않는다. 질문 화면에서만 선택지를 보여주고, 양형 이유를 설명할 때는 감춘다.
- 재연은 **고정 모서리 한 곳에 ‘보도 기반 재연’**, 시각 비유가 있는 컷은 **‘보도 기반 재연·비유’**로 표시한다. Shorts x110/y200, 30px/500, stroke3px부터. 롱폼 x60/y50, 28px/500부터. 작은 글씨는 얇은 중립색 외곽선으로 대비를 보완한다.
- 이 고지는 ‘시각비유·녹음이 증거로 돌아오다’ 같은 설명 문장과 다르다. 긴 해설 띠는 제거하되 비유임을 알리는 고지는 남긴다. 360p 축소본에서 흐리면 크기를 올린다.
- 법원·검찰·당사자 주장이 혼동되는 컷에서는 짧은 귀속 표시를 자막에 포함한다. 화면의 날짜·장소는 새 시간·장소를 소개할 때만 보여준다. 사실 의미가 달라지는 표시는 미적 이유로 지우지 않는다.
- 설명란에는 `판결·보도를 토대로 재구성했습니다. 인물과 배치는 단순화했으며 실제 현장 영상이 아닙니다.`와 해당 자료·판결 단계·구형/선고 구분을 적는다. 허구 캐릭터·시간 축약·비유 사용의 상세도 여기에 둔다. 화면의 짧은 재연 고지를 대체하지 않는다.

## 장면 구성

그림은 화면 끝까지 갈 수 있고, 말과 핵심 행동은 안전 영역에 둔다. 현재 Shorts 기준의 x110–970, y190–1540과 하단 우측 액션 레일(x880 이후)을 출발점으로 유지한다. 풀 화면으로 키운다는 이유로 중요한 얼굴·증거·구형/선고 라벨을 잘라내지 않는다.

| 장면 역할 | 배치 |
|---|---|
| 행동·충돌 이전 | 공간이 읽히는 와이드. 작은 설명 박스 대신 행동으로 관계를 보여준다 |
| 녹음 등 판단의 단서 | 인물 얼굴과 소품을 크게. 가로 패널을 세로 화면에 그대로 넣는 방식에서 벗어난다 |
| 법원이 본 사정 | 두 사람의 시선·증거·반응이 이어지는 장면. 필요하면 독립 비유 컷으로 전환한다 |
| 구형과 선고 | 심급과 절차를 붙인 수치 하나를 우선한다. 같은 숫자를 헤더·도장·자막에 세 번 쓰지 않는다 |
| 결말 | 여운이나 실제 다음 사건 질문. 유리 카드·가짜 구독 버튼·화살표를 얹지 않는다 |

의도적인 비대칭은 인물·소품의 중요도와 시선 방향에서 나온다. 자막의 정렬 불량·랜덤 회전·새 그레인·낙서·스티커로 ‘사람 손맛’을 흉내 내지 않는다. 장면 안 실제 책상·문·휴대폰의 둥근 모서리는 UI 카드와 구분한다. 정보 비교가 필요한 표는 허용하되 모든 장면의 바깥 틀로 사용하지 않는다.

롱폼 proof는 이미 와이드와 클로즈업이 있으므로 그 구도 변화를 유지한다. 상단 사건명·phase·날짜만 정리하고 자막부터 조정한다. full-bleed 재구도가 필요하면 인물·장소의 의미를 보존한 장면별 작업으로 진행하며, 16:9를 9:16로 단순 잘라 적용하지 않는다.

## 한국어 문장

[humanize-korean 진단 규칙](https://github.com/epoko77-ai/im-not-ai/blob/bad4ef0a2b514318b2278b65cb4545414ad84d82/skills/humanize-korean/references/diagnosis-rules.md)의 A/C/D/E/H/I/J를 영상에 맞게 취한다. 내레이션은 짧은 구어에 가까운 설명체로 쓴다. 롱폼의 `-습니다`를 유지해도 자연스러울 수 있다. 사람답게 보이려고 반말·`-죠`·감탄사를 무작위로 섞지 않는다.

| 덜어낼 표현 | 편집 방향 |
|---|---|
| `검찰에 의해 구형이 이루어졌습니다` | `검찰은 징역 20년을 구형했습니다` — 원자료가 이 수치를 확인할 때만 |
| `그런데 반전은 여기서 시작됩니다` | 다음으로 확인된 사실을 바로 말한다. 새 반전을 만들지 않는다 |
| `주목할 점은 ~라는 점입니다` | 누가 무엇을 판단했는지 바로 쓴다 |
| `시각비유 · 녹음 ≠ 면책`이라는 긴 띠 | 고지는 짧게 유지하고 설명은 현재 발화와 그림에 맡긴다 |
| 제목과 자막이 모두 `선고는 달랐습니다` | 예고는 한 곳만. 실제 선고는 원 대본의 답 공개 시점에 제시한다 |
| `다음 판결도 맞혀보세요 → 구독` | 실제 다음 사건 질문이 있을 때 짧게 한 번. 없으면 장면으로 끝낸다 |

말투를 줄여도 수치·날짜·심급·혐의·판단 주체·부정어·직접 인용을 바꾸지 않는다. 특히 `하려 했다`와 `했다`, `혐의`와 `유죄`, `구형`과 `선고`, `피해 인원`과 `사망자 수`를 서로 바꾸지 않는다. `~로 보인다`가 근거의 불확실성을 담고 있다면 보존한다. 직접 인용은 따옴표를 포함해 그대로 둔다.

## 바꾸지 않는 세 가지

**재연임을 밝힌다. 검찰 구형과 법원 선고·심급을 구분한다. 피해자가 식별되지 않게 한다.** 비유를 실제 사건 물건처럼 보이게 하거나 익명 인물에 실존 인물의 외모·상세 정보를 더하지 않는다. 표정 개그는 가해자의 논리·판단의 모순에 한정하고 피해·사망 자체를 희화화하지 않는다.

## 같은 장면의 전후 시안

모두 **1080×1920 PNG**다. 원본 영상 프레임의 그림을 CSS로 크롭·확대·배치하고 자막과 고지만 새로 조판했다. 두 개의 after가 목업 본체이며 before는 대응 원본 프레임이다. 새 그림·새 사실은 만들지 않았다.

| 장면 | before | after | 보여주는 변경 |
|---|---|---|---|
| q014 f180 / 6.000초 | [원본](../../episodes/review_full/unslop/mockup_01_recorder_before.png) | [녹음 장면](../../episodes/review_full/unslop/mockup_01_recorder_after.png) | 얼굴·휴대폰 확대, 상시 제목·설명·중복 출처 제거, 고지 한 곳, 흰 자막 |
| q020 f375 / 12.500초 | [원본](../../episodes/review_full/unslop/mockup_02_demand_before.png) | [구형 장면](../../episodes/review_full/unslop/mockup_02_demand_after.png) | 베이지 띠·`#N`·중복 예고 제거, ‘검찰 구형’과 형량을 한 cue로 조판 |

[나란히 비교 1](../../episodes/review_full/unslop/compare_01_recorder.png), [비교 2](../../episodes/review_full/unslop/compare_02_demand.png). 크롭과 토큰은 [mockup_layout.json](../../episodes/review_full/unslop/mockup_layout.json)에 기록했다. 6초 자막은 원래 이어지는 문장의 중간 cue이므로 다음 cue에서 검찰 판단의 문장을 끝내야 한다. 기존 비트맵 확대라 그림이 부드러워지며, 실제 적용에서는 원 벡터 장면을 새 구도로 렌더한다. 정적 시안으로 전체 영상의 가독성·음성 싱크가 검증된 것은 아니다.

## Owner correction (2026-11-06): subtitle legibility
Owner's words: "자막 가독성 더 높이고 가로중앙 정렬해" (make the subtitles more legible and center them horizontally).
- **Centered horizontally:** every subtitle line is centered on the canvas (text-align center, the box center = the canvas center). No left or right offset.
- **Legibility up:**
  - Shorts: font size at least 64 px.
  - Long-form: font size at least 52 px.
  - Weight 800 or more; white text with a black outline of at least 8 px (Shorts) or 6 px (long-form) plus a soft shadow.
  - At most 2 lines; at most 14 characters per line on Shorts.
  - Fixed position: the safe area at about 62–70% of the canvas height on Shorts, where no character's face is covered.
  - Highlight color: one phrase only, high-contrast yellow (#FFD400 family).
- "Thin subtitles" in the previous rule means **few visual layers** (no boxes or strips), **not thin type**.
- Line breaks at meaning boundaries; never cram a long sentence into one line. Keep the safe area (CEO, 11-06).
# Addendum (owner direct instructions, 11-06 12:00, take precedence over all existing rules)

- Courtroom and sentencing scenes: as dynamic as possible.
  - Cut every 1–1.5 s with camera moves.
  - The judge, defendant and victim act and react.
  - Sentencing factors hit the screen like a stamp, and the scales tip.
  - The answer lands with a gavel and an impact.
- **No faces without eyes, nose and mouth.** Victims get an original toon face with expressions (no resemblance to the real person).
- **No Blender or 3D opening and ending footage.** Toon only.
- **No on-screen disclosure captions or corner labels** ("재구성", "시간 압축", "시각비유", the series corner mark). Disclosures go in the description only. The demand-vs-sentence distinction is a fact, not a disclosure, so it stays.
- A/B/C choices: big, colored, timed pop-ins plus a countdown or comment prompt; on the answer reveal the correct card lights up and the others go dim.
# Addendum (owner direct instruction "릭앤모티 연출법들 적극참고해" — actively borrow Rick and Morty's directing techniques; takes precedence). Continue.

Borrow **only the directing grammar**. Do not copy characters, designs, catchphrases or logos — original characters only.
- **Smash cuts:** cut abruptly at the climax of an action into the reaction or the result. Use hard cuts, not soft transitions.
- **Snap zooms:** a 2–4 frame sharp zoom onto a face at the moment of shock.
- **Deadpan beat:** a 0.3–0.5 s hold right after a big impact (a frozen expression, sweat), then the next cut.
- **Squash and stretch:** exaggerated deformation of the head and body at impact; whole-body acting when shocked.
- **Rapid reaction chain:** cut back and forth between the attacker's expression ↔ the victim's expression ↔ the judge's expression within 1 second.
- **Extreme expressions:** jittery pupils, bulging eyes, sweat beads, twitching mouths, veins (a cartoon-style exaggeration).
- **Background gag details:** small, fun visual details in the set. Never mock the victim or a death.
- Courtroom: the judge's line and the defendant's reaction exchange like the rhythm of a sitcom gag.
- Victims, deaths and injuries are not gag material. Comic exaggeration is for the defendant's attitude and for visual metaphors only.
# Addendum (Rick and Morty reference research findings; source: W/references/rick_and_morty/RM_DIRECTING_REFERENCE.md). Continue.

- **Animatic first:** lock shot order and timing in a rough pass first, cut out the dead air, then polish. Final QA: no "weird cuts or strange staging" (R&M director Erica Hayes).
- **Write the line flat, exaggerate the reaction:** one exaggerated reaction beat per key line (a gavel flinch, a side-eye, a sweat drop) (Harmon/Marder).
- **Reused rigs: vary timing, not shape.** Get dynamism from hold lengths and cut timing; keep one consistent house style.
- Courtroom: smash-cut the dead beats (under 0.5–1 s of "nothing happening"). Never hold one framing more than 2–3 s; rotate wide → medium → close → over-the-shoulder.
- Answer/sentence reveal: a 2–4 frame snap zoom → a 0.5–1 s deadpan hold.
- **A/B/C choices:** each option gets its own snap-zoom beat of about 0.3–0.5 s with a distinct sound effect and pose. The choice screen is **the longest deliberate hold in the piece** (the climax of suspense).
- Investigation, evidence and procedure: a 3–6 shot quick montage, 0.5–1 s per shot.
- Violence: cut away at the impact and show the reaction or aftermath. Do not linger.
- Give each reused character a signature micro-gesture (e.g. the judge adjusts his glasses before a ruling).
- There is no published R&M cuts-per-minute figure; set our own targets from our own data.
- Editing rhythm (owner 11-06 "너무 편집감이 빨라"): base shot 2–3 s; cut only at line boundaries; use snap zoom and smash cut only at key moments. This overrides the earlier "cut every 1–1.5 s" rule.

## Motion numbers와 living ban list (2026-11-07)

현재 오너 규칙: **Shorts 자막은 가로 중앙(x=540)·72px**, 기본 샷 2–3초, 인물은 계속 연기, 모든 얼굴에 눈·코·입, Blender·3D 금지. 위의 과거 60/64px 시작값·비중앙 배치·화면 고지·급속 컷 제안보다 최신 오너 지시와 REVIEW_CHECKLIST A1–H14가 우선한다. 수치 구현 지시는 [MOTION_NUMBERS.md](MOTION_NUMBERS.md)를 따른다. 이 추가는 제작 코드에 적용됐다는 뜻이 아니다.

| 금지 패턴 이름 | 대체 지시 |
|---|---|
| **fade-and-slide-up on every element** | 모든 요소에 같은 진입 프리셋을 반복하지 않는다. 샷 hero 1개에 행동 목적과 곡선을 지정한다 |
| **everything appearing at once** | hero 우선, secondary는 3–6f 뒤·이동량 50–70%. 선택지는 beat별로 순서대로 등장 |
| **text that moves while it is read** | 진입이 끝난 뒤 읽기 hold를 센다. 자막·선택지 좌표/크기/회전 고정; 2% push는 장면에만 적용 |
| **decorative glow, gradients and particles** | 장식용 glow·gradient·particle 제거. 중요한 행동·표정·소품으로 강조하며 정답 카드도 장식 glow 대신 색/명암으로 강조 |
| **linear easing on character moves** | 인물 진입 ease-out, 퇴장 ease-in, 위치 이동 ease-in-out, 반동 ζ 0.3–0.6. ambient의 선형 시간 위상은 좌표 선형 보간과 구분 |
| **unanchored interview props** (LF3 첫 러프 f1600·f2600) | 설치 파일과 가면이 화면 옆에 따로 떠서 소품과 인물의 관계가 끊겼다. 설치 파일은 노트북 화면 안에 두고, 면접의 가면은 얼굴 가장자리 들림으로 표현한다. 완전히 분리된 가면은 벗기는 행동 뒤에만 쓴다. 기술 비유용 독립 공간과 실제 작업실 소품을 구분한다 |
| **centered-everything layouts** | 모든 인물·소품을 중앙에 쌓는 기본 구도를 피한다. **오너 규칙인 자막 가로 중앙 정렬은 명시적 예외이며 반드시 유지한다** |

각 lane은 **매 첫 렌더 뒤**, 실제로 발견한 새 모델 기본 패턴을 이름으로 이 표에 추가하고 해당 shot/frame과 대체 지시를 붙인다. 새 패턴이 없으면 항목을 꾸며내지 않는다. 현재 작업에서는 렌더하지 않았으며 새 발견을 주장하지 않는다. H10의 선택지 카드는 질문 구간에만 허용하며 상시 UI 카드 금지를 해제하지 않는다.

## 2026-11-07 — 두 MIT 저장소에서 취한 자막·훅 규칙

**원일 규칙이 우선한다.** Shorts 자막은 캔버스 가로 중앙, **72px·weight 800·검정 외곽선 8px 이상**, 최대 2줄·줄당 14자 이하로 쓴다. 기존 Pretendard를 유지한다. 위의 초기 64/60px·700·6px 제안은 이 Shorts 기준으로 대체한다. 기본 샷은 **2–3초**, 대사 중간 컷은 피하고 샷 안 행동·반응으로 역동성을 낸다. 이 절은 문서 규칙이며 제작 코드 변경은 아니다.

### 채택

- 무음에서도 사건과 질문이 읽히게 한다. 첫 행동과 짧은 질문을 함께 설계하되 질문은 음성에 맞는 자막 한 벌로 보여준다. 별도 제목·설명·출처 띠를 쌓지 않는다. 예시는 [HOOKS](HOOKS.md)에 있다.
- 흰 글자와 검정 외곽선으로 대비를 확보하고 배경 pill·박스는 쓰지 않는다. 한 발화 구절을 안정적으로 표시하고 실제 음성 경계에서 바꾼다. 단어별 바운스·타자 효과 대신 인물의 연기로 시선을 이끈다.
- 긴 문장은 의미 단위로 나눈다. 조사·부정어·‘검찰 구형’·‘항소심 선고’·형량을 잘라 뜻을 바꾸지 않는다. 얼굴·손·핵심 소품과 플랫폼 UI를 피하되 가로 중앙 정렬은 유지한다.
- 강조색은 편집자가 고른 중요한 어구 하나에만 드물게 쓴다. 숫자마다 자동 색칠하지 않는다. 한국어는 주체와 행동을 바로 말하고 ‘그런데 진짜 반전은’, ‘결과는? 바로…’ 같은 빈 예고·자문자답·과장 문구를 덜어낸다. 실제 판결을 묻는 질문은 유지한다.
- 첫 질문과 다음 발화가 같은 사건·쟁점을 이어가게 한다. 답은 영상 안에서 회수하고, 구형·선고·심급·혐의와 판단의 구분을 자막에서도 보존한다. 재연 고지는 기존 H9대로 설명란에 둔다.

### REJECTED — 읽은 범위에서 우리 규칙과 충돌하는 권고

경로 약칭: **M** = `coreyhaines31/marketingskills`, **Y** = `AgriciDaniel/claude-youtube`. 정확한 경로와 MIT 표기는 [THIRD_PARTY](../THIRD_PARTY.md#hook-and-caption-distillation--2026-11-07)에 있다. 특정 광고 형식의 권고를 우리 기본값으로 옮기는 경우도 아래처럼 제외한다.

| 판정 | 외부 권고·위치 | 이유와 우리 적용 |
|---|---|---|
| REJECTED | M `ad-creative/references/short-form-video-specs.md`: TikTok Sans·weight 700, 약 58px부터 26px까지 자동 축소, 긴 벽자막 허용 | Pretendard·72px·800을 유지하고 문장을 나눈다. 작은 글씨로 밀어 넣으면 가독성이 떨어진다 |
| REJECTED | 같은 파일: 자막 시작·끝을 영상 세그먼트와 반드시 일치 | 자막은 발화 구절과 음성 경계를 따른다. 컷 때문에 문장을 지우거나 늘이지 않는다 |
| REJECTED | 같은 파일: 모든 핵심 요소를 고정 720×1200 크로스플랫폼 밴드에 배치; 모든 소스를 중앙 크롭 | 채널의 중앙 정렬·안전 영역과 장면 의미가 우선이다. 다른 화면비를 일괄 잘라 얼굴·행동·귀속을 잃지 않는다 |
| REJECTED | M `ad-creative/references/hook-system.md`: 행동·음성·caption은 절대 같은 내용을 반복하지 않음 | 접근성을 위해 자막은 음성을 충실히 전달한다. 제거 대상은 중복 헤더·장식 라벨이다 |
| REJECTED | 같은 파일의 별도 hook header/overlay, Y `retention-scripting-guide.md`의 text pop-ups/lower thirds | 자막 한 벌과 필요한 선택지 외에 상시 헤더·메타 라벨·고지 층을 더하지 않는다(H4·H9) |
| REJECTED | M `ad-creative/SKILL.md`의 word-timed captions를 매 단어 교체·색칠로 적용하는 해석 | 타임스탬프는 싱크에만 쓴다. 매 단어 강조는 AI 템플릿처럼 보인다. 원문이 단어별 색칠을 직접 권한 것은 아니다 |
| REJECTED | M `short-form-video-specs.md`의 0.5–1초 컷 공식, `social/references/short-form-video.md`의 1–3초 quick cuts를 기본값으로 적용 | 기본 2–3초와 H14가 우선이다. 1.2초 미만 컷은 핵심 임팩트에만 제한한다 |
| REJECTED | Y `retention-scripting-guide.md`의 2–3초마다 interrupt, `sub-skills/shorts.md`의 3초마다 visual change를 의무 컷·팝업으로 적용 | 샷 안 행위·반응의 변화로 취할 수 있다. 대사 중간 컷·의미 없는 흔들기·화면 장식을 강제하지 않는다 |
| REJECTED | Y `sub-skills/hook.md`의 완전한 30초 훅·약 75단어, 다른 파일의 0–3/5/30초 도입을 그대로 사용 | 우리 훅은 행동과 질문을 0–2초에 전달한다. 30초 예고나 긴 도입으로 본문을 늦추지 않는다 |
| REJECTED | Y `hook.md`의 shock claim ‘no hedging’, M `copywriting/SKILL.md`의 confident over qualified를 사실의 유보까지 제거하는 데 적용 | 혐의·주장·불확실성을 지우지 않는다. 사실 정확성이 자신감 있는 말투보다 우선이다 |
| REJECTED | Y `hook.md`의 problem-agitation·고통 증폭, M `social/.../short-form-video.md`의 비밀·논란·hack 문구를 사건에 그대로 이식 | 미확인 사실·감정·동기와 피해 희화화를 만들 수 있다. 확인된 행동과 법원 판단을 묻는다 |
| REJECTED | M `hook-system.md`의 proof-first 결과 선공개, `social/.../short-form-video.md`의 결과 예고를 형량 정답 공개로 적용 | 형·형량 정답은 H2의 마지막 구간에 둔다. 첫 화면은 행위와 질문이다 |
| REJECTED | Y `shorts.md`의 끝 1–2초 seamless loop 의무, Y retention의 이중 CTA·‘Join the family’, M social의 고정 3–5초 CTA/end card | 템플릿 엔딩·가짜 구독 UI·답을 흐리는 루프를 만들지 않는다. 다음 사건을 볼 실제 이유가 있을 때 짧게 연결한다 |
| REJECTED | Y retention의 Shorts 15–30초 최적값, `shorts.md`의 13/60초 sweet spot·30–45초 dead zone | 서로도 다른 일반론이다. H5대로 판결 이유를 보존하며 우리 데이터로 비교한다 |
| REJECTED | Y retention의 보편적 유지율·전환 상승 수치와 AI 내레이션 70% 감소 단정, `shorts.md`의 예측 viewed 60% PASS 기준 | 우리 채널 실측·검증 기준이 아니다. 추정으로 합격·승자를 만들거나 기존 음성을 교체하지 않는다 |
| REJECTED | M `social/.../short-form-video.md`의 하루 최대 3회 게시 확장, 고조회·부정 댓글 뒤 논란 강화 | G1의 하루 1회 제한과 사실·피해자 보호가 우선이다. 조회수만으로 구독 전환 성과를 확정하지 않는다 |

M copywriting/ad-creative의 anti-slop 원칙은 사실에 근거한 짧은 한국어에 적용한다. 영어 문장 장치 금지를 기계적으로 옮겨 실제 질문·직접 인용·판단의 유보를 지우지 않는다. 외부 성과 수치는 새 목표나 자동 게이트로 채택하지 않는다.
