# Task E: cartoon engine v5 (Rick-and-Morty-level energy) + LF2 rewritten, re-voiced and re-animated

W = /Users/isaac/projects/verdict-kr/work. You OWN `W/production/compositor/src/cartoon/engine_v5/` and `W/episodes/lf2_daejeon_bank/cartoon_v5/`. Everything else is read-only, including engine_v4 and the v4 outputs. Write `engine_v5/READY_ENGINE.txt` when the API is stable, because Task F (N18) imports it.
- No Blender or 3D, no paid image or video services, no network, no uploads.
- Model: you are gpt-6.1-sol; do not hand off to another model.

## Owner verdict on LF2 cartoon v4 (11-01, verbatim)

"형편없어 더 자극적이고 호흡 빠르게 해 / 실제 릭앤모티 느낌 처럼 시청자가 눈을 뗄수없게 / 지루하지않게 뽑아야돼 / 그리고 년월일 표시 한글로하지말고 숫자로해"

v4 was a calm explainer: a narrator pointing at evidence cards, repeated courtroom shots, slow narration. That is rejected.

## 1. Script v2: provocative and fast, still factual

- Rewrite `script_v1.md` into `cartoon_v5/script_v2.md` using only `facts.md`.
- Shape:
  - a shocking cold open in the first 3 s;
  - the central question within 10 s;
  - an open loop or cliffhanger every 30–45 s;
  - punchy short sentences;
  - a sarcastic, darkly comic narrator persona, satirizing the absurdity rather than mocking the victims;
  - no filler or recap.
- Target runtime about 4:30–5:30; cut what does not drive tension.
- Every claim still traces to facts.md (≥2 sources). No invented events. Violence and death are shown explicitly; see the owner update below.
- **On-screen dates are numeric**, e.g. 2011년 12월 21일 / 2001.12.21 (in subtitles and graphics). Narration may say them naturally.

## 2. New narration

- Synthesize the full script v2 with the local TTS used for the Shorts (Supertonic 3, the same voice).
- Pace: ≥ 7.5 syllables/s, silences ≤ 0.15 s, with energetic delivery.
- Gate: ASR against the script ≥ 98%. Fix any mispronounced numbers with the lexicon.

## 3. Engine v5 animation energy (original characters; Rick and Morty is a FEEL reference only, copy nothing)

- **Character performance:**
  - wild takes (eyes bulge, jaw drop);
  - smear and multiple frames on fast moves;
  - anticipation and overshoot;
  - wobbly line boil (subtle outline jitter at 8–12 fps);
  - eye darts, sweat drops, exaggerated mouth shapes;
  - characters move constantly; no idle standing rows.
- **Camera:** snap zooms, whip pans, crash zooms on reveals, dutch angles in tense beats, quick push-ins, 2.5D parallax. Average shot ≤ 1.8 s in action parts, with varied shot sizes.
- **Comic and satirical beats:** visual gags, absurd cutaway inserts (clearly labelled as illustrative and non-factual), and a sarcastic narrator character with expressive reactions.
- **Sound:** punchy SFX (whooshes, hits, stings, record scratch), drawn from licensed or self-made local sounds only, and a driving music bed that rises at the cliffhangers. Ducking under the voice.
- **Text:** subtitles only, large and bold, with keyword highlight pops. No paragraph boxes. Evidence and graphics appear as fast animated inserts (≤ 1.5 s), not static cards.

## 4. Render, QA and self-review

- Render `cartoon_v5/lf2_cartoon_v5_1080p.mp4` (1920×1080, 30 fps) and a 640×360 share copy.
- QA (`qa.json`):
  - runtime;
  - syllables/s and silences;
  - ASR;
  - subtitle sync;
  - numeric dates on screen (scan the subtitle text: no Korean-word dates);
  - the shot-length distribution;
  - no static span over 1.5 s;
  - the red lines.
- Make `sheet.jpg` of every cut and look at it yourself.
- Compare your first 60 s against v4 honestly: is it obviously more gripping? If not, iterate before finishing.

## Final message (short, Korean)

The paths, the runtime and pace, the QA numbers, what makes it gripping now, and anything unfinished.

## Owner update (11-01, verbatim): depict the violence explicitly

"쓰러지거나 숨지는 장면, 총쏘는장면 등등 적나라하게 다표현해 카툰이라 상관없어"

This REPLACES the earlier 'imply only' rule.
- Show the key violent moments clearly on screen, in cartoon form:
  - LF2: the gun drawn and fired (muzzle flash, impact), the victim falling;
  - N18: the recruit collapsing during the drill, and the emergency.
- Stage each moment as the facts describe it, and nothing more.
- Limits that still apply:
  - the victim is never identifiable;
  - the moment of death is never played for laughs. The satire targets the perpetrators and the institutions, and the tone turns serious at these beats;
  - no lingering gore close-ups (no gushing blood, no exposed wounds). A cartoon blood mark or a stain is fine. This avoids a YouTube age restriction;
  - no invented brutality beyond the facts.
