# Task: implement REVIEW_CHECKLIST.md as mechanical review gates for Shorts AND long-form

W = .. Implement in `W/factory/`. Extend the existing gates, sign-off and input_sha256 binding in `factory/gates.py`; do not rewrite them. Do not modify any existing video or package. No network, no uploads, no paid services. Model: gpt-6.1-sol.

`W/factory/REVIEW_CHECKLIST.md` lists every review miss the owner has pointed out (A1–G2), each tagged:
- [자동]: decided by code;
- [자동+서명]: code produces the evidence and the CTO signs per item;
- [운영]: an operational gate.

## Build

1. **`factory/review_gates.py`**: one function per checklist item, used by both:
   - `factory/short.py` (Shorts);
   - a new `factory/longform_qa.py <video.mp4> --shots shots.json --script script.md --facts facts.md [--alignment alignment.md]` (long-form; it reads the episode's shot list and narration timing).
2. **[자동] gates, with real measurement on the final encoded file:**
   - **C1 pace:** syllables/s and pauses from the final mix ASR or TTS timing. Format windows: Shorts ≥ 7.5; long-form 6.8–7.2, end-of-sentence pauses 0.2–0.3 s, in-sentence pauses ≤ 0.15 s.
   - **C2:** cold open ≤ 3 s and central question ≤ 10 s (from the script markers plus timing); cliffhanger cadence; static span over 1.5 s = 0 (frame-difference detection).
   - **C3:** character-acting shot share ≥ 80% (long-form, from shot metadata AND spot-checked by a simple figure detector if one is available locally); motion share; paragraph-box detection on frames (OCR text area outside the subtitle band = FAIL); prop/graphic insert ≤ 1.5 s.
   - **D2:** cut times against clause boundaries from the word timestamps (±0.12 s).
   - **D3:** jump-cut detector (consecutive shots with the same subject and set and the same shot size, or a high SSIM across the cut boundary) = FAIL; screen-direction continuity from shot metadata; the first shot of each location is establishing or wide.
   - **E1:** a Korean-word date regex over the subtitles and all on-screen text (OCR) = 0; every date shown must exist in the facts table (no invented month or day).
   - **F2:** always write the "실시간 재생 미검수" limit into qa.json.
3. **[자동+서명] evidence generators**, each writing an image or markdown file that the CTO reviews and signs:
   - B1 reference side-by-side sheet;
   - B4 reads-as sheet (key prop and character frames with the script's intended label);
   - C2 first-60-seconds sheet at 1 frame/s;
   - D1/D2 cut sheet: for EVERY cut, the last frame before and the first frame after, plus the MID-SHOT frame of each shot, each with its subtitle text and the shot's narration words;
   - E2 the violence beats from the facts table with the frames at their timestamps.
   These gates stay NEEDS_REVIEW until a CTO sign-off bound to input_sha256 exists. A self-reported MATCH from the production lane is ignored.
4. **[운영] G1/G2:** `factory/upload_precheck.md` with the exact pre-upload and post-upload checklist; uploads stay human-run.
5. **Regression proof: known-bad inputs must FAIL the right gate.**
   - LF2 cartoon v4 (`episodes/lf2_daejeon_bank/cartoon_v4/`): its subtitles contain Korean-word dates such as '이천십일 년 십이월' → E1 FAIL.
   - N18 cartoon v4 (`episodes/v4/n18/cartoon_v4/`): mostly prop cards → C3 character share FAIL.
   - LF2 cartoon v5 (`episodes/lf2_daejeon_bank/cartoon_v5/`): pace 8.17 syl/s → C1 FAIL for long-form; produce its D2 cut sheet so that narration and picture mismatches are visible.
   - Shorts `upload/v52_q013.mp4` → empty panel FAIL (already a factory gate; keep it green).
   - Report which gates fired, and also any gate that did NOT fire on a known-bad input, as a gap.
6. **`factory/README.md`:** add the long-form command and the rule that nothing goes to the CEO or the owner unless every [자동] gate passes and every [자동+서명] item is signed.

## Final message (short, Korean)

The gate list and its implementation status, the regression results (fired and missed), and anything unfinished.
