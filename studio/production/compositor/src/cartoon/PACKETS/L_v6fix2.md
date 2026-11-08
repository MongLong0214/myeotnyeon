# v6fix round 2 — CEO decision A (continue the same session; the previous work stays valid)

The CTO review (`W/episodes/review_v6fix/CTO_REVIEW.md`) and the CEO both FAIL v6fix. Read the CTO review first.

## Decision A
- **Script constraint lifted for the middle act only** (LF2 about 2:00–5:40, N18 about 2:40–5:12). TTS regeneration is allowed there.
  - Use the same voice, model and speaking-rate settings as the existing narration, so the joins sound seamless.
  - Do not change the rest of the narration.
- **Compress the repeated sentencing and legal explanation.** 60–90 s is a target, not a mandatory cut.
  - Keep, word for word in meaning: the prosecution's sentencing demand, the sentence, whether it became final, the court's key reasons and the timeline.
  - Re-check every changed sentence against facts.md and record it.
- **Cutaways reenact confirmed facts only.** No invented actions, lines, motives or places to fill time.
  - Pull the pictures from events already in the facts: the arrest, the interrogation, the DNA match, the training, the hospital transfer and so on.
  - Reaction shots and split screens are allowed.
  - Do not cover repetition with engine tricks. Fix the editing cause.
- **Fix the other defects in the same pass:**
  - LF2: car arson not shown at 1:16; the bank employee wrongly placed at the 2001-10-15 police scene; the Suwon theft shot in the bank-garage set; the blank black panel in the parking lot; the blank cream panel on the courtroom wall.
  - N18: the translucent blue rectangle at 1:18–1:20; the white line across the hospital frame at 1:22–1:46; the H149 duplicate boundary; the H007 missing establishing shot.
  - N18 mother: match the existing character design and role continuity, not a gender stereotype of looks. She must read as the mother — the same person each time she appears, and clearly the parent.
- **Date display:**
  - If only the year is confirmed, use natural Korean such as `2015년` or `2015년에는`; `2015에는` is banned.
  - Full dates use `YYYY-MM-DD`. Never fill in a month or day that isn't confirmed.
  - Write date ranges naturally for what they mean. For example, change "07-01에서 06-01" to "7월 1일→6월 1일" or "시작일 07-01→06-01" — the meaning must be clear.
- **No new QA tooling and no engine redevelopment.** Run the existing longform_qa.py once, on the final file; its result is for reference only.

## Output (in the same folders: `*_v6fix2_1080p.mp4` and `_360p.mp4`; keep the earlier files)
READY_FIX2.txt, one package containing:
- the full sha256 of the frozen MP4;
- the changed script segments as a before/after diff, each with its facts reference;
- the changed footage plus a sheet of the frames before and after every affected join;
- the remaining defects, stated honestly.

No self-assigned MATCH or PASS. Final message: short, in Korean.
