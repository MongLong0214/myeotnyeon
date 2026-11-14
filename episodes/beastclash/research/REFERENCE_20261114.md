# Beast Clash reference study (measured 2026-11-14)

8 Shorts published after 2026-08-16, found via Data API search, measured from the downloaded files.

| id | channel | views | published | dur s | cuts (ASL s) | 1st motion s | 1st word s (words/s) | stats | fight actions | flashes | text cap-h, words | ending | style |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| yuWS2EmKmHI | VITMI | 3,376,807 | 10-27 | 32.3 | 28 (1.1) | 0.03 | 0.0 (1.6) | none | 7 bouts, 1 hit each | 2 | 4.5%, 1 | gag twist (tank), no CTA | 2D flat cartoon + meme inserts |
| -9CRhQnZZ6A | Chal Ve Facts | 2,956,123 | 09-13 | 41.9 | 22 (1.8) | 0.07 | 0.0 (2.9) | none | ~6 real clashes | 0 | watermark only | spoken like/subscribe | real footage, heavy colour filters |
| YAU9y180WSY | The animal adventure in Hindi | 2,509,069 | 10-05 | 41.1 | 24 (1.6) | 0.03 | 0.0 (4.2) | 1 overlay ("743 PSI") | 0 | 0 | 6% labels, 2-3 | subscribe animation + poster card | real footage, oversaturated |
| 34v8ETJTtNQ | Tales Of The Wilderness | 736,882 | 11-04 | 33.4 | 37 (0.9) | 0.03 | 0.0 (3.6) | spoken, in captions ("300 / 1,000 pounds") | 0 | 0 | 3%, 1 | spoken verdict "not even close", hard cut | podcast clip + real b-roll |
| N7k_qgconJU | MindGlitch | 438,928 | 09-08 | 20.2 | 8 detected, ~13 seen (~1.5) | 0.04 | 0.0 (3.9) | spoken, in captions (mph, seconds) | 0 (race) | 4 | 2.5%, 1-3 | split screen + "who are you betting on?" | real footage, some AI-looking |
| nulM8xhI-T0 | Unknown Past | 252,227 | 10-27 | 10.1 | 0 (10.1) | 0.04 | no speech (sfx/music) | none | ~3 lunges, one take | 0 | none | no verdict; ends in opening pose (loops) | photoreal, looks AI-generated |
| 7gOrSZBfxOM | The Chickenossaurus | 207,313 | 08-29 | 43.7 | 0 detected, ~5 seen | 2.77 | no speech (audio from 2.2) | none | 2 (pounce, tussle) | 0 | none | nuzzle, 4 s fade to black | 2D cartoon, fan animation |
| VM2Pswlveoo | Mammoth Animal's Animation | 152,549 | 09-30 | 45.0 | 8 (5.0) | 0.03 | no speech (music) | none | ~3 clashes + knockdown | 0 | none | winner stands over loser | 3D game-sim |

Medians: duration 37 s; ASL 1.7 s (detector 2.0); first motion 0.04 s; first word 0.0 s on the 5 narrated; narration 3.6 words/s; fight actions 2.5; caption cap height ~3.8% (4 with text), 1 word at a time.

## Method and limits
Cuts: ffmpeg scene score > 0.30, merged within 0.2 s, checked against contact sheets (0.25 s steps for 0-3 s, 2 fps after). The detector missed dissolves and pans (7gOr, N7k); "seen" counts are from the sheets; on yuWS it also counts insert swaps. First motion: first frame-to-frame mean abs luma diff > 0.6 at 180x320. First word: local mlx whisper-large-v3-turbo word start; audio onset (> -40 dBFS) was <= 0.14 s on all but 7gOr. Flashes: luma spike > 35 that decays within 4 frames. Text height: capital height against a 5% grid on one native frame per video. Fight actions, particles, shake and style are my reading of 2 fps sheets, so sub-0.5 s smears or shakes can be missed; none were seen. Not verified: audio was not listened to (speech vs music inferred from whisper output), Hindi narration meaning, AI-generated guesses, retention or any cause of the view counts. Files were 360p (except 7gOr), so fine text is approximate. Sample is 8 videos from 8 queries; lion-vs-tiger raw clips (e.g. f6i93wMYme4, 14.5M) were seen but left out as unformatted footage. No high-view Short in this search used our card format, so the format itself is untested by this sample.

## Principles to take
1. The matchup is on screen and spoken at 0.0 s: both animals or the first clash in frame 1, no title hold.
2. Something new every 1-2 s: new shot, new angle or zoom punch. The top four sit at 0.9-1.8 s ASL.
3. Numbers ride on action. Nobody stops for a stat card; stats are spoken and flashed as one-word captions over moving animals.
4. Captions are one word at a time, 3-4.5% cap height, outlined, mid or lower-mid frame.
5. Narration runs 3.6-4.2 words/s without gaps (the two silent, slow animations are also the two least viewed; correlation only).
6. Contact comes early and often: the top cartoon delivers 7 short bouts, each ending in a visible result plus a reaction beat.
7. End on the payoff or a question, then cut. CTAs are spoken or a 2 s overlay.
8. Close-ups of faces and teeth alternate with wides (eyeballed).

## What we lack
- Opening: our first 2 s is a title card with small animals at the edges; references open on the clash.
- Three static stat cards hold ~6 s with no animal motion; references never stop moving.
- Shot rate: ours changes about every 2 s with the same wide framing; no close-ups, no zoom punches.
- Fight: 3-4 poses on a near-empty background, one impact; no reaction beats, debris or secondary motion.
- Captions: two-line sentences at the bottom; references use one large word.
- Verdict: three text-bar slides (~6 s) of reading; references state the winner in one line or show it.
- Keep: original characters, the A/B question, sourced numbers.
