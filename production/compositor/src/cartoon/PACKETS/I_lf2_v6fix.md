# LF2 v6 correction (CEO FAIL + CTO measurement)
W=/Users/isaac/projects/verdict-kr/work. Target: W/episodes/lf2_daejeon_bank/cartoon_v6/ (build.py, LF2.tsx, shots_v6.json, alignment.md). Engine: W/production/compositor/src/cartoon/engine_v6 (owned by this lane). CEO review in full: /Users/isaac/.hermes/reviews/longform-v6-ceo-review.md

## Blocking
1. F1: The top-of-screen dates at 00:14.700, 04:02.700 and 05:31.200 still use 년/월/일 words. Change them to 2001-12-21, 2023-01-16 and 2023-12-14, and fix any subtitle carrying a date the same way.
2. F2: V6_041–060 (97.2–154.7 s) and V6_101–129 (260.6–342.2 s) are dominated by central panels, arrows and the same courtroom backdrop. Rebuild them as scenes where characters act: investigators, the DNA comparison, interrogation, the courtroom with the judge, defendant and prosecutor and their reactions, and so on.
3. CTO measurement: 86 shots are static for more than 1.5 s (no body or camera motion; 244 s, 69% of the film). Every one of them needs character motion or a motivated camera move. List:
V6_001 1.9s V6_004 2.7s V6_005 3.17s V6_006 2.97s V6_007 2.3s V6_008 2.63s V6_012 1.87s V6_013 3.57s V6_014 2.1s V6_015 4.07s V6_016 1.53s V6_018 2.53s V6_019 2.03s V6_021 1.87s V6_022 3.6s V6_023 1.9s V6_026 1.77s V6_027 2.23s V6_028 3.07s V6_029 2.4s V6_030 3.07s V6_033 2.4s V6_034 2.23s V6_035 2.0s V6_037 2.6s V6_038 2.8s V6_039 3.67s V6_040 1.57s V6_041 2.67s V6_042 2.3s V6_043 5.03s V6_044 3.03s V6_046 1.6s V6_047 2.8s V6_049 3.97s V6_050 2.9s V6_051 1.67s V6_054 1.63s V6_056 3.43s V6_058 1.87s V6_060 2.77s V6_061 2.53s V6_062 4.23s V6_064 3.17s V6_065 3.57s V6_067 3.23s V6_068 1.6s V6_074 2.47s V6_077 2.6s V6_078 1.63s V6_079 2.9s V6_084 3.57s V6_089 2.03s V6_090 2.13s V6_091 2.93s V6_095 1.97s V6_097 2.8s V6_099 2.3s V6_100 2.03s V6_101 5.03s V6_102 2.17s V6_103 1.57s V6_104 3.3s V6_106 3.27s V6_107 3.07s V6_110 3.87s V6_111 2.27s V6_112 2.0s V6_113 4.07s V6_114 3.23s V6_115 3.07s V6_117 5.13s V6_118 2.13s V6_119 1.87s V6_121 2.8s V6_122 3.57s V6_124 1.63s V6_125 3.1s V6_126 3.43s V6_127 2.3s V6_128 3.43s V6_129 3.47s V6_130 2.67s V6_131 3.87s V6_132 3.17s V6_133 2.7s
   In particular, V6_003–008 and V6_013–018 (the cold open and the incident) are static cards or empty sets. Replace them with acted scenes: the robbers getting away with the bag, the chase, the parking lot with people in it.

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
