# SPEC — facts → episode spec

Input: the spec from RESEARCH.md. Output: a complete `episodes/specs/<id>.json` that passes
`.venv/bin/python factory/make_short.py validate episodes/specs/<id>.json`. Schema: `factory/schema/episode.schema.json`.
Copy the closest golden spec from `factory/specs/golden/` and change it: `q044.json` (ko), `en001.json` (en), `ja001.json` (ja),
`bc001.json` (Beast Clash: beats face, stat×3, prompt, clash 2-5, verdict 1-2, loop; animals and backgrounds in `factory/shorts/library.json` → `bc`).

## Fill in this order
1. `stage`: run `.venv/bin/python factory/make_short.py stages --tags money,bank --channel myeotnyeon`; take the top
   match that is not marked "previous episode". The open line or its fact must match the stage tags. `stage_day: true`
   only with the `cash` stage (day variant). `defendant`: a look from the stage's chars (or any look in the schema).
2. `quiz`: 3 choices, `answer` = index of the real sentence (validate rejects a 3rd same answer in a row: reorder; not in
   `result_first`). The correct choice must use the sentence type, number and unit of the `sentence_fact` quotes.
   `answer_text` (optional) = a longer answer wording that contains the correct choice (ja001: `実刑` → `実刑判決`).
   `format: "result_first"` (required when the channel has `spec_format: "result_first"` in factory/channels/registry.json — myeotnyeon does; skip `quiz` then): no quiz board; `hook` = the sentence outcome, 1-3 shots per line, and write
   `pinned` (one-line factual summary for the pinned comment).
3. `lines` — exactly this beat order: `open, hook, guess, twist, fact (1-4), answer2, loop`.
   - `text` = the subtitle, numbers as digits (`14억`, `12번`, `30 days`). Do not write `say`; the builder makes the spoken form.
   - `fact` = the fact id the line comes from. Every number in `text` must appear in that fact's quotes with the same unit (the `claim` does not count).
   - `shots`: `open` and `loop` have none. Others 1-2 shots, at most ~2.6 s of speech per shot.
     `react`/`cell` show the line `actor` (default the defendant); set `look` + `"other": true` only for someone else.
     Cards (`paper`, `bubble`, `stamp`, `phone`) must reuse words of the line; `tally.count` and `calendar.date` name a value (`F3.count`, `F1.start`).
   - `loop` = the words that lead back into `open` (e.g. `2020년 12월, 고객이 맡긴 통장과,`).
   - The builder adds choices, options, answer and the opinion question; do not write them.
4. `pops` (number pop-ups): `big`/`small` are templates with **no digits**; numbers come from `vars`:
   `F2.loan`, `F2.loan - F2.request`, `span(F1.start, F1.end)`, `months(F4.sentence)`, `days(...)`, `hours(...)`.
5. `hook` (2 short lines), `cover` (≤2 lines, `\n`), `title` (ko ≤30 chars, ends with `몇 년?` / `몇 년 나왔을까?` / `형량은?`,
   no 쟁점/어떤 형/최후), `description` (facts only; the builder adds finality, disclaimer, TTS credit, hashtags, sources),
   `hashtags` (3-6). Numbers in title, description, hook and cover must be in a fact quote.

## Never do
- No free TSX, no new stage names, no colours, sizes or coordinates: they are computed.
- No `#N`, `TBD`, `[...]`, `미정` anywhere. No gag wording or `dizzy` in a `grave` case.
- Do not edit `episodes/quiz/batch_1107/b_format/specs/` — that file is generated.

## Worked example (q044, ko)
`{"beat": "fact", "text": "서류 위조만, 12번이었습니다.", "fact": "F3", "actor": "suit", "shots": [{"scene": "tally", "count": "F3.count", "label": "문서 위조"}, {"scene": "react", "expr": "smug", "move": "nod"}]}`
→ spoken `서류 위조만, 열두 번이었습니다.`; tally of 12 checked against the text; pop `{real} → {forged}` renders `19억 5천만 → 16억 5천만`.
