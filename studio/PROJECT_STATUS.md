# EP001 판결의 이유 — 작업 상태

갱신: 2026-10-26 07:40 (v2 가벼운 편집본 완성)

## 지금 상태
- **완성본**: `episodes/EP001/final.mp4` (3분 47초, 1920×1080 30fps, H.264 + AAC, 92.7 MB), `thumbnail.png`, `subtitles.ko.srt/.vtt`, `description.ko.md`, `render_manifest.json`.
- **검사**: `validate_v2.py --media final.mp4` 16개 항목 모두 통과 (타임라인·플레이트·자막·음성 배치·사실 출처·라운드니스 -16.0 LUFS / 트루피크 -1.4 dBFS). 검은 화면 구간 0. 전체 2초 간격 화면 시트 육안 확인.
- **인물**: Quaternius 마네킹(CC0) + CMU·100STYLE 모션캡처. 일어나는 동작은 발 끌림이 남아 사용하지 않음(다시 들이받힐 때 B는 서 있는 상태로 재구성).
- **공개 전 보류 (변경 없음)**: 판결문 원문 확보(유료 열람, 승인 없이 결제 안 함), Sketchfab CC-BY 자산 현재 라이선스 재확인, Remotion 회사 라이선스 해당 여부, 사람의 법률·사실 검수. 업로드하지 않음.

## 다시 만드는 순서 (episodes/EP001)
1. `python3 script.py` — 원고(script_text.json)
2. `source ../../.venv/bin/activate && python tts.py M2 1.2` — 음성, 이어서 `python asr_check.py` (기준 넘는 문장은 `python tts_best.py ID,.. 5`)
3. `python3 layout.py` — 프레임 배치·자막·script.json
4. `python3 edit.py` — 편집 결정 목록 → compositor/public/ep001/render.json, edit_fx.json
5. `(cd ../../production/audio && python synth2.py ../../episodes/EP001)` — 음악·효과음·믹스·마스터
6. 3D: `production/blender/render_queue3.sh L01_aerial …` (shots3.py, shotlist3.json), 법정·소품은 `render_queue.sh SH13 …` (shots2.py)
7. `./render_final.sh` — final.mp4, thumbnail.png, render_manifest.json, `validate_v2.py --media final.mp4`
8. `python3 ledger.py && python3 make_docs.py` — 원장·문서 갱신

## 결정 기록
`work/DECISIONS.md`
