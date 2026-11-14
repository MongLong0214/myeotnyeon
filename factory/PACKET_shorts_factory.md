# Task: Shorts factory — one command from episode spec to upload package, with machine QA gates

W = /Users/isaac/projects/verdict-kr/work. Build new code under `W/factory/`. Do not modify existing pipeline files in place; import or copy them. Local only: no network, no uploads, no paid AI.

## Why

The owner wants Shorts produced like a factory. Today each Short is rebuilt by a one-off lane that reverse-engineers `W/episodes/quiz/v51_support`, `v52_support`, `v52_q013_q014_support`, `v52_n15`/`v52_n16` and `episodes_n16.py`. Human review then caught defects that machines should catch:
- empty story panels (q013);
- quiz-number collisions (#13/#14 already scheduled);
- a non-series title prefix;
- end-transition stray frames;
- the prosecution demand confused with the sentence;
- facts with fewer than 2 sources.

## Scope (CEO)
Reuse the existing v52 path. Build no new framework and no parallel pipeline. Long-form is out of scope.

## Build

1. **`W/factory/short.py <qid> --no <N>`.** From the episode entry (`episodes.py` or its n16 successor), produce the full v52 Short exactly as the current pipeline does:
   - hero still;
   - v3 body narration unchanged plus the synthesized hook line;
   - push-in;
   - panels with toon/object sets;
   - end card;
   - the END_TRANSITION fix.
   Never overwrite an existing package or upload file: write a new versioned dir if one exists. A failed run leaves no READY marker.
   Output a package dir `W/upload/pkg/<qid>_n<N>/` with:
   - `video.mp4`, `cover.jpg`;
   - `meta.txt` (title, description, pinned comment, in the series format);
   - `qa.json`, `review_sheet.jpg`, `SHA256`.
2. **Machine gates in `qa.json`.** Every gate is PASS or FAIL with its evidence. The package is READY only if all pass.
   - All existing v52 gates: duration 22–40 s; ASR and sync; pace ≥ 7.5 syl/s; silences; hook frame-0/4 gates; push-in; choice/answer timing; end-card transition; loudness; freeze/black.
   - **No empty panel.** Every story-panel interval has illustration content beyond the paper background and stamps; measure by edge or pixel variance against the empty paper template, per scene.
   - **Number.** N must not be in `W/upload/ledger.json`. N must equal the badge, end card and cover text: OCR, or the rendered props.
   - **Title format.** It matches the series pattern: no "형량 퀴즈 #N ·" prefix, ends with the series hashtags, ≤ 100 chars.
   - **Demand vs sentence.** If the episode has a prosecution demand, the narration and answer panel state the sentence as the answer and the demand as 구형, never swapped. Check against the episode's answerHead/facts fields.
   - **Facts.** Every claim maps to ≥ 2 independent publishers. Two sources existing is NOT enough for PASS: also check that the sources describe the SAME case and instance (court, instance, date) and that the demand and the sentence are kept apart. Anything the machine cannot decide is `NEEDS_REVIEW`, not PASS. A package with any NEEDS_REVIEW is not READY until the CTO signs that gate off in `qa.json`.
   - **Red lines:** sexual crimes, minor victims, domestic violence, stalking, living public figures; no gore or collapse depiction; defendants faceless or silhouette.
3. **`W/upload/ledger.json`.** Seed it with the channel state, read from the files and logs in `W/upload` and `W/episodes/quiz/out/업로드_문안.md`:
   - published and scheduled numbers #1–#15 with video ids, where known;
   - #15 = S-eU5rbP9yg (11-05);
   - #16 reserved for q013.
   `short.py` reads it for the number gate. Uploads stay a separate, human-run CTO step; the factory never uploads.
4. **Regression proof.** Rebuild q013 as #16 and q014 as #15 with the factory and compare them with the existing `upload/v52_q013_n16.mp4` and `upload/v52_q014_n15.mp4`:
   - frame count, audio md5, per-frame PSNR (min ≥ 40 dB, or explain every difference);
   - the gates must PASS for both.
   Also show the gates catching known defects:
   - run the empty-panel gate on the old `upload/v52_q013.mp4` and the number gate with N=13; both must FAIL;
   - run the title gate on the old prefixed title; it must FAIL.
5. **`W/factory/README.md`.** Usage in 10 lines.

## Final message (short, Korean)

The command, the gate list, the regression numbers, the defect-catch results, and anything unfinished.
