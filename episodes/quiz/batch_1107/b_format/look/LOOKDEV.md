# B-format look layer (opt-in)

Same 2D cartoon: same rig, characters, thick ink. Nothing changes until a template switches it on.

## Switch it on
- **Whole film:** `<BStandard c={c} look={{film:MyLookFilm}}/>`. `look.film` replaces the episode film and `look.post` draws over it. Without `look`, BStandard renders exactly as before. Examples: `Q021LookFilm` / `Q024LookFilm` in `ShotsQ021.tsx` / `ShotsQ024.tsx`. A mode without an upgraded shot falls back to the original film.
- **Per shot:** wrap the shot in `<Stage cam light impact>` and put content in `<Layer depth>`. Use depth .3 for the view outside the windows, .9 for the wall, 1 for the actors and 1.4 for the foreground. Then draw people with `<Actor .../>` instead of `Who`.
- **Profiling and lite switch:** set the inputProps `lookOff: ['charfx','blur','blend','grain','cast','grade','acting']`.
- **FightRig additions:** new optional props on `ArticulatedGuy` are `mouth`, `blink`, `filter`, `torsoExtra` and `headExtra`. When they are undefined, the drawing is the original.

## Features → how
| Feature | How to enable | Where |
|---|---|---|
| Key / rim / cel shadow on characters | `Actor light="court"|"courtDark"|"street"|"nightStreet"|"homeNight"|"cell"` | BLook `LIGHTS`, `CharFilter` |
| Cast shadow (sun) | `Actor cast` | BActing |
| Contact shadow | `<Contact x y rx light/>` | BLook |
| Haze, floor tint, vignette, grain | automatic in `Stage` | BLook `Atmos` |
| Light spill / window shafts | `<Beam pts color opacity id/>` | BLook |
| Parallax depth layers | `<Layer depth>` under `Stage cam` | BLook |
| Rack focus | `cam.focus` (depth in focus) + `cam.focusAmt` (px per depth unit). Blurs only BlurSvg content and Actors | BLook |
| Dolly / push | `dolly(f,[[frame,{zoom,x,y,focus}],...])` (quintic ease) | BLook |
| Whip + motion blur | `whip(f,at,dur,dx)` → `cam.x` and `cam.blurX` | BLook |
| Handheld drift / decaying shake | `drift(f,amount)`, `shakeAt(f,[[frame,px],...])` | BLook |
| Impact frame (B/W invert, then flash) | `Stage impact={f-hitFrame}` | BLook |
| Speed lines, smear, trail, dust + debris | `SpeedLines`, `Smear`, `Trail`, `Dust` | BLook |
| Springs on hands / head / torso / prop angle (cross-fades, follow-through) | default on `Actor`. Tune with `springs={{hands:[hz,zeta]|null,...}}` | BActing |
| Pose cross-fade between key poses | `poseKeys(t,[[frame,fn],...],fade)`, `blendRig` | BActing |
| Anticipation → action → overshoot → settle | `act(p,a,b,frames,antic,amount)` (motion.ts) | BActing re-export |
| Emotion take (squint, swap, squash, overshoot) | `Actor take={{at,from,amt}}` | acting.ts `takeAt` |
| Breathing, weight shift, blinks, eye darts | `breath`, `weight`, and automatic blink and darts (`darts={false}` to lock the eyes) | BActing |
| Lip sync (Rhubarb rules) | `talk={talkTrack(u.tts,onsetF,offsetF)}`. Each shape holds ≥2 frames, the lips close 1 frame early for ㅁ/ㅂ/ㅍ, final ㅁ/ㅂ closes, short pauses keep the shape, and the track leads the audio by 1 frame. Angry faces keep the clenched-teeth design with the jaw opened by the viseme | BActing |
| Hand library | `hand(slot,'point'|'fist'|'open'|'relaxed'|'grip'|'hold',object?,rot?)`. Sets the side automatically, and props are held at the wrist | BActing |
| Suit tie swing | automatic for `look:'suit'` | BActing |
| Detailed sets with Korean signage | `CourtOut/CourtWall/CourtDais/CourtRailPlus`, `AlleyOut/AlleyWall/AlleyNear`, `HomeOut/HomeWall`, `CellOut/CellWall` | Sets.tsx |

## Render cost
These are wall-clock ms per frame at concurrency 4. Three interleaved runs were made on a shared machine at load average 35–70, so read every number as ±30%.

| Shot (30 f) | Before | Full look | Lite (`lookOff: blur,grain,cast,blend`) |
|---|---|---|---|
| q021 street (3 actors) | 240 | 536 (2.2×) | 305 |
| q021 cell | 79 | 356 (4.5×) | 275 |
| q024 night | 141 | 574 (4.1×) | 435 |
| q024 fight | 153 | 574 (3.8×) | 395 |
| Sum of the three runs | 1866 | 6694 (**3.6×**) | 4721 (**2.5×**) |

**Whole Short (estimate):** about 75% of frames are film. The full look then comes to about 2.9× and lite to about 2.1×.

**What costs what:** the character light filter (`charfx`) costs about 120 ms per hero character per frame. The next costs are focus blur, then the atmosphere layers and acting springs, at about 40–60 ms each. Rack focus used to be a CSS blur over the full frame and that was the biggest cost; it now blurs only BlurSvg content and Actors.

## Tools
- `node look/render_look.cjs <qid> <BEFORE|LOOK> "<from-to:out.mp4>,..."` renders ranges, or use `... stills <dir> <f,f>` for stills.
- `look/compare.sh <name> <idx>` writes the side-by-side PNG, the 2-second strip and the review sheets to `episodes/quiz/lookdev/compare/`.
- `node look/cpuprof.cjs <qid> <from> <to> <comp> <off,...>` times one configuration.

---
# v2 ("full2"): opt-in, no render-time limit

**Turning it on.** For a B3 spec, set `"look":"full2"` in the case. `"full"` keeps the v1 look unchanged, and no `look` keeps the original drawing. In `B3Kit.tsx`, `P3` then draws `Actor2` and uses the narration lip-sync track. For hand-built shots, use `Actor2`, `Look2` and `v2/Shots2.tsx` (examples: `FILMS_V2`). The proof compositions are `LOOK1` (v1) and `LOOK2` (v2) in `look/entry.tsx`.

**Per episode:** run `python3 look/v2/lipdata.py <qid>`, then add the JSON to `LIPDATA` in `v2/Lip.ts`. Without that step, the mouths fall back to evenly spread syllables.

**FightRig additions:** `hair` (a transform on the hair group), `noBrows`, `rigExtra` and `arm0Layer` (`back|front|top`). When unset, the drawing is the original.

| Feature | How |
|---|---|
| Hair sway on head turns and impacts | automatic; set the amount with `hairAmt` |
| Planted-foot walk (no sliding) | `walk={{x0,v,from,cycle,stance,lift,arms}}`; read the position with `xAt(o,f)` |
| Sit-down / stand-up | `sit={f=>0..1}` and `seat` (hip height); a chair prop is in `Shots2` |
| Key poses | `POSE.lean/slump/recoil/point/armsCrossed/handsOnKnees` (headInHands DISABLED: throws) |
| Pose-to-pose with overlap | `poseKeys2(t,[[frame,fn]],fade)` → `applyPose`. Hips move first, torso +2 f, arms +3 f, head +5 f, then springs |
| Arms crossed or head in hands, layered correctly | `arm0="top"` (or a function of f) |
| Eyes lead the head | `lookAt={f=>-1..1}`. The gaze runs 3 frames ahead of the sprung head |
| Brows and cheeks that move with emotion; blinks on beats | automatic from `expr`, the takes (`take=[{at,from,amt}]`) and loud syllables; add extra blink frames with `blinks=[frames]` |
| Lip sync | `talk={talkTrack2(tts,onF,offF,LIPDATA[qid].rms)}`. Syllables are placed on the real voiced runs and follow the Rhubarb rules. Openness follows loudness. Angry and sad faces keep their own mouth designs |
| Cel-shade band on the face and torso, subtle rim light | automatic when `light` is set; turn it off with `shade={false}` |
| Fabric folds that follow the pose (shoulders, waist, elbow creases) | automatic; turn them off with `folds={false}` |
| Tears / sweat | `fx={{tears:[from,to],sweat:[from,to]}}` |
| Snap zoom, whip between characters, slow push, Dutch tilt | `snapZoom`, `whipBetween`, `slowPush`, `dutch` (Look2) |
| Foreground occluders | `ForeBars`, `ForeRail`, `ForeMonitor`, `ForeLamp`, placed in `<Layer depth≥1.3>` |
| Ink-splash impact (no gore), paper flutter, falling papers | `InkSplash`, `FlutterPaper`, `FallingPapers` |
| Night light flicker | `Flicker` and `flickerAt` (the door spill also uses it) |
| Particles | `Motes` (dust in light beams), `Rain`, `PaneDrops` |
| Background depth of field | in v2 the wall layers blur as well (no `noBlur`) |

**Cost:** about 1.3–2× the v1 look per film frame, i.e. 270–870 ms per frame against 180–530 ms for v1, measured on a loaded machine.

**v2 status (2026-11-13): READY with light ON.** Pass `light` to Actor2 as normal; the old workaround of dropping it is no longer needed. Fixed in this pass:
- The rim-light arc beside faces is gone: the rim filter is clamped to the opaque silhouette and the shade clip is in the right coordinate space.
- Cel shadows now fall away from the light.
- Closed eyes (blink, squint, crying) are drawn as skin lids with a lash arc.
- Under heavy lids (tired, smug, serious, half blink) the pupil drops below the lid line, so the eyes are never empty circles.
- The sit-down shot ends in a slump with hands on knees.

`POSE.headInHands` is DISABLED (calling it throws) until its hand layering over the face is tested. "full" (v1) is unchanged.
Proof: `episodes/quiz/lookdev/compare_v2/eyes/` and `compare_v2/arcfix/`.
