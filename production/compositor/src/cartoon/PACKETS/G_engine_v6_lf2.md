# Task G: LF2 cartoon v6 — narration-matched shots, cinematic grammar, slightly slower pace

W = /Users/isaac/projects/verdict-kr/work. You OWN `W/production/compositor/src/cartoon/engine_v6/` (start from a copy of engine_v5; do not edit engine_v5) and `W/episodes/lf2_daejeon_bank/cartoon_v6/`. Everything else is read-only, including v5. Write `engine_v6/READY_ENGINE.txt` when the API is stable, because Task H (N18) imports it read-only. Model: gpt-6.1-sol; do not hand off.

Base: `episodes/lf2_daejeon_bank/cartoon_v5/` (script_v2.md, shots.json, assets), facts.md.

## Owner verdict on cartoon v5 (11-01, verbatim)

"아니 컷이랑나레이션이랑 하나도안맞잖아 ㅡㅡ / 그림검수안해? 호흡 조금만 더 느려도돼 / 컷편집도 영화적 문법 최대한 맞춰서해 / 컷튀면안돼"

## Requirements, all mandatory

1. **The picture matches the narration, shot by shot.**
   - Build `shots_v6.json` FROM the narration: one or more shots per sentence or clause.
   - Each shot depicts the subject of the words being spoken at that moment: who, what, where and what action. When the narration names a person, place, object, date or event, that is what is on screen then.
   - Cut points are taken from the word timestamps of the final narration (ASR or TTS alignment) and fall on sentence or clause boundaries, within ±0.12 s.
   - No shot may show something the narration is not talking about. A narrator reaction shot is allowed only when the narration is the narrator's own comment.
2. **Pace slightly slower than v5.** Re-synthesize the narration with the same local Supertonic voice at about 6.8–7.2 syllables/s, with pauses of about 0.2–0.3 s at sentence ends and ≤ 0.15 s inside sentences. Keep the v5 script (`script_v2.md`) unless a line must change so the picture can match it. Facts are unchanged.
3. **Cinematic editing grammar:**
   - open each new location with an establishing or wide shot, then medium, then close;
   - the 180-degree rule and consistent screen direction for movement (a car leaving left keeps going left);
   - eyeline matches;
   - shot/reverse-shot for confrontations (court, interrogation);
   - match on action when cutting during movement;
   - motivated cuts only.
   Transitions are mostly hard cuts on beats; a whip pan or a smash cut only where the energy needs it.
4. **No jump cuts.** Two consecutive shots of the same subject must change the shot size by at least one step or the camera angle by ≥ 30°, or change the subject. Never cut between two nearly identical framings. Characters must not pop position or pose across a cut unless the cut is a deliberate time jump that the narration states.
5. Keep the earlier owner rules:
   - Rick-and-Morty FEEL, original characters;
   - explicit non-gore depiction of the factual violence;
   - victims non-identifiable; deaths not played for laughs;
   - numeric on-screen dates, without filling in an unverified month or day;
   - no Blender, no paid image or video services, no network, no uploads.

## QA (`qa_v6.json`) and review artifacts

- **Alignment table** `alignment.md`: one row per shot, with start–end time, the exact narration words in that span, what the shot shows, and the shot size and angle. Then a self-check column: MATCH / MISMATCH. Fix every MISMATCH before finishing.
- **Cut sheet** `cut_sheet.jpg`: for EVERY cut, the last frame before and the first frame after, side by side, each labelled with the subtitle at that moment. Use it to find jump cuts and mismatches; fix them.
- Numbers: syllables/s, pauses, ASR ≥ 98%, subtitle sync, cut-to-clause-boundary offsets (max and mean), jump-cut detector hits (must be 0), the shot-size sequence per scene, and the red lines.
- Write `READY.txt` only when everything above holds.

Render `cartoon_v6/lf2_cartoon_v6_1080p.mp4` (1920x1080, 30 fps) and a 640x360 share copy.

## Final message (short, Korean)
The paths, the pace, the alignment and jump-cut results, and anything unfinished.
