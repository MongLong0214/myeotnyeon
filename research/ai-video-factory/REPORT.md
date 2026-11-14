# AI-Video-Factory (ersinkoc) 분석 요약 (2026-11-08)
(하위 에이전트 쓰기가 막혀 CTO가 요약 저장. 커밋 47aa05a, v0.4.6, MIT © 2026 Ersin KOÇ. 클론 src/, 무료 데모 렌더 preview_out/, vitest 595/596 통과(실패 1 Windows 전용))

## 정체
Claude 에이전트가 대본·SVG 캐릭터를 만들고 Remotion으로 렌더하는 TS 모노레포(약 36,000줄). vector 모드는 우리 lf_toon과 같은 계열. TTS는 Gemini/ElevenLabs(유료)뿐, 에이전트는 Claude Agent SDK(과금) → 통째 도입 불가, 부품만 이식(파일에 MIT 표기 + LICENSE 사본).

## 도입 후보 (노력)
- 손·팔: 2-본 IK video/src/ik.ts (S), 관절 한계 클램프 anatomy.ts — strain 목록을 게이트 사유로 (S), 손목 롤 Vector.tsx handRoll l.436 (S–M), 개인 공간 keepInSpace l.1252 (M), 책상 높이 IK deskArm l.305 (M)
- 연기: 전완 지연 0.08초·최소 상승 시간 motion.ts (S), 표정 테이블·눈썹 좌우 분리 EXPRESSIONS l.521 (S/M), **대기 포즈·리스너 연기(체중 이동, 손 비비기, 팔짱, 듣는 사람이 화자 쪽으로)** Vector.tsx l.1299-1318 (M), 음성 비트 제스처 beats.ts (S, 한글 음절 세기 수정 필요), 첫 샷 빌드인 entrance.ts (S)
- 립싱크: visemes.ts/mouthShape.ts (M, 한글 자모 매핑 새로 작성)
- 카메라·정적: 삼각대 흔들림·모션블러 lens.ts (S), 전환 순환 cut.ts (S), 같은 샷 크기 연속 방지 pipeline/src/variety.ts (S), 클로즈업 자동 프레이밍·소품 매크로 인서트 (M–L), 원형 확대 인셋 callout.ts (M), 말풍선 bubble.ts (S–M, 한글 폭 수정), 조명 워시 light.ts (S)
- 자막: 무음 기반 단어 정렬 align.ts (M, whisper 교차검증용). 분할 자체는 얻을 것 적음
- 처리량: 스테이지 재개 개념 (S–M), **장면 청크 렌더 캐시 chunks.ts/render.ts — 바뀐 장면만 재렌더** (M), 코드 lint 게이트(얼굴 잘림·가림·관절 튐·관통) lint.ts (M)
- 패키징: Short 구간 보정 short.ts (S), 썸네일 프레임 점수 thumbnail.ts (S), 훅 프롬프트 문구(콜드오픈, 60–90초마다 재훅)

## 불가
유료 media-gateway, Agent SDK 런타임, likeness·Wikimedia 인물 참조(실존인물 캐리커처, 기본 realism:true), 3D 전부, ComfyUI 사진풍, GSAP(MIT 아님), DB·S3·Redis·Studio·Trigger.dev(과설계), 영어·터키어 전용 모듈.
