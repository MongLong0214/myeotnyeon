# OpenToonz 분석 요약 (2026-11-08)
(하위 에이전트 쓰기가 막혀 CTO가 보고 원문 요약을 저장함. 소스: src/, 커밋 c003fb8c, v1.8.0. 앱 설치·빌드 안 함 — 소스 읽기 기준 판단)

## 정체·라이선스
- 지브리가 쓰던 Toonz를 DWANGO가 공개한 C++/Qt5 GUI 2D 애니메이션 앱. 손그림 작업 전제.
- BSD-3 (thirdparty·MyPaint 브러시는 별도). 코드 이식 시 저작권 고지 유지.

## 헤드리스
- tcomposer CLI(tcomposer.cpp:600-645)로 .tnz 렌더 가능, .toonzscript 실행 가능.
- 스크립트 API는 셀 배치·렌더만, 키프레임·스켈레톤·FX 불가. Homebrew cask는 Gatekeeper로 막힘, pkg는 sudo 필요.
- → 렌더러·합성기로 도입하지 않음.

## 가져올 아이디어 (Remotion TS로 새로 작성)
1. 키별 보간 타입(EaseInOut 사다리꼴, 베지어, 지수, 계단 hold) — tdoubleparam.cpp — S. 현재 motion.ts는 smoothstep 하나라 리듬이 전부 같음.
2. on 2s/3s 포즈 끊어 찍기 + hold — Xsheet 모델(txsheet.cpp) — S. 30fps로 미끄러지는 AI스러운 움직임 제거.
3. 잔상(multiples, iwa_motionblurfx zanzo) + 라인 보일(feTurbulence+feDisplacementMap, seed 3프레임마다) — S.
4. 한글 립싱크: whisper 타임스탬프 → 자모 → Preston Blair 입모양(ㅏ→AI, ㅓㅐㅔㅣ→E, ㅗㅜ→O/U, ㅁㅂㅍ→MBP, 휴지→rest) — S, 입모양 SVG 6–8개 필요. 대안 Rhubarb(MIT) phonetic(한국어 미검증).
5. 아크 모션 패스 카메라·소품(tstageobjectspline.cpp) — S.
6. 몸통 회전: 정면/3·4/측면/뒷면 그림 바꿔 끼우기 + 팔다리 앞뒤 순서 키 — S–M. OpenToonz도 자동 회전 없이 이 방식.
7. ARAP 메시 변형(plasticdeformer.cpp) TS 이식 — L, 보류.

## 못 쓰는 것
앱·렌더러 도입, toonzscript(QtScript deprecated, GUI 필요), 렌더 팜·플러그인 SDK, ARAP 그대로 이식, GTS·MyPaint·Toonz Raster(손그림·스캔), 실사풍 FX.
