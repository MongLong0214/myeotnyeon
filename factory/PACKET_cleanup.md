# Task: delete unneeded local work products (owner instruction: "로컬에도 불필요한 작업물들 남겨놓지마 용량부족해" — don't leave unneeded work products locally; space is short) — W=/Users/isaac/projects/verdict-kr/work (100 GB)

## Keep (never delete)
- Every source file: code, scripts, facts tables, raw source texts (research/, episodes/*/raw, facts*.md), metadata, ledger, DECISIONS/PROJECT_STATUS, every .md/.json/.py/.ts(x).
- Final files of videos that are published or scheduled: upload/v52_q014_n15_comedy.mp4, v52_q013_n16_comedy.mp4 and the final mp4 plus cover of each published episode. Identify them by matching video IDs in upload/ledger.json.
- Current long-form work: the current files under production/lf_toon/ (prev1/prev2/prev3 may go), production/astra_12min/audio_edit plus the scripts and cues, and the TTS finals in use.
- Evidence the CEO ordered preserved: production/astra_preserved/, the 4 representatives at astra_12min/astra_correction/delivery_*, and episodes/review_astra/.
- Engines and models needed for rendering and TTS (tts_lab/engines, production/compositor source, node_modules).
- The 3D long-form failure record: keep only FROZEN_CANDIDATES.md and one 720p final; the rest may go.

## Delete
- Regenerable render intermediates: frame directories, bundle/, render_*/ output folders, picture_*.mp4, silent intermediate mp4s, audit.mp4, empty.mp4, video_muted.mp4, *.wav intermediates (mix intermediates, not the final TTS).
- Superseded versions: replaced or rejected candidates (v3/v4/v5/v51 shorts mp4s that were never published; the v4/v5/v6/v6fix/v6fix2 cartoon mp4s, which are rejected — keep their READY/qa/md records; the 3D long-form intermediates), and upload/inspect_*, fix_*, preview.
- factory/review_runs/** images and video (keep qa.json and the md files).
- tmp, cache, and other *.log files over 50 MB.

## Procedure
1. Write a manifest first: `W/_cleanup/manifest_2026-11-06.tsv` (path, size, category, reason).
2. Delete only the "Delete" categories. If anything is ambiguous, keep it and list it in the report.
3. Never use rm -rf patterns that cross the W root. Delete by explicit paths, in order.
4. Report: space reclaimed (before/after df), deletions by category, and the ambiguous items that were kept.

Do not touch the .git or .gitignore being made by the concurrent repo-init lane. Final message: short, in Korean.
