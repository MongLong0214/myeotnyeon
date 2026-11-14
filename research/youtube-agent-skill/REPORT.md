# youtube-agent-skill (utillayer) 분석 요약 (2026-11-08)
(하위 에이전트 쓰기 차단으로 CTO가 요약 저장. 커밋 e0ac1e7, v1.2.0, MIT © 2026 UtilLayer. 클론 src/, 파일 38개 전수, 테스트 42개 통과)

## 정체
Claude Code 플러그인: /yt-* 스킬 12개 + 표준 라이브러리 Python 도구 9개(대본·제목·시청 지속·챕터·쇼츠 후보). 게시 기능 없음. 유료·API 키·로그인·GPT 없음(yt-dlp 선택).

## 쓸 것 (MIT, 파일 머리 출처 표기 + factory/THIRD_PARTY.md)
- A retention.py (S–M): Analytics API 무료 쿼리 dimensions=elapsedVideoTimeRatio, metrics=audienceWatchRatio,relativeRetentionPerformance, filters=video==ID → 곡선 → 가장 가파른 하락 5곳 + 그 시점 대사. cutoff를 인자로(쇼츠 2–3초 창). 첫 2초 이탈 진단.
- B 독립 팩트체크 (S): 대본 안 쓴 새 에이전트가 원전 줄 번호로 SUPPORTED/NOT IN SOURCE/CONTRADICTED/OVERSTATED/FLAGGED 판정, 줄 번호 없으면 SUPPORTED 불가, CONTRADICTED 0이어야 녹음. sourcekit.py find로 판결문 줄 번호.
- C 제목·썸네일 쌍 검사 (S): 썸네일이 제목 단어 반복 감점, 3어절 이하, 모바일 앞 40자. 조사 제거 처리 필요. shorts_rules check_title에 결합.
- D 챕터 초안 (S): chapters.py 경계 + 유튜브 규칙(00:00 시작, 3개 이상, 각 10초 이상) 검증, 제목은 새로.
- E 한국어 훅 채점기 (M): 판정식(평균 60% + 최저 축 40%)·공식 스키마만, 단어 목록 새로. lint 용도.
- F 롱폼→쇼츠 후보 (M): 20–55초 독립 구간, 9:16 재렌더 필요.
- G TTS 대본 검사 (S–M): 숫자 표기·기호·이름 통일·중간 반전, 음절·속도 기준.
- H 채널별 voice.md (S): 채널 팩마다.
- 운영 규칙: 해시태그 앞 3개만 제목 위·60개 초과 무시, 설명란 5,000바이트, 60초 초과 쇼츠는 Content ID claim 시 전 세계 차단(BGM 쓰면 60초 이하), 댓글 분류→주제 후보.

## 안 쓸 것
영어 단어 목록, swipe.py(topic_score.py와 중복), deadair.py(TTS엔 무관), 주 2–3회 업로드 권고, 플러그인 통째 설치.
