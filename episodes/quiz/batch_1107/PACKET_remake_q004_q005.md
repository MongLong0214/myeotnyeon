# Remake q004 and q005 at the current Shorts standard (owner 2026-11-07)

Owner, 11-07: "4번째,5번째영상 회사냉장고초코파이,이주노동자지게차 이거 2개 삭제하고 다시만들어서 다시올리자"

The old uploads EomEdxcqfsU (q004, Choco Pie, 21 views) and MYjtxd25BhU (q005, forklift, 27 views) are deleted. They were the early v3 format. Remake both at the standard that produced the 11-07 Shorts (upload/pkg/q020_std, q018_std, q022_std). Use the same production path, gates and look.

## Standard (all of it, in this order of precedence)
1. factory/REVIEW_CHECKLIST.md, every item A1–H14. These are fail conditions.
2. factory/unslop/STYLE_VIDEO.md:
   - subtitles centered horizontally, legible, not AI-looking;
   - base shot 2–3 s ("너무 편집감이 빨라");
   - the R&M-style direction rules.
3. episodes/quiz/batch_1107/PACKET.md with add1–add5 and fix_victims. Where those conflict with items 1–2, items 1–2 win; for example the narration pace follows the _std versions, not 7.5 syllables/s.
4. The look and rig of the approved q013 v3 / q014 comedy standard.

## Case specifics
- **q004 (회사 냉장고 초코파이 절도 재판):**
  - The draw is outrage: a trivial snack turned into a criminal trial.
  - Lead with the absurd contrast (a ₩450-level snack vs a criminal court) in frame 1.
  - Re-check the verdict stage, appeal included, and every amount against at least 2 independent sources. Use the latest confirmed ruling.
- **q005 (이주노동자 지게차 결박):**
  - The draw is outrage at a light sentence (유전무죄/무전유죄 style).
  - Frame 1 is the act: a worker strapped to a pallet and lifted, staged non-graphically.
  - The victim's appearance follows the facts only (nationality as reported). Do NOT reuse the q013 foreign-worker design (fix_victims rule).
  - Not identifiable, no mockery. Every face has eyes, nose and mouth.
- Both: emphasize the A/B/C choices; the answer comes at the very end. No 재구성/시간압축 captions on screen; disclosure goes in the description only. No Blender. Dates as digits in Korean form (`2024년 5월 23일`), never ISO.

## Output
- W/upload/pkg/q004_std/ and W/upload/pkg/q005_std/, with the same file set as q020_std:
  - video.mp4, cover.jpg, qa.json, facts.md;
  - meta.txt containing only [제목], [설명] and [출처] (no internal notes).
- Frame sheets of 0–3 s and of the full video at 1 s intervals, under W/episodes/review_full/shorts/<qid>/.
- Do not upload. Stop for CTO review.
