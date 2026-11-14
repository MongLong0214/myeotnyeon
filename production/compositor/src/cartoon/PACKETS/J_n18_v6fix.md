# N18 v6 correction (CEO FAIL + CTO measurement)
W=/Users/isaac/projects/verdict-kr/work. Target: W/episodes/v4/n18/cartoon_v6/ and the N18 sources under W/production/compositor/src/cartoon/n18/. engine_v6 is READ-ONLY (it is owned by the LF2 lane); new angle drawings go in the N18 source. CEO review in full: /Users/isaac/.hermes/reviews/longform-v6-ceo-review.md

## Blocking
1. F2: H064–094 (160.3–240.0 s) and H121–139 (315.4–360.5 s) only swap the explanation panel while repeating medium and close zooms of the same courtroom or briefing room. Faces and bodies are hidden behind the panels. Rebuild them as acting scenes with gaze and reaction.
2. CTO measurement: cream panel boxes cover characters from H002 to H006 (court ruling, sentencing reasons, incident date, unit name, police findings) and in many shots after that. Remove the panels. Put the information in the subtitle or a short top-corner label.
3. H011→H013 and H014→H018: the planned ±35° is really a frontal SVG crop. Draw real different angles (3/4, side, reverse) or merge the shots.
4. F3: a leftover strip of a cream card's border remains at the top after H020→H021 (46.233 s) and in H024 (51.6–53.1 s). Remove it.
5. CTO measurement: 15 shots are static for more than 1.5 s. Add motion or a camera move to each. List:
H042 1.9s H045 3.9s H047 2.77s H048 2.1s H049 1.63s H140 3.03s H141 5.47s H143 2.63s H144 4.3s H145 1.67s H146 4.87s H147 3.63s H148 2.47s H149 1.8s H150 4.07s
6. Non-blocking: in H049 the phone call is unclear. Do not invent anything the mother did. Make it clear that the call is the one recorded in her letter.

## Shared rules (owner, CEO and CTO)
- **Keep the script, TTS, facts and the current cut times.** Clause-boundary cuts stay. Shots with no new information may be merged or held.
- **Keep the art style and the hard lines.** Explicit cartoon violence is allowed, but no gore close-ups, and victims stay unidentifiable.
- **Do not overwrite the reviewed v6 MP4.** Write the output to `*_v6fix_1080p.mp4` and `_360p.mp4` in the same directory. No new engine version and no new version chain.
- **Picture grammar.** Every shot shows a character acting out the narrated action, gaze or reaction.
  - Repeated zooms in and out of the same frontal drawing are banned.
  - Explanation panels, cards or arrow diagrams that cover a character are banned.
  - Any legal diagram that is truly needed is a small in-scene prop. It moves, and it is on screen for at most 1.5 s.
  - On-screen text is limited to subtitles plus a short place or date label.
- **Dates are numeric** `YYYY-MM-DD` in every on-screen title and subtitle. The spoken narration is not re-recorded.
- **Real angle changes.** An angle change must be a genuinely different drawing (a 3/4 or side view, or a reverse shot). A crop or zoom of the same SVG is not an angle change and counts as a jump cut.
- **Acceptance gate.** The lane does not self-report MATCH. Run this on the final MP4:
  `W/.venv/bin/python W/factory/longform_qa.py <mp4> --shots <shots> --script script_v2.md --facts <facts> --alignment alignment.md`
  - Every [자동] gate must PASS, including C2 static span >1.5 s = 0, C3 and E1.
  - Record the review_runs path in READY_FIX.txt.
  - Also record the list of changed shots, each with a before/after frame pair.
- **Final message:** short, in Korean. Changed shots, the result of each gate, and anything unfinished.
