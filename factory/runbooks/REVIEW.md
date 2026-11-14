# REVIEW — fixed checklist, no taste

Input: `upload/pkg/<id>_B/` after BUILD passed. Output: `upload/pkg/<id>_B/review.json`. You do not judge whether the
video is "good"; you answer fixed questions with frame numbers. Numbers were already checked by the builder.

Who runs this step: a Sonnet-class model or stronger. RESEARCH, SPEC and BUILD can run on Haiku. Measured 11-14: Haiku
answered R1 "no" twice on zzh056 while faces_1fps.jpg plainly shows an envelope over the mouth at 0.5-2.5 s; Sonnet
caught it on zzs056.

## Read, in this order
1. `shorts_checks.md` — every row must say PASS (BUILD guarantees it). Copy `metrics` into review.json.
2. `gate/gate.md` — note the non-PASS rows listed under "Non-blocking items for REVIEW.md".
3. `sheet_1fps.jpg` — one tile per second, labelled `t s / frame`. Open it with the image viewer (Read tool).
4. `gate/subtitle_breaks.md` and `cues.md`.
5. `faces_1fps.jpg` (when the package has one) — every detected head at the same times, cropped close and labelled `t s fN #k`. Open it with the Read tool for R1. Some crops are not faces (cards, props the detector mistook); skip those.

## Answer each question: `"no"`, or `"yes"` + the tile times (e.g. `["3.5s", "12.5s"]`)
| id | question (look at sheet_1fps.jpg) |
|---|---|
| R1 | Is any face missing eyes, nose or mouth, or is anything (a prop, text, hand, another character) covering the eyes, nose or mouth? Answer from `faces_1fps.jpg` crop by crop, then check the same times in `sheet_1fps.jpg`. Give the crop labels' times. |
| R2 | In the tile image itself: is a letter of any text cut off by the frame edge, or hidden under another element? (A gate row saying "text box at frame edge" is not an answer; it also fires on approved videos. Put it in R9.) |
| R3 | In the first three tiles: does a letter of the big hook text lie on top of a face (eyes, nose or mouth hidden)? Text above a head is "no". (gate `hook_text_over_face` goes to R9, not here.) |
| R4 | Is any card (paper, bubble, stamp, calendar, tally) blank or showing a different number than the subtitle under it? |
| R5 | In a tile whose main subject is a person (react, cell, judge, prosecutor), is that person shorter than a third of the tile height? Tiles whose main subject is a board, card or prop (quiz choices board, paper, stamp, tally, bubble, money, the opening stage with desks) are "no" even if small people appear in them. |
| R6 | Count the cuts where the next shot looks the same as the one before it (same background, same person, same pose). Use the shots in order from `case.json` → `utterances[].shots` (BUILD already blocks two identical people shots in a row), not tiles: two tiles inside one shot that lasts over a second are one shot and never count. |
| R7 | Does the answer card show the same sentence as `meta.txt` and the quiz answer? |
| R8 | Does any subtitle line start with a particle or a split number (`건`, `을`, `,000`)? (subtitle_breaks.md) |
| R9 | For each non-blocking gate row: copy its id and the frames it lists. These rows are leads only; they never turn R1-R8 into "yes" unless you see it in the tile. |

## Verdict rule (mechanical)
- Any "yes" on R1-R5, R7, R8 → `"verdict": "FAIL"`, list the tiles, send to the coordinator. Do not fix by hand.
- R6 count ≥ 3 → FAIL. Otherwise PASS.
- review.json shape: `{"id": "<id>", "metrics": {...}, "answers": {"R1": "no", ...}, "gate_review": [...], "verdict": "PASS"}`.

## Never do
- Never write "looks fine" or a score. Never clear a gate REVIEW item without its frame numbers.
- Never call a frame-sheet read "watched the video". Say "1 fps sheet read".
