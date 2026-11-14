# Task: calibrate review gates (false positives and misses) — W=/Users/isaac/projects/verdict-kr/work, edit only W/factory/

Running `factory/longform_qa.py` on the v6 long-forms gave the results below. The result directories are
`factory/review_runs/lf2_cartoon_v6_1080p_001` and `n18_cartoon_v6_1080p_001`.
Fix only these points. Do not add new checklist items or new KPIs. Do not touch the two cartoon lanes that are running, or their episode directories.

1. **E1 miss.**
   - Owner's words: "년월일 표시 한글로하지말고 숫자로해". The CEO's reading: on-screen dates are `YYYY-MM-DD`.
   - The LF2 v6 subtitles and titles show "2001년 12월 21일" (13.59 s and others) and still PASS. Any on-screen text (subtitle or graphic) of the form `N년 N월 N일`, `N월 N일` or `N년 N월` must FAIL.
   - The spoken narration is exempt. If subtitles and narration are the same text, judge the subtitles by their displayed form.
2. **E1 false positive.** N18 has dates such as 2024-05-25 and 2024-08-27 marked "not in facts". The facts are split across `episodes/v4/n18/facts.md` and `facts_enrich.md`. Accept multiple `--facts` files.
3. **C1 false positive.** LF2 measures 6.52 and N18 6.13 syllables/s. That count is based on the ASR text and leaves out the syllables of spoken numbers. Count using the TTS pronunciation text (the script's spoken form) over the actual speech duration. Reconcile with the 7.15 and 7.09 the lanes reported.
4. **D2 false positive.** For example, LF2 cut 1.9 s is judged 0.34 s off. A cut that falls inside the pause between two clauses (from the end of the previous word to the start of the next word) is on the boundary. Measure the distance to that pause interval.
5. **C3 false positive.**
   - LF2 scores a character share of 0%, N18 2.7%. The classifier depends on a vocabulary that isn't in the shot metadata.
   - Ground truth from the CTO's own viewing: V6_001 and V6_002 contain characters, V6_003–006 do not. N18 H001–H008 all contain characters, but H002–H006 have explanation panels covering them.
   - Detect characters and their action from frames (a local detector or silhouette heuristics), or from character fields that really exist in the shot JSON.
   - Unknown counts as NEEDS_REVIEW, never as a 0% FAIL.
6. **Missing inputs vs defects.** A1–A3 and B1/B3 FAIL because no local reference exists. Report input-missing as `INPUT_MISSING`, kept separate from `FAIL` (a defect), so a missing input is never shown as a defect.
7. **False-positive control (mandatory).**
   - Run Shorts QA on the Shorts the owner accepted and that were published, e.g. `upload/v52_q014_n15.mp4`.
   - Run long-form QA on the CTO's ground-truth shots listed in item 5.
   - Report a false-FAIL count per gate.
   - Keep the known-bad regression (`review_runs/known_bad_003`) all FAIL.
   - Any gate whose false-FAIL count is not 0 is marked `advisory` in qa.json, and an advisory gate does not decide `ready`.

Final message: short, in Korean. Before/after for each item, the false-FAIL count per gate, the regression result, and the list of advisory gates.
