# Task: Shorts batch for the growth sprint (6 videos) — W=/Users/isaac/projects/verdict-kr/work

Goal: 1,000 subscribers by 11-26 (currently 9). Analysis (W/channel/analytics/REPORT_2026-11-06.md):
- Bottleneck 1: the first 1–2 s — the viewed-vs-swiped-away rate is only 24–50%.
- Bottleneck 2: every video stalls at 1–1.8k views.
- Bottleneck 3: almost no subscriber conversion — about 0.5 per 1,000 views.

## Topics (6)
- Pick from W/research/viral_candidates.md, v3_candidates.md, agent1_case.jsonl and interest/. Already-used qids are excluded.
- Criteria: shock first — death, violence, social outrage, widely searched or controversial (owner rule: provocative only; financial and tech crimes are weak). A judgment (the sentence) must be confirmed.
- Facts: at least 2 independent sources. The facts gate of the existing factory/short.py is mandatory.

## Production rules (new in this batch)
1. **Frame 1 (0.0 s) is already the action:** the q014 comedy rig (W/episodes/quiz/q014/fight_revision/comedy/) reenacting the key act, plus a big number question (e.g. "징역 몇 년?").
   - No title card or empty background at the start. The current 2-second hook card (a 3D street with text) is removed.
2. Reenactment: the same method as the owner-praised q014 comedy — action → reaction → result, visual metaphors labeled. Facts only, victims not identifiable, no mockery.
3. **Subscribe conversion devices:**
   - Series identity: "몇년나옴 #N" in the bottom corner throughout.
   - Hold the answer until the very end (create a reason to stay).
   - Final 1.5 s: a picture of the next case plus "다음 판결도 맞혀보세요 → 구독". Remove the black end card.
   - The title and description ask viewers to answer in the comments (e.g. "댓글로 정답 먼저 →").
4. Length 20–30 s. Narration 7.5+ syllables/s; Shorts are fast.
5. Every review gate of factory/REVIEW_CHECKLIST.md. E1: dates as numbers.

## Output
- W/upload/pkg/<qid>_batch1107/
  - video.mp4 (1080x1920), cover.jpg
  - meta.txt (title ≤ 40 chars with a hook, description, sources)
  - qa.json
  - the 0.0–3.0 s frame sheet, as PNG under W/episodes/review_full/shorts/<qid>/ (paths the CEO can open)
- No numbers assigned yet; the CTO assigns them in upload order.

No self-assigned PASS. No uploads. Final message: short, in Korean, with each topic's choice reason and its facts sources.
