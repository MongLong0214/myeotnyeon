# Shorts factory v2 (offline)
채널 팩 CLI: `factory/make.py --channel <id> --episode channels/<id>/episodes/<eid>.json --stage <name|all>` — 설계·감사는 [FACTORY_DESIGN.md](FACTORY_DESIGN.md). 출력은 `out/factory/`, `upload/pkg/`에 쓰지 않는다.
`./factory/short.py q013 --no 16` — 같은 qid 예약은 PASS, 타 qid 예약·타 영상의 발행/예약 발행 번호는 FAIL.
`./factory/short.py q014 --no 15 --video-id S-eU5rbP9yg` — 알려진 동일 영상의 재빌드.
`./factory/short.py q011 --no 99 --dry-number` — 신규 hero·전체 M1 음성·v52 화면을 만드는 업로드 금지 테스트.
신규 입력은 `episodes_n16.py`의 에피소드 명세와 `research/raw*/` 보관 기사; 기존 편별 파일 불필요.
hero는 기존 `build_hero.py`/`world2.py`, 음성은 로컬 Supertonic 3 M1, 7.5음절/초 이상·문장 간 무음 0.12초 이하.
로컬 `.venv`, Blender, FFmpeg, Remotion/Chromium, Supertonic·Whisper 모델 캐시와 공용 폰트 필요.
기존 q013/q014 준비 자산·AAC 캐시 경로는 유지; `--fresh-hook`은 기존 훅만 재합성.
결과 `upload/pkg/qid_nN[_vK]/`: 영상·커버·메타·qa.json·review_sheet.jpg·SHA256; 기존 패키지 보존.
ledger 항목: `{no,qid,state:published|scheduled|reserved,video_id?,date?}`; 검사는 읽기 전용, 번호를 소비하지 않음.
`--dry-number`는 모든 게이트를 실행하며 `TEST_ARTIFACT`를 기록하고 READY를 만들지 않음.
사실·금지선은 `FAIL / NEEDS_REVIEW`; CTO 확인 전 READY 불가.
CTO는 `qa.json.cto_signoffs.<gate>`에 role=CTO,name,reason,input_sha256 기록 후 `--check <패키지>`.
CTO 서명은 facts의 모든 로컬 보존 스냅샷 SHA256에 연결되며, 변경 시 재검토·누락 시 `missing source snapshot: <id>` 확정 FAIL로 서명 및 READY 불가.
`./factory/regression.py` — q013/q014 프레임·AAC·PCM·PSNR 회귀, 알려진 결함 및 예약 소유자 3개 사례 검사.
네트워크·업로드·유료 AI 호출 없음.

## 숏츠·롱폼 공통 체크리스트

`review_gates.py`의 A1–G2 항목별 함수를 기존 `gates.py` 뒤에 추가한다. 기존 빈 패널·사실·원문 스냅샷·번호 게이트는 유지한다. Shorts의 새 빌드와 `short.py --check`가 공통 항목을 실행한다. 기존 패키지를 보존하려면 `--check`를 실행할 복사본 또는 새 빌드를 사용한다.

롱폼 최종 인코딩 검수:

```sh
./factory/longform_qa.py video.mp4 --shots shots.json --script script.md --facts facts.md facts_enrich.md --alignment alignment.md
```

`--alignment`는 선택 사항이다. 결과는 새 `factory/review_runs/<영상>_<순번>/qa.json`과 근거 시트에 쓴다. 기존 영상·에피소드·패키지·원장은 읽기 전용이다. 롱폼 검수는 렌더·업로드를 실행하지 않는다.

**advisory를 제외한 [자동] 게이트가 PASS이고 [자동+서명] 항목이 CTO_SIGNED이어야 한다.** `INPUT_MISSING`은 입력 부족, `NEEDS_REVIEW`는 미확정, `FAIL`은 확인된 결함이다. 입력 부족은 별도 목록에 기록하며 readiness를 막는다. 승인 대조군에서 false-FAIL이 남은 게이트는 `gate_calibration.json`에 따라 `advisory: true`로 표시하고 `ready` 계산에서 제외한다. `ready`/`ceo_review_eligible`은 CEO 검수 진입 조건이다. 그 후 CEO 시각 검수 PASS가 있어야 원일에게 전달한다. F3/G1/G2는 사람이 실행하며 자동 서명으로 통과시키지 않는다. 업로드 절차는 [upload_precheck.md](upload_precheck.md)를 따른다.

샷의 `start`/`end`는 프레임 번호, `start_s`/`end_s`는 초다. 기존 `shots.json` 리스트 및 `shots`·`narration`·`subtitles`가 있는 문서를 지원한다. 리스트형 샷은 같은 폴더의 `episode_data.json`·`subtitles.srt`에서 내레이션·자막을 읽는다. 컷 시트는 최종 믹스 ASR 단어를 사용하며, 의도된 발화와 분리해 표시한다.

대본에 `[COLD_OPEN @ 0.000]`, `[CENTRAL_QUESTION @ 2.940]`, `[CLIFFHANGER @ 40.000]` 또는 시간 구간이 있는 `## N001 · 0.000–2.885s · COLD_OPEN` 표기를 넣는다. 자동 추정이나 제작 QA의 주장으로 대체하지 않는다. 샷은 `subject`, `location`/`set`, `shot_size`/`type`, `screen_direction`, `axis_side`, `character_acting`, `action`, `intended_label`, `facts`를 제공한다. `camera_direction`은 화면 속 인물 방향의 증명이 아니다. 필요한 메타데이터가 없으면 FAIL이다.

추가 근거는 `--review-inputs review_inputs.json`으로 제공한다(Shorts는 새 패키지 안 `review_inputs.json`). 경로는 이 JSON 파일 기준이며, 네트워크 URL만 있으면 통과하지 않는다:

```json
{
  "subtitle_band": [0.78, 1.0],
  "topic_criteria": "CTO의 소재 채택 기준",
  "interest_evidence": [
    {"kind": "press_count", "file": "press.md", "value": 12},
    {"kind": "community", "file": "community.md", "value": 25}
  ],
  "references": [{"channel": "채널명", "video": "reference.mp4", "metrics": {"views": 100000}, "time_s": 0, "our_time_s": 0}],
  "style_bible": "style_bible.md",
  "renderers": ["2D"],
  "sources": [
    {"publisher": "매체1", "file": "source1.txt", "sha256": "로컬파일해시"},
    {"publisher": "매체2", "file": "source2.txt", "sha256": "로컬파일해시"}
  ]
}
```

ASR는 로컬 Whisper 가중치만 읽는다. OCR은 로컬 macOS Vision(한국어/영어), 없으면 설치된 Tesseract를 사용하며 한국어 OCR 불가를 PASS로 처리하지 않는다. C3는 실제 `staging.actors`·`actors`·`p.actors` 필드를 읽고, 없으면 로컬 머리·몸통·다리 실루엣과 카메라 이동 보정 후 인물 영역 변화를 확인한다. 미검출은 unknown이며 인물 비율을 0%로 확정하지 않는다. 정지·모션은 자막 영역을 제외한 전 프레임 차분으로 측정한다. OCR은 최종 인코딩의 모든 프레임을 640px 폭으로 검사한다. 시간 표본 추출은 하지 않는다. 작거나 장식적이거나 대비가 낮은 글자를 놓칠 수 있으며 이 한계를 qa.json에 남긴다. F1은 전체 영상의 모든 프레임을 시트로 제공한다. 실시간 재생을 대체하지 않으며 모든 qa.json에 `실시간 재생 미검수`를 명시한다.

CTO는 결과의 `input_sha256`를 확인하고 `cto_signoffs.<항목>`에 `role=CTO,name,reason,input_sha256`를 기록한다. D2는 `matches: {"샷ID": "MATCH"}`를 **모든 샷**에, B4는 `reads_as: {"샷ID": "직접 읽힌 명칭"}`를 기록해야 한다. 제작 쪽 정렬표의 MATCH는 무시한다. 자동 실패는 CTO 서명으로 해제할 수 없다. 서명은 본인 역할을 기재하는 기존 로컬 프로토콜이며 암호학적 신원 인증은 아니다.

```sh
./factory/longform_qa.py video.mp4 --shots shots.json --script script.md --facts facts.md \
  --resume factory/review_runs/video_001 --signoffs cto_signoffs.json
```

재검사는 같은 검수 디렉터리에서 근거를 다시 생성한다. 영상·대본·사실표·샷·정렬표·원문·검수 코드·근거 시트 바이트가 바뀌면 기존 서명이 무효다. F3/G1/G2의 사람 확인은 별도 기록하며 `owner_delivery_ready`는 자동으로 켜지지 않는다.

구현 상태:

| 항목 | 판정·근거 |
|---|---|
| A1/A3 | 소재 점수표·로컬 포맷 레퍼런스 → CTO 서명 |
| A2 | 관심 근거 2종 이상 첨부 확인 |
| B1/B2/B4/B5 | 비교·AI 티·의도 명칭·스타일 시트 → CTO 서명 |
| B3 | 로컬 레퍼런스 컷·인물·모션·텍스트 실측. 측정기 미지원 시 FAIL |
| C1 | 대본 TTS 발음 음절 / 실제 발화 구간 합(문장 사이 삽입 쉼 제외). 대본 동일성·최종 ASR 음성 시작/끝 대조. 쉼 포함 속도와 ASR 표기 속도도 함께 기록 |
| C2 | 타임 마커·클리프행어·전 프레임 정지 검사 + 첫 60초 시트 서명 |
| C3 | 인물 연기 비율·로컬 인물 검출 표본·모션·자막 밖 OCR·삽입 컷 길이 |
| C4 | 표정·동작·카메라·독창 캐릭터 검수 시트 서명 |
| D1/D2 | 전 컷 앞뒤·샷 중간 프레임·실제 발화·자막; 이전 절 마지막 단어 끝부터 다음 단어 시작까지의 구간과 거리 ±0.12초 + 샷별 CTO MATCH |
| D3 | 메타데이터·컷 SSIM·화면 방향·180도 축·장소 설정 샷 |
| E1 | 자막·실제 graphic 필드·전 프레임 OCR의 한글 수사 및 숫자+년월일 날짜 금지(발화 제외). 복수 facts의 채택 사실·날짜 열 대조 |
| E2/E3 | 사실표 폭력 비트 프레임·원문 스냅샷·정확성·레드라인 검수 서명 |
| F1/F2 | 전 프레임 시트 서명; ASR·싱크·음량 수치·실시간 재생 미검수 한계 |
| F3/F4 | CTO 이후 CEO 시각 검수(운영); 전달 전 레퍼런스 재확인 서명 |
| G1/G2 | 사람이 Studio 당일 업로드 수·비공개 잔존본·원장 대조 |

B3 레퍼런스의 인물 검출은 macOS Vision의 로컬 human rectangles를 우선 사용하며 설치된 OpenCV HOG를 대안으로 쓴다. 카툰의 표정·동작 자체를 확정하는 모델은 아니므로 인물 검출로 메타데이터의 연기 여부를 승격하지 않는다. B4 의도 명칭은 샷의 `intended_label` 또는 `review_inputs.json.intended_labels.<샷ID>`로 명시한다. 행동 코드만으로 소품 이름을 추측하지 않는다. C1의 문장 끝 0.2–0.3초 창은 롱폼에 적용하며 Shorts는 기존 문장 간 0.12초 이하 게이트를 유지한다.

`./factory/review_regression.py`는 원본을 수정하지 않고 요청된 네 알려진 결함을 검증한다. 새 `factory/review_runs/known_bad_<순번>/report.json`에 발화한 확정 FAIL·놓친 기대 게이트·검수 대기·미평가 범위·입력 변경 여부를 기록한다. LF2 v5는 공통 게이트 전체를 실행하고 D2 전 컷 시트를 만든다. LF2 v4/N18 v4는 날짜·인물 결함에 필요한 최종 프레임/OCR 검사를 실행한다. 의미상 그림·발화 불일치는 기계가 결정할 수 없으므로 CTO 샷별 서명이 계속 필요하다.

보정 대조군 실행은 `./factory/calibrate_review.py`를 사용한다. 지정된 승인 Shorts 원본(`upload/v52_q014_n15.mp4`)의 공통 A1–G2 검수, CTO 인물 유무 14샷, 기존 known_bad_003의 4개 결함을 검사한다. false-FAIL은 자동 확정 결함만 세며 입력 부족·미서명·운영 항목을 세지 않는다. 각 대조군의 범위와 미판정 항목을 결과에 명시한다. 기존 legacy Shorts 게이트는 그대로 유지한다.

`longform_qa.py --measurement-cache factory/review_runs/<기존결과>`는 영상·ASR·오디오·OCR 해시를 확인하고 기존 로컬 ASR/OCR을 재사용한다. 프레임·모션은 다시 측정한다. 검수 대상 lane이 수정 중이면 메타데이터를 `factory/`에 고정한 사본으로 제공한다.
