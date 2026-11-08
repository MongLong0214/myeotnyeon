# Gates fix1: false fails in longform_qa (N18 v2 run)

Evidence: factory/review_runs/n18_v2_1080p_001/qa.json, from factory/longform_qa.py on production/lf_toon/v2/n18/n18_v2_1080p.mp4.

Fix the gate code only. Never loosen a gate to make a video pass. Each fix needs a test with one real counterexample that must still FAIL and one false fail that must now PASS.

1. **C1 pace window is out of date.** Long-form uses window [6.8, 7.2]. The owner later ruled "너무 편집감이 빨라" (base shot 2–3 s). Memory pace-faster gives 6.2–6.6 syllables/s with pauses of at most 0.2 s. Take the format windows from factory/unslop/STYLE_VIDEO.md and REVIEW_CHECKLIST.md (H14), one per format (Shorts and long-form). Do not hard-code a single window. If those two sources disagree, report the difference instead of picking one.
2. **C3 and D3 crash** with "unhashable type: 'dict'", so evidence generation fails. Find the cause and fix it, then add a regression test.
3. **D2 reports cuts at frames 2, 3, 5 and 10.** These come from motion inside a shot, not cuts. The cut detector must use the shot list (shots_v2.json boundaries) as ground truth and treat in-shot animation as non-cuts. A real hard cut that is not in the shot list must still FAIL.
4. **E1 marks 2024-05-23 as "not in facts"**, but fact_trace.md line 441 contains it. Make the facts parser read ISO and Korean date forms in the facts file. A date that really is absent must still FAIL.
5. Add a new check under E1 (or a new item number if the checklist structure needs it): subtitles must not show ISO or code-like dates (`2024-05-23`). The owner wants subtitles that do not look AI-made, so the Korean date form is required. Record the new item in REVIEW_CHECKLIST.md with today's date and the reason.

Run the existing gate tests and the new ones. Do not render or upload anything. Report the result as a changed-file list with test output.
