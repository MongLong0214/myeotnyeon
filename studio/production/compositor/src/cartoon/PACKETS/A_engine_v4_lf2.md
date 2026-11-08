# Task A: cartoon engine v4 (higher quality) and the full LF2 cartoon long-form

W = .. You OWN `W/production/compositor/src/cartoon/engine_v4/` and `W/episodes/lf2_daejeon_bank/cartoon_v4/`. Write nothing else; earlier pilot files are read-only references.
- No Blender or 3D; no paid AI; no network; no uploads.
- Another lane (Task B, N18) imports your engine read-only. When the engine API is stable, write `engine_v4/READY_ENGINE.txt` with a short API note.

## Owner direction

1. "롱폼 2개 더 높은수준으로 디벨롭해" (11-01): develop the long-forms to a much higher level.
2. Earlier: 2D cartoon in the Shorts style, with a Rick and Morty FEEL (tone only), and no Blender.

The 45 s pilot (`episodes/lf2_daejeon_bank/cartoon/pilot_45s.mp4`, `src/cartoon/*_v3.tsx`) had these CTO-found weaknesses. Fix all of them:
- stiff acting: characters stand in a frontal row;
- blank oval faces on the bank staff, which look unfinished;
- almost a single background, the parking lot;
- weak expressiveness: no exaggerated faces or poses, no camera-angle variety.

## Engine v4 (React/SVG in Remotion, reusing the toon style)

- **Characters.** Layered puppets with:
  - multiple heads per angle (front, 3/4, profile, back);
  - expressive eyes (pupil wobble, squint, wide), eyebrows and mouth shapes (A, E, O, M, F visemes from the narration audio);
  - arm/hand poses and a walk/run cycle;
  - squash/stretch and secondary motion.
  Bank staff get simple, non-identifying cartoon faces, not blank ovals. Robbers and defendants stay faceless or silhouette.
- **Staging.** Shot types (wide, medium, close-up, over-the-shoulder, low and high angle), 2.5D parallax layers, eased camera moves, and cuts every 2–3 s with purpose. Mood colour grading per scene: night, tense, courtroom.
- **Locations.** Draw every location the script needs, at least 6 distinct sets: bank exterior, the parking lot from 2 angles, streets and getaway, investigation room, the forensics lab, the courtroom.
- **Graphics.** Animated maps, timelines and evidence cards in the same toon style. Subtitles are the only body text.
- **Sound.** The existing narration (`episodes/lf2_daejeon_bank/audio/`) is unchanged. Add a local licensed music bed and SFX, if any are licensed in `W/assets`, ducked under the voice.

## The LF2 episode

- Follow `script_v1.md`, `beats.md` and `facts.md` (verified). Do not add actions or situations that are not in the facts as if they were facts. Staging reconstructs only what the sources support; imply violence and death, never show them.
- Render the full episode to `episodes/lf2_daejeon_bank/cartoon_v4/lf2_cartoon_v4_1080p.mp4` (1920×1080, 30 fps), plus a share copy at 640×360.
- QA (`qa.json`):
  - duration matches the narration;
  - lip-sync onset;
  - subtitle sync;
  - no empty or static shot over 3 s;
  - shot-type variety;
  - the red lines;
  - a contact sheet of every cut (`sheet.jpg`).
  Look at the sheet yourself and fix every off-model drawing, overlap or clipping before you finish.

## Final message (short, Korean)

The paths, what changed from the pilot, the QA numbers, and anything unfinished.
