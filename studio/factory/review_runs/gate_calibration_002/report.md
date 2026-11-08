# 리뷰 게이트 보정 결과

수정·생성 범위는 `factory/`뿐이다. 실행 중인 lane과 episode 파일은 수정하지 않았다. LF2 lane이 실행 중 메타데이터를 갱신했으므로, 최초 리뷰의 컷 시트에 남은 원본 샷 JSON을 `calibration_inputs/lf2/`에 복원했다. 기준 영상은 기존 리뷰의 SHA256과 일치한다.

| 항목 | 이전 → 이후 |
|---|---|
| 1 E1 표시 | LF2 PASS → FAIL. 자막·실제 graphic 필드·전 프레임 OCR의 `N년 N월 N일`·`N월 N일`·`N년 N월` 검출. 발화 제외. |
| 2 E1 근거 | 단일 facts·첫 열만 → 복수 `--facts`(반복/목록), 채택 사실·날짜 열·명시적 날짜 구분문. N18 근거 누락 0건. 날짜 표시 형식 결함은 별도로 FAIL 유지. |
| 3 C1 속도 | ASR 표기 6.52/6.13 → TTS 발음 7.851/7.094음절/s. LF2 2537음절/323.145s, N18 2586음절/364.548s. LF2 lane의 7.15는 문장 사이 쉼 포함(2537/354.6); 동일 분모가 아니었다. 쉼 포함 ASR 음성 구간 속도도 별도 기록. LF2 속도 창 FAIL, N18 속도 창 PASS; 두 편의 기존 ASR 쉼 결함은 별도 유지. |
| 4 D2 | LF2 1.9s 컷 오차 0.34 → 0.02s(허용 범위). 이전 절 마지막 단어 끝~다음 단어 시작 구간 내부는 거리 0. |
| 5 C3 | LF2 0% → 30.1%; N18 2.7% → 미확정(75.3%–100.0%). 실제 actor 필드·로컬 실루엣·카메라 이동 보정 후 인물 영역 변화 사용. CTO 14샷 인물 유무 일치 14/14. N18 H002–H006의 설명 패널은 결함 근거로 남음. 소품 view 이름만으로 인물 부재를 확정하지 않으며, 미검출은 0%가 아니라 unknown/NEEDS_REVIEW. |
| 6 입력 부족 | A1–A3·B1/B3 및 실제 입력이 없는 B4/B5/E3: FAIL → INPUT_MISSING. 미서명은 NEEDS_REVIEW. 결함 목록과 입력 부족 목록 분리. |
| 7 대조군 | 원본 `upload/v52_q014_n15.mp4`에 Shorts 공통 A1–G2 QA 실행, CTO 14샷과 known_bad_003의 기존 4결함 재검사. false-FAIL이 남은 게이트만 advisory, ready 계산에서 제외. |

## false-FAIL (게이트별)

| 게이트 | 건수 |
|---|---:|
| A1 | 0 |
| A2 | 0 |
| A3 | 0 |
| B1 | 0 |
| B2 | 0 |
| B3 | 0 |
| B4 | 0 |
| B5 | 0 |
| C1 | 0 |
| C2 | 1 |
| C3 | 1 |
| C4 | 0 |
| D1 | 0 |
| D2 | 1 |
| D3 | 1 |
| E1 | 0 |
| E2 | 0 |
| E3 | 0 |
| F1 | 0 |
| F2 | 0 |
| F3 | 0 |
| F4 | 0 |
| G1 | 0 |
| G2 | 0 |

자동 확정 FAIL만 집계했다. INPUT_MISSING·NEEDS_REVIEW·운영 항목은 false-FAIL에 포함하지 않았다. Shorts 대조군은 사용자가 승인·게시 대조군으로 지정한 원본이며, 로컬 ledger에는 scheduled로 기록돼 있다. CTO의 long-form 정답은 인물 유무 14샷에만 적용했다. 라벨이 없는 다른 long-form 게이트를 무결함으로 가정하지 않았다. 기존 legacy Shorts 게이트는 변경하지 않았으며, 승인 원본의 대조 실행 범위는 공통 A1–G2다.

## 회귀·advisory

- LF2 v4 E1, N18 v4 C3, LF2 v5 C1, Shorts 빈 패널: **4/4 FAIL 유지**. 기존 known_bad_003은 보존.
- advisory: **C2, C3, D2, D3** (각 1건). C1은 승인 Shorts에서 7.852음절/s로 PASS, false-FAIL 0.
- 행동 테스트 **28개 통과**. 최종 source/evidence 바이트와 policy 바인딩 일치 확인.
- 두 long-form의 `ready=False` 유지. 입력 부족·미서명과 C1의 남은 결함을 숨기지 않았다.

[Shorts QA](accepted_short/qa.json) · [CTO 14샷](ground_truth.json) · [known-bad](known_bad.json) · [LF2 QA](../calibrated_lf2_v6/qa.json) · [N18 QA](../calibrated_n18_v6/qa.json)
