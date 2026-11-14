# Task: adopt the reusable parts of claude-animated-shorts (MIT) — W=/Users/isaac/projects/verdict-kr/work

Read W/references/claude-animated-shorts/ANALYSIS.md first.
- **License:** code and docs are MIT. Reuse requires attribution: leave the original copyright and MIT notice in the file header and in `W/factory/THIRD_PARTY.md`.
- **Never reuse `references/`** (third-party channel frames, sheets, STYLE_BIBLE, reports).
- **Do not install dependencies or run the original repo's scripts.** Port the code you need into our stack, then verify it with our tests.

## Port (edit only the paths named here; do not touch files that running lanes are writing)
1. **QA:** port `templates/scripts/short_qa.py` (black/white frames, frozen holds, pop frames, loudness, contact sheets) to `W/factory/lib/frame_qa.py`.
   - Call it from factory/review_gates.py as an advisory gate.
   - Regression: run it on our final files (v52_q013_n16_unslop.mp4, v52_q014_n15_comedy.mp4). Report the false positives.
2. **Audio:** port `templates/audio/mix.py` and `dsp.py` (LUFS/true-peak limiting, word-timing-keyed music ducking) to `W/factory/lib/audio_mix.py`, connected to the Supertonic word timestamps.
   - Shorts −14 LUFS, true peak −1 dBTP.
   - Apply it only to new renders.
3. **Camera DSL:** re-derive the frame-pure camera timeline pattern from `templates/bridge/story.ts` (glide, pushK, kickAt) in 2D, as `W/production/lf_toon/src/camera2d.ts` (new file).
   - Primitives: snapZoom (2–4 frames), smashCut, impactShake, deadpanHold, pushIn.
   - Pure functions plus unit tests. Write down how to import it into the existing ToonRig/FightRig scenes (do not change the scene code).
4. **Expression library:** use the expression table structure of `templates/bridge/toon.ts` (14 expressions) as a model and write `W/production/lf_toon/src/expressions.ts` (new file).
   - **Every expression must have eyes, nose and mouth** (the original has no nose, so add one).
   - Include the exaggeration levels of W/factory/unslop/STYLE_VIDEO.md (the R&M rules): jittery pupils, bulging eyes, sweat, veins, a twitching mouth.
5. **Beat formula:** adapt `templates/SCRIPT_example.md` (hook → setup → escalation → snap → analogy → consequence → callback) into a court-case beat sheet, `W/factory/BEATSHEET.md`, aligned with the existing REVIEW_CHECKLIST H rules.

Output: the ported files, tests, THIRD_PARTY.md, and a report of the frame_qa regression results. Final message: short, in Korean.
