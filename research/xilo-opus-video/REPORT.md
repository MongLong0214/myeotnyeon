# xilo-opus-video 분석 요약 (2026-11-08)
(하위 에이전트 쓰기 차단으로 CTO가 요약 저장. MIT © 2026 周行(Kianzzz). 클론 src/, 데모 demo/. 15개 파일 907줄 전수)

## 정체
중국어 Claude Code 스킬. HTML render(t) → Playwright 프레임 캡처 → ffmpeg. 규칙 문서 + Python 도구 4개. 대부분 x-seeconvm·cinecode와 겹침. 코드엔 유료·네트워크·비밀값 없음(문서 권고의 edge-tts·유료 영상 모델은 제외).

## 조정자 지적 검증
- normalize(1패스): 데모 −17.0 LUFS·TP −0.9로 자기 목표 미달 → 우리 2패스(±0.2 LU)가 낫다.
- 360px 시트·컷 검출: 이미 있음(phone_check, format_v4 analyze).
- spring(): motion.ts:95에 동일 공식 있음.
- 2.5초 노출: 화면 속 강조 문구에만. 내레이션 자막엔 안 맞음.

## 새로 쓸 것 (모두 S)
1. 용도별 스프링 4단계 프리셋 + 목표 중첩식 v0+Σ(vi−vi−1)·spring(t−ti) → motion.ts
2. 파형·스펙트럼 PNG(showwavespic/showspectrumpic)를 오디오 증거로
3. 최악 3개+시각 → Remotion --frames=a-b 부분 재렌더, 회차 상한 3(점수 자기평가 제외)
4. cue 시각 SFX 합성기(impact·whoosh·riser·tick) — 에셋 없는 채널용
5. 기획 방안 3개(안전/화풍 변경/서술 구조 변경: 관통 주인공·원테이크·역순·단일 비유)
6. 기본 스타일 회피 목록(어두운 배경+가운데 큰 글자+전부 페이드)
7. UI 요소 좌표 기록 후 카메라를 실제 버튼으로 미는 방식(Remotion React UI로 구현) — M

## 안 쓸 것
render.py(Remotion 중복), 1패스 normalize, numpy 비트 추적기(120 BPM을 184.6으로 오판), 녹색 배경 인물 영상 모델(유료·실사), edge-tts(외부 전송), Manim·Three.js·WebGL.
