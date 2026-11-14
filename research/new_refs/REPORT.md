# 신규 참고 프로젝트 조사 (2026-11-08)

후보 15개를 평가하고 5개를 클론해 N18 영상에 직접 돌려 확인했다. 하위 에이전트의 쓰기가 막혀서 CTO가 요약해 저장한다.
- 클론: `research/new_refs/{kiwipiepy,imgutils,rapidocr,rhubarb,dragonbones}/src` (로컬 전용, 재배포 금지)
- 데모: `research/new_refs/{kiwi_demo,hand_demo,ocr_demo}.py`
- 환경: `research/new_refs/.venv`

| 순위 | 후보 | 라이선스 | 해결 | 검증 | 판정 |
|---|---|---|---|---|---|
| 1 | kiwipiepy | Apache-2.0 | 자막 줄바꿈을 품사로 판정 | 실행함. 문장당 5.5ms, 띄어쓰기 복원 정확 | 도입. captions.py 판정부 교체 |
| 2 | deepghs/imgutils detect_hands | 코드 MIT / 가중치 OpenRAIL | 손 기형 검수 후보 자동 추출 | 실행함. 신뢰도 0.36–0.72, 2.8초/프레임 | 도입. 손이 모자라거나 신뢰도 0.35 미만이면 크롭 시트 생성. 불합격 판정이 아니라 후보 추출용 |
| 3 | RapidOCR PP-OCRv5 한국어 | Apache-2.0 | 글자 잘림 박스 판정 | 실행함. 0.2초/프레임, 띄어쓰기 누락 있음 | 보조로 도입. Apple Vision과 교차검증 |
| 4 | Rhubarb | MIT | 입모양 깜빡임 | 실행함 | 규칙만 자체 구현. 최소 2프레임, 짧은 쉼은 입 안 다묾, ㅁ·ㅂ·ㅍ 앞 선행 닫힘 |
| 5 | PySceneDetect | BSD-3 | 컷 리듬, 정지 구간 측정 | 미실행 | 도입. 2초 규칙 게이트로 |
| 6 | DragonBonesJS | MIT | 포즈 전환이 뻣뻣함 | 코드 읽음 | 아이디어. IK 가중치 블렌드, 레이어 크로스페이드 (opt-in) |
| 7 | smartcrop.js | MIT | 썸네일 크롭 | 미실행 | 도입 |
| 8 | korean-subtitle-splitter | MIT | 자막 규칙 | — | 테스트 케이스로만 사용 |
| 9 | CosyVoice 3 | Apache-2.0 | TTS 대안 | — | 측정만 |
| 10 | Motion Canvas | MIT | 대사 이벤트에 카메라 큐 연동 | — | 아이디어 |
| 11 | Inochi2D | BSD-2 | 2.5D 고개 돌림 | — | 아이디어 (노력 큼) |
| 12–15 | kss, auto-editor, Retention, Theatre.js | — | — | — | 보류 |

**스와이프 이탈:** 효과를 데이터로 입증한 오픈 프로젝트는 없다. PySceneDetect로 첫 2초 변화량을 재고, Kiwi로 첫 자막을 의미 단위로 끊고, smartcrop으로 썸네일 후보를 만든 뒤, 셋의 효과를 engaged%로 판정한다.

**자막 기준 근거:** Netflix 한국어 자막 가이드는 한 줄 16자, 초당 12자다.
