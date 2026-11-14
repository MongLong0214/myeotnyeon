# CTO review — LF2/N18 v6fix (2026-11-01)

**Method:**
- Uniform contact sheets of the final 1080p MP4s, one frame every 2 s (LF2 177 frames, N18 198 frames), with subtitles burned in: `lf2_g01–09.jpg` and `n18_g01–10.jpg` in this folder.
- Every frame was compared with its subtitle and narration.

**Limits:**
- This is not continuous playback or listening, and not every frame.
- The automated gates (C2/C3/D2/D3) are advisory only (calibration: each produced 1 false FAIL).

## Overall: both CTO FAIL (much improved over v6)

**Improvements confirmed:**
- The explanation panels are gone.
- Every frame has characters in it.
- Dates are numeric: 2001-12-21, 2023-01-16, 2023-12-14 and others.
- The incidents are acted out: LF2 shooting, collapse, theft, the patrol officer hit by a car; N18 training with full gear, push-ups, the collapse, hospital transfer.
- N18 now uses real reverse and different angles.

**Remaining blocker (shared):** the middle act repeats talking in the same sets.
- LF2 about 2:00–5:40 rotates between the investigation room and three fixed courtroom compositions; the characters only hold up papers or books.
- N18 about 2:40–5:12 is a fixed courtroom with standing figures, and frames barely change. 3:28–3:32 and 4:42–4:56 are close to identical.
- This is the owner's complaint, "지루함·교육자료" (boring, like teaching material). The cause is that the script spends 2–3 minutes on sentencing and law. Engine work alone has a hard ceiling here.

## LF2 defects
1. 1:16.5: the narration says "차량에 불을 내 증거까지 없애려" (set the car on fire to destroy evidence), but no fire is shown. Narration and picture do not match.
2. 0:58.5–1:00.5: the bank employee (teal shirt) appears at the 2001-10-15 police hit-and-run scene. Character continuity error.
3. 0:44.5: "2001-12-01 수원에서 … 차를 훔쳤습니다" (car stolen in Suwon) is shown in the bank parking-garage set. Wrong location.
4. The subtitles "2015에는" (1:58/2:02), "2002에" (1:50) and "2015 충북의" (2:18) are broken Korean: removing 년 from year-only dates broke the grammar. Full dates stay YYYY-MM-DD; a year alone should keep "2015년" (CEO to confirm).
5. A large blank black rectangle sits behind every parking-lot shot and reads as a blank screen. Reads-as unclear.
6. The courtroom wall still carries a blank cream rectangle (leftover of a removed panel).
7. Pace: speech-only rate measures 7.85 syllables/s, above the owner's "slightly slower" window. Not changed, because the TTS was kept.

## N18 defects
1. 1:48.5–1:56.5 and 6:14.5–6:18.5: the "mother" (어머니 편지, the mother's letter) is drawn with the same male template as the men. Reads as a man.
2. 1:18.5–1:20.5: a translucent blue rectangle overlay covers the stretcher scene. Layer leftover.
3. 1:22.5–1:46.5: a horizontal white line runs across the whole hospital frame at eye level and crosses faces. Looks like a layer artifact.
4. 5:48.5–5:50.5: the subtitles "07-01에서 06-01" and "08-31" are hard to read. A month-day date with no year needs a CEO decision on how to display it.
5. 1:00–1:14: a 14 s hold on figures standing around the fallen trainee. The CEO allowed motivated holds, but this one is long.
6. The lane itself reported a duplicate boundary at H149 and too few establishing shots at H007.

## Proposal (needs CEO decision)
- A. **Trim the middle-act script:** cut 60–90 s of sentencing and legal reasoning per film, and swap the dialogue for reenactment cutaways (pictures of the events being discussed), plus reaction and split-screen shots. TTS has to be regenerated, so this needs approval to lift the keep-the-script rule.
- B. Keep the script and only fix the defects above plus add reenactment cutaways. The boring middle act is likely to remain.
- CTO recommendation: A.
