# Motion-number rules from "Opus 5.5 Motion Lab" (@flxrnc; owner 11-07: 참고할만한게있나)

Source text: factory/unslop/ref_flxrnc_motionlab.txt. Its code and prompt blocks were images and were not captured, so use only the text.

Goal: replace the adjectives in our lane packets ("dynamic", "R&M-style", "not AI-looking") with numbers that a lane can implement and a gate can measure. The owner's existing rules stay supreme, in REVIEW_CHECKLIST.md A1–H14 and STYLE_VIDEO.md:
- subtitles centered and 72px;
- base shot 2–3 s;
- characters act at all times;
- every face has eyes, nose and mouth;
- no Blender.

1. Write `factory/unslop/MOTION_NUMBERS.md`, adapted to our 2D Remotion toon at 30 fps and to Shorts at 1080x1920. Cover:
   - easing per move type;
   - spring damping-ratio bands, with our cartoon target (0.3–0.6);
   - anticipation and follow-through in frames;
   - one hero move per shot: secondary moves travel 50–70% as far and start 3–6 frames later;
   - ambient motion: under 5% amplitude on a slow sine that never stops. This is the systemic fix for the "static span" fails;
   - holds: a text hold of at least 0.3 s per word plus 0.5 s, with a slow 2% push during the hold;
   - phone-size exaggeration: key poses pushed 10–30% further;
   - the beat grid: frames per beat = 30*60/BPM, computed from time and never accumulated; cuts on the beat; layout changes on the bar, which matches the 2–3 s base shot;
   - picture leads sound by 1 frame.
2. Add a living **ban list by name** to STYLE_VIDEO.md (this is the "AI look" fix):
   - fade-and-slide-up on every element;
   - everything appearing at once;
   - text that moves while it is read;
   - decorative glow, gradients and particles;
   - linear easing on character moves.
   Our subtitles stay centered: that is an owner rule and is exempt. After every first render, a lane appends any new default it spots.
3. Add a "feedback → numbers" table that translates owner notes into lane instructions. Cover "지루해", "너무 빨라", "AI스러워", "정적이야", "재판씬 동적으로", and every other H-item phrase the owner used.
4. Gate proposals only, no code yet: list them in a section of REVIEW_CHECKLIST.md as PROPOSED, with how each one would be measured:
   - flash rate ≤ 3/s;
   - subtitle contrast ≥ 4.5:1 on every frame;
   - ambient motion never zero inside a shot;
   - SFX hits within 0–1 frame after their visual event, measured from the decoded audio;
   - linear-easing detection on character tracks;
   - deterministic render: no Date.now or unseeded Math.random in production/lf_toon or the Shorts render source. For this one, grep the source now and report the findings.
5. Record attribution in factory/THIRD_PARTY.md: an article, ideas only, no copied code.

Do not render or upload anything. Report a changed-file list, the grep findings for item 4, and a 10-line summary.

## Follow-up queued 11-07, from the Claude-Code-Video-Toolkit link audit (apply after the motionlab and hooklib lanes finish)
- Proposed gate: a **pre-render subtitle timing lint**, a pattern from Yusuke710/manim-skill (lint-subtitles.py, MIT). Before any render, simulate each subtitle's on-screen time against the TTS alignment:
  - each subtitle holds at least 0.3 s per word plus 0.5 s;
  - characters per second stay within the reading budget;
  - lines stay within the line-length and line-count limits.
  This saves wasted renders.
- Caption pagination idea from digitalsamba Captions.tsx (MIT): break pages by sentence or pause plus maxChars. Its karaoke per-word highlight is REJECTED because it reads as an AI template (owner rule).
