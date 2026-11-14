# Gates fix3: H15 composition repetition and presenter ban; H16 digits in subtitles (owner 2026-11-07)

See factory/REVIEW_CHECKLIST.md H15–H16 and production/lf_toon/LONGFORM_ANIMATION_BIBLE.md.

1. **H16 (automatic):** scan the subtitle text (SRT, timeline or script subtitle lines, plus OCR as backup). Detect Korean-word numerals, built from 일이삼사오육칠팔구십백천만 runs or native forms like 한/두/세/네 + counter, when they are followed by a counter or unit (사단, 명, 개, 번, 분, 초, 년, 월, 일, 원, 억, 조, 퍼센트 and so on).
   - Positive control: N18 "십이사단" must FAIL.
   - Negatives that must PASS: 12사단; ordinary words such as 일단, 이상, 삼촌, 사실, 오늘, 구조, 한번에.
   - Keep the false positives under control with a word allowlist and a test.
2. **H15 (automatic plus sign-off):**
   - Sample one representative frame per shot (shots.json) or every 1 s. Compute a composition signature that is robust to the subtitle area: mask the bottom 30% and use a downscaled perceptual hash plus a color-layout histogram. Cluster the signatures.
   - FAIL if a cluster recurs within 60 s of film time (counted after a break), or appears in more than 3 separate segments in the film.
   - Presenter-pattern heuristic: a single large static figure plus a static prop region, with low motion inside the shot. Report it as NEEDS_REVIEW with the frames.
   - Produce a 10 s overview sheet for CTO sign-off.
   - Positive controls: N18 v2 and LF2 v2 finals and the LF3 Binance animatic (episodes/review_full/lf3_binance/lf3_binance_animatic_360p.mp4) must FAIL. Negative: q013 v3 Shorts (upload/v52_q013_n16_v3.mp4) should PASS or have only minor findings.
3. Add both to longform_qa.py and short.py. Add tests and run the existing tests with .venv/bin/python. Never loosen other gates. No rendering or uploads.
