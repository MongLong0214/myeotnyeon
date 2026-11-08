# Task D: LF2 cartoon v4 — review-only analysis of the existing file (no re-render, no edits to sources)

W = .. Input: `W/episodes/lf2_daejeon_bank/cartoon_v4/lf2_cartoon_v4_1080p.mp4`. Read it only. Write only into `W/episodes/lf2_daejeon_bank/cartoon_v4/review/`.

1. **Motion and transitions.** For every cut (detect them, or use the shot list), save a strip of the 4 frames before and 4 after the cut, plus 6 evenly spaced frames inside the shot, in chronological sheets. View the sheets yourself. Record: popping, off-model drawings, clipping or overlap, frozen characters, awkward transitions.
2. **Voice.** Run ASR (local mlx_whisper) on the final mix and compare it with `script_v1.md`. Report missing, duplicated or garbled words and audible artifacts.
3. **Sync.**
   - subtitle start and end against the ASR word timestamps (max and mean error);
   - mouth-open onset against syllable onset, using the engine's viseme track if available, otherwise an image-based mouth ROI.
4. **Loudness.** Integrated LUFS, true peak, and how much the music ducks under the voice.
5. Write `review/report.md`:
   - the numbers;
   - a list of concrete defects with timecodes;
   - the stated limit: no real-time playback viewing.
   Write `READY.txt`: `READY <defects>`.

## Final message (short, Korean)

The counts, the main defects with timecodes, and the limits.
