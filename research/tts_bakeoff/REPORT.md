# 한국어 TTS 비교 (2026-11-08)
(하위 에이전트 쓰기 차단으로 CTO가 요약 저장. 수치 원본 metrics.json, raw/asr.json, raw/utmos.json. 샘플 samples/ 14개, compare_all.mp3)

## 방법
같은 3문장, 다큐 내레이터 톤, 엔진별 1회 합성(골라내기 없음), 모두 −16 LUFS로 맞춤. 음절/초, 로컬 whisper 오인식률, 합성 속도, UTMOS(영어 기준 참고치) 측정. 실제 청취 판정은 안 함.

## 상업 이용 가능 + 로컬
| 후보 | 라이선스(코드/가중치) | 음절/초 | 오인식 | 비고 |
|---|---|---|---|---|
| Supertonic3 M1 (현재) | MIT/OpenRAIL-M | 5.81 | 0 | 기준선 |
| Qwen3-TTS 설계 남 / Sohee / 설계 여 | Apache/Apache | 4.5–4.8 (속도 맞춤판 6.4) | 0 | 가장 빠름, 채널 전용 목소리 설계 가능 |
| Chatterbox Multilingual 남/여 | MIT/MIT | 5.9 / 5.1 | 0 / 0.022 | 참조 음성 필요(Qwen 합성 음성 사용), 워터마크 여부 미확인 |
| VoxCPM2 남/여 | Apache/Apache | 6.0–6.6 | 0 | 4bit에서 잡음 의심 |
| MeloTTS KR | MIT/MIT | 4.2 | 0 | 단조로움 |
| MOSS-Nano | Apache | 1.9–2.1 | 높음 | 불합격 |

## 제외(라이선스·언어)
OmniVoice·F5-TTS·MMS-TTS·Voxtral(CC-BY-NC), Fish S2/OpenAudio·Higgs v2(비상업/연구), XTTS-v2(CPML), Spark-TTS·KSS VITS(NC-SA), macOS 내장 음성(비상업), IndexTTS2·Kokoro(한국어 미지원).
미측정(라이선스 OK): CosyVoice 2/3(다음 1순위), GPT-SoVITS, ZONOS2(15GB), Orpheus 한국어.

## compare_all.mp3 순서
supertonic3_M1 → qwen3 설계 남 → 설계 남(속도 맞춤) → Sohee → Sohee(속도 맞춤) → 설계 여 → Ryan → VoxCPM2 남 → VoxCPM2 여 → Chatterbox 남 → Chatterbox 여 → MeloTTS → MOSS-Nano 여 → 남
