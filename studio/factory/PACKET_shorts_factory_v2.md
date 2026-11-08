# Task: Shorts factory v2 — reservation-aware number gate, and new episodes from scratch

W = .. Extend `W/factory/`; never overwrite existing packages or upload files. Local only: no network, no uploads, no paid AI.

The v1 factory (`factory/short.py`, `factory/regression.py`, `factory/README.md`, run_003) is proven: q013 #16 and q014 #15 rebuild bit-identically, and the known defects FAIL. Two gaps remain.

## 1. Number gate with reservations

`upload/ledger.json` holds published, scheduled and reserved numbers. Change the gate:
- FAIL if N is published or scheduled for a DIFFERENT video, or reserved for a different qid;
- PASS if N is reserved for this same qid, or is free.
Add a ledger field per entry: {no, qid, state: published|scheduled|reserved, video_id?, date?}.
`factory/regression.py` must show:
- q013 #16 PASS (reserved for q013);
- q013 #13 FAIL;
- q014 #16 FAIL (reserved for another qid).

## 2. New episodes from scratch

Today the factory needs existing v52/v5 inputs and a cached hero. Make `short.py <qid> --no N` work for an episode that only has its entry in the episode spec and its research sources:
- **hero still:** produced by the existing hero builder path (`episodes/quiz/v52_q013_q014_support/build_hero.py` imports `production/blender/world2.py`; reuse it);
- **narration:** the full narration synthesized with the same local TTS and voice as the v3 bodies (Supertonic 3 M1, the same speed rules: ≥ 7.5 syl/s, silences ≤ 0.12 s), with the hook line as today;
- **panels, captions, cover, meta:** as v52;
- **all gates**, with NEEDS_REVIEW for the facts and red lines until CTO sign-off.

Prove it on ONE unused episode, q011 (비상문 레버 승객, 대구지법). It is NOT reserved, so do not write it into the ledger. Use a test number, for example `--no 99 --dry-number`, so the number gate is exercised but not consumed. The output package is a test artifact, not for upload. Report its gate results and a review sheet.

## 3. Update `factory/README.md` (≤ 15 lines) and keep the regression green

Run `factory/regression.py` again; q013 and q014 must still be identical.

## Final message (short, Korean)

The gate changes, the q011 from-scratch result with its gate list, the regression result, and anything unfinished.
