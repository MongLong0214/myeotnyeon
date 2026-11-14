# Reference absorption matrix (2026-11-08)

Scope: every owner reference with a `research/*/REPORT.md` and the owner URLs found in the main transcript.
Each status is backed by a file and its call site in the current pipeline: N18 (`production/lf_toon/n18_film/Cut.tsx` → `Scenes.tsx`), LF3 (`lf3_heist/FilmV2.tsx`), the shared engine (`production/lf_toon/src`), the Shorts factory (`factory/make.py` → `gates.py`/`review_gates.py`) and the long-form review (`review_gates.evaluate` → `CODE_LINT`, `FRAME_QA`). Report claims did not count as proof.

Statuses: **IN-USE** (adopted, and a current pipeline calls it) · **UNUSED** (the code exists, but no current film or factory step calls it) · **NOT** (not adopted) · **REJECTED** (with the reason) · **NOW** (implemented in pass 1) · **NOW2** (pass 2; opt-in and tested, with no change to films under review).
Value/effort: H/M/L, S/M/L. "Idea" means no code was copied.

**Counts (136 items; A11 duplicates O4):** IN-USE 64 · NOW2 27 · NOW 6 · NOT 20 · REJECTED 12 · UNUSED 7.

## cinecode — MIT (Sarp Yıldız)
| # | Item | Status | Evidence | V | E |
|---|---|---|---|---|---|
| C1 | scene_check repeats / static action / pops | IN-USE | `factory/lib/code_lint.py` `check_video` → `review_gates.code_lint_gate` | H | S |
| C2 | Rubber-hose single-path arms | IN-USE | `src/ToonRig.tsx` `arm()` (one Q path, sleeve dash) | H | S |
| C3 | Body acting per emotion | IN-USE | `ToonRig.tsx` `ACTING`/`actedRig` | H | S |
| C4 | Character model sheet before scenes | **NOW2** | `src/insets_stills.tsx` `model-sheet` → `preview/insets/model-sheet_f0.png` (found: tie on back view, two eyes in side view) | M | S |
| C5 | anticipate/back/spring/act/lag helpers | IN-USE (thin) | `src/motion.ts`; only `settle` (`lf3_heist/Scenes.tsx`) and `back` (`lf3_heist/Cast.tsx`) are called | M | S |
| C6a | handheld / follow camera | IN-USE | `src/camera2d.ts` `handheld` ← `n18_film/Scenes.tsx` | H | S |
| C6b | whip / iris / retime / Hermite path camera | **NOW2** | `src/camera2d.ts` `whipPan`/`whipBlur`/`hermitePath`/`retime`/`irisRadius`; `tests/absorb2.test.ts` | M | M |
| C7 | 2.5D parallax planes | IN-USE (LF3 only) | `lf3_heist/ScenesCold.tsx`, `FilmV2.tsx` | M | M |
| C8a | Shot-rhythm check (cv ≥ .30, no run of 5 alike, acts vary) | **NOW** | `factory/lib/code_lint.py` `check_rhythm` → CODE_LINT | H | S |
| C8b | Camera-move deck draw | NOT | — | M | S |
| C9 | scifi-toon grammar doc | NOT (tone covered by `LONGFORM_ANIMATION_BIBLE.md`) | — | L | S |
| C10 | RMS/spectral-centroid audio lip-sync | NOT | — | M | M |
| C11 | Caption grouping, balanced wrap, hold time | IN-USE | `factory/lib/captions.py` `split`/`wrap` ← `make.py s_captions`, N18 subtitles | H | S |
| C12 | SFX peak on the contact frame / whoosh before cut | **NOW2** | `factory/lib/sfx_bank.py` `place` (peak on cue, error ≤ 1 ms), `whoosh_before_cut` | M | S |
| C13 | Kenney CC0 SFX | **NOW2** (opt-in; film mixes not wired) | `sfx_bank.place` accepts local files, e.g. `sfx/kenney/*` | M | S |
| C14 | TTS clean chain (voice_treat) | **NOW2** | `factory/lib/voice_treat.py` (cinecode MIT), 50 Hz rumble −8.9 dB in test | M | S |
| C15 | Per-scene loudness ±3 LU (`scene_check sound`) | **NOW2** | `code_lint.check_scene_loudness`, opt-in `review_inputs.scene_loudness` | M | S |
| C16 | Reference format measurement | IN-USE (own) | `references/frame_metrics.py`, `research/format_v4/analyze` | M | S |
| C17 | Curiosity map, twist every 60–90 s | IN-USE (rule) | `LONGFORM_ANIMATION_BIBLE.md:44` | H | S |
| C18 | Hook: motion in 0–2 s | IN-USE | `factory/gates.py:258` `hook_motion` | H | S |

## Tesseract — PROPRIETARY (Mirage terms): ideas only, nothing copied
| # | Item | Status | Evidence | V | E |
|---|---|---|---|---|---|
| T1 | 2-bone IK arms/legs, head look-at | IN-USE | `ToonRig.tsx` `solveArm`/`solveLeg`; `acting.ts` `eyeLine`/`listenHead` | H | M |
| T2 | Pause-based subtitles (silencedetect −45 dB/0.2 s) | IN-USE | `captions.py` `silences_from_audio` | H | S |
| T3 | Per-cut filmstrip / overview sheet | IN-USE | `review_gates.py` `cut_sheet` (D1), `frame_qa` contact sheets | M | S |
| T4 | Cue map (line → event → SFX peak → music gap) | **NOW2** (SFX part only; music gaps NOT) | `sfx_bank.place` cue list | M | M |
| T5 | Punch-in that keeps the eye midpoint fixed | UNUSED (now tested) | `camera2d.ts` `punchIn`; `tests/absorb2.test.ts` keeps the eye point fixed | M | S |
| T6 | Loudness/TP and ducking | IN-USE | `factory/lib/audio_mix.py` (−14 LUFS, TP ≤ −1, word-keyed ducking) ← both `finish_audio.py` | H | S |
| T7 | Self-made SFX presets | IN-USE (numpy synth, not aevalsrc) | `n18_film/finish_audio.py` | M | S |
| T8 | Two independent critic agents | REJECTED: process overhead; the CEO review gate already does this | — | L | M |

## OpenToonz — BSD-3: ideas only
| # | Item | Status | Evidence | V | E |
|---|---|---|---|---|---|
| O1 | Per-key interpolation types | UNUSED | `motion.ts` `Ease`/`k()`; no film passes step/expo/bezier | M | S |
| O2 | Posing on 2s/3s | **NOW2** | `motion.ts` `onN` | M | S |
| O3a | Line boil | IN-USE | `ToonRig.tsx` `boil` | M | S |
| O3b | Smear / zanzo multiples | **NOW2** | `ToonRig.tsx` `ArticulatedGuy smear`; `ABSORB_DEMO.png` f33 | M | S |
| O4 | Korean jamo → viseme lip-sync | **NOW2** | `ArticulatedGuy viseme` ← `lipsync.visemeTrack`; `ABSORB_DEMO.png` | M | M |
| O5 | Arc motion paths | **NOW2** | `motion.ts` `arcPoint` | M | S |
| O6 | Body turn by view swap | IN-USE | `ToonRig.tsx` `View` ← `n18_film/Scenes.tsx` | H | M |
| O7 | ARAP mesh deform | REJECTED: L effort; view swap covers turns | — | L | L |

## AI-Video-Factory — MIT (Ersin KOÇ)
| # | Item | Status | Evidence | V | E |
|---|---|---|---|---|---|
| A1 | 2-bone IK, elbow ≤ 150° | IN-USE | `ToonRig.tsx` `solveArm`, `ELBOW_FLEX` | H | S |
| A2 | Strain list as a gate reason | NOT | — | L | S |
| A3 | Wrist roll | IN-USE | `ToonRig.tsx` `handRoll` | M | S |
| A4 | keepInSpace | UNUSED | `ArticulatedGuy space` prop; no film passes `space=` | M | S |
| A5 | Desk-height IK | NOT | — | M | M |
| A6 | Forearm lag 0.08 s | UNUSED | `motion.ts` `lag` (no caller) | L | S |
| A7 | Expression table, split brows | IN-USE | `src/expressions.ts` ← 3 importers | M | S |
| A8 | Idle / listener acting | IN-USE | `acting.ts` `listenHead` ← 7 scene files | H | M |
| A9 | Voice-beat nods/gestures (Korean syllables) | **NOW2** | `src/beats.ts` (`speechBeats`, `nodAt`, `strokeAt`), tested | M | M |
| A10 | First-shot build-in | NOT | — | L | S |
| A11 | Visemes | see O4 (UNUSED) | — | — | — |
| A12 | Tripod shake / motion blur | handheld IN-USE; blur NOT | `camera2d.ts` | L | S |
| A13 | Transition cycling | **NOW2** | `camera2d.ts` `seamFor` | M | S |
| A14 | Same-shot-size variety guard | **NOW2** | `code_lint.check_variety`, opt-in `review_inputs.variety` (needs shot `size`) | M | S |
| A15 | Close-up / macro insert | UNUSED | `src/MacroInsert.tsx`; only `insets_stills.tsx` | H | M |
| A16 | Circular magnifier callout | UNUSED | `src/MagnifierInset.tsx`; only `insets_stills.tsx` | M | M |
| A17 | Speech bubbles | **NOW2** | `src/Overlays.tsx` `SpeechBubble` | M | S |
| A18 | Light wash | NOT | — | L | S |
| A19 | Silence-based word alignment | REJECTED: local whisper already aligns | — | L | M |
| A20 | Stage resume | IN-USE | `factory/make.py` `input_hash`/`state` | M | S |
| A21 | Changed-shot chunk render cache | UNUSED (dry-run OK) | `tools/chunk_cache.py plan` on N18 `film_data.json`: 136 shots keyed; no render command uses it yet | H | M |
| A22 | Code lint (face cut, text on face, overflow) | IN-USE | `factory/lib/code_lint.py` → CODE_LINT | H | M |
| A23 | Long-form → Shorts segment | IN-USE | `lf3_heist/shorts_build.py` | H | M |
| A24 | Thumbnail frame score | NOT | — | M | S |
| A25 | Cold open, re-hook every 60–90 s | IN-USE (rule) | `factory/unslop/HOOKS.md`, BIBLE:44 | H | S |
| A26 | Paid gateway, Agent SDK, likeness, 3D, GSAP | REJECTED: paid, likeness, 3D ban or non-MIT | — | — | — |

## x-seeconvm — ClaudeAnimationBase MIT (John Heibel); PDoomVideo has no licence, so ideas only
| # | Item | Status | Evidence | V | E |
|---|---|---|---|---|---|
| S1 | "Reads" timing sheet per shot | IN-USE (rule) | `LONGFORM_ANIMATION_BIBLE.md` "Reads sheet per shot" | M | S |
| S2 | emotions() acted change (squint → swap → take → overshoot) | **NOW** | `src/acting.ts` `takeAt`; `ToonRig.tsx` `ArticulatedGuy take` | H | M |
| S3 | Prop hooked to the arm end, no twinned arms | IN-USE | `ToonRig.tsx` twin guard, scene-prop shift | H | M |
| S4 | strip / 360 px phone test / crop-at | IN-USE (strip and phone); crop-at NOT | `factory/lib/phone_check.py`, `n18_film/strip.py` | M | S |
| S5 | Worst-3 critique loop + partial re-render | IN-USE (partial re-render: `n18_film/render.cjs range a-b`); fixed worst-3 loop NOT | — | M | S |
| S6 | Stacked spring camera | **NOW2** | `motion.ts` `springTo` + `SPRING.base` (camera/containers) | M | S |
| S7 | A transition at every seam | **NOW2** (helpers) | `seamFor`, `whipPan`, `irisRadius` | M | M |
| S8 | On twos | **NOW2** | `motion.ts` `onN` | M | S |
| S9 | Reference → style guide | IN-USE | `factory/unslop/STYLE_VIDEO.md`, `research/format_v4/spec_v4.md` | M | S |
| S10 | HOOK–PROBLEM–REVEAL–PROOF–CLOSE | IN-USE | `factory/BEATSHEET.md` | M | S |
| S11 | Motifs that escalate, opening/ending rhyme | IN-USE (rule) | `LONGFORM_ANIMATION_BIBLE.md` "Same set, bigger each return", "One prop motif" | M | S |
| S12 | One scene per file | IN-USE | `lf3_heist/Scenes*.tsx` | L | S |
| S13 | librosa BGM beats | NOT | — | L | S |
| S14 | Seedance, Clawd design, PDoom code/music | REJECTED: paid, trademark, no licence | — | — | — |

## x-aiwithvinay — ideas only
| # | Item | Status | Evidence | V | E |
|---|---|---|---|---|---|
| V1 | Required camera/SFX/beat fields per scene | IN-USE (Shorts spec) | `factory/shorts_rules.py` `check_spec` (twist, subscribe gag) | M | M |
| V2 | Top status badge (사건 당일 → 1심 → 항소심) | **NOW2** | `src/Overlays.tsx` `StatusChip`; `ABSORB_DEMO.png` | M | S |
| V3 | In-clip reaction beat (expression swap + push-in) | **NOW** (via S2 take) | `ArticulatedGuy take` | H | S |
| V4 | "Then vs now" topic axis | NOT | — | L | S |
| V5 | Silent visual gag before the narration | IN-USE (rule) | `LONGFORM_ANIMATION_BIBLE.md` "Shorts: silent gag option for 0–2 s" | M | S |
| V6 | About 4 s clip with an inner change about every 2 s | IN-USE (rule) | `review_gates.py` `pace_policy` (H14 2–3 s) | H | S |
| V7 | Gemini/Flow pipeline, reference image | REJECTED: paid/watermark; the SVG rig is already consistent | — | — | — |

## youtube-agent-skill (utillayer) — MIT
| # | Item | Status | Evidence | V | E |
|---|---|---|---|---|---|
| U1 | Retention cliffs | IN-USE | `factory/lib/retention.py` ← `channel/analytics/retention_pull.py` | H | M |
| U2 | Independent fact check | IN-USE (procedure) | `factory/FACTCHECK_PROMPT.md`, `lib/sourcekit.py` | H | S |
| U3 | Title/thumbnail pair | IN-USE | `shorts_rules.check_pair` | M | S |
| U4 | Chapters | IN-USE | `factory/lib/chapters.py` ← `n18_film/deliver.py` | M | S |
| U5 | Korean hook scorer | NOT | — | M | M |
| U6 | Long-form → Shorts candidates | IN-USE | `lf3_heist/shorts_build.py` | H | M |
| U7 | TTS script lint (numbers, names) | IN-USE | `review_gates.py` `pronunciation`, `fresh.lexicon` | M | S |
| U8 | Per-channel voice.md | IN-USE | `channels/*/voice.md` | M | S |
| U9 | Hashtag, 5,000-byte description, 60 s Content ID rules | **NOW2** | `factory/lib/upload_rules.py` | M | S |

## youtube-agent-skill (Jakes) — MIT
| # | Item | Status | Evidence | V | E |
|---|---|---|---|---|---|
| J1 | Retention axis guess breaks on ≤ 100 s videos | **NOW** | `retention.py` refuses an ambiguous axis; new `--unit` | H | S |
| J2 | © Jake Schincariol in the ported-file headers | **NOW** | `shorts_rules.py:105`, `FACTCHECK_PROMPT.md:3` | M | S |
| J3 | Rule: no unsourced % or multiples in hook examples | **NOW2** | `factory/unslop/HOOKS.md` | M | S |
| J4 | Loop-back check | IN-USE (frame) | `shorts_rules.loop_diff` | M | S |
| J5–7 | Jakes tools, viral multiple, "74 hooks" claim | REJECTED: defective or duplicate | — | — | — |

## xilo-opus-video — MIT (Kianzzz)
| # | Item | Status | Evidence | V | E |
|---|---|---|---|---|---|
| X1 | Spring presets (4 levels) + target stacking | **NOW2** | `motion.ts` `SPRING`, `springTo` | M | S |
| X2 | Waveform/spectrum PNG as audio evidence | **NOW2** | `factory/lib/audio_evidence.py` (waveform/spectrum PNG + LUFS/TP json) | M | S |
| X3 | Worst-3 + `--frames` partial re-render, max 3 rounds | partial, see S5 | `n18_film/render.cjs range` | M | S |
| X4 | Cue-time SFX synthesiser | IN-USE (equivalent) | `n18_film/finish_audio.py` | M | S |
| X5 | Three plan options | NOT | — | L | S |
| X6 | Default-style ban list | IN-USE (as unslop bans) | `factory/unslop/STYLE_VIDEO.md:156` (named bans) | M | S |
| X7 | Camera pushed onto real UI coordinates | NOT verified (LF3 has UI scenes in `lf3_heist/UI.tsx`, but no coordinate-targeted push was found) | — | M | M |
| X8 | 1-pass normalize, numpy beat tracker, edge-tts, Manim | REJECTED: worse than ours or external | — | — | — |

## ref_channel UCRbkh4MunftbYddrdaVPCHw (이삼이 싸이언스) — ideas only
| # | Item | Status | Evidence | V | E |
|---|---|---|---|---|---|
| R1 | Question by 3.5 s, twist about 6 s | IN-USE | `shorts_rules.check_spec` `twist`/`twist_max` | H | S |
| R2 | Background change about every 1.5 s | IN-USE | `shorts_rules.setting_changes` → SHORTS_RULES | H | S |
| R3 | Big numbers in everyday units | IN-USE | `shorts_rules` life-unit rule + `tests/test_shorts_rules.py` | H | S |
| R4 | Loop ending ≤ 25/255 | IN-USE | `shorts_rules.loop_diff` | M | S |
| R5 | Subscribe gag at 7–8 s | IN-USE | `shorts_rules` `subscribe_window` | M | S |
| R6 | 6.3–6.6 syllables/s, no pause over 0.5 s | IN-USE | `n18_film/qwen_pace.py` (6.4, pauses ≤ 0.18 s) | H | S |
| R7 | Title format (`'키워드'` … 몇 년 나옴?) | IN-USE | `shorts_rules.make_title`/`check_title` | M | S |
| R8 | Characters as reactors (4–6 big reactions) | NOW (tool: take); no count rule | — | M | S |

## x-nowlovepan (thumbnail colours) — no licence, ideas only
| # | Item | Status | Evidence | V | E |
|---|---|---|---|---|---|
| N1 | Yellow numbers, red crime word, 8 % outline, offset shadow | IN-USE (LF3 thumb) | `lf3_heist/Thumb.tsx` (#ffd84d) | M | S |
| N2 | 160 px legibility check | **NOW2** | `factory/lib/thumb_check.py` (160/320 px sheet, text height warning) | M | S |
| N3 | Test & Compare A/B (up to 3) | NOT in code (manual Studio step) | — | M | S |
| N4 | 42 % full darkening, inner frame, "absolute/99 %" claims | REJECTED (owner rule: no exaggerated facts) | — | — | — |

## tts_bakeoff
| # | Item | Status | Evidence | V | E |
|---|---|---|---|---|---|
| K1 | Qwen3-TTS Sohee, speed-matched | IN-USE | `n18_film/qwen_synth.py`, `qwen_pace.py` | H | M |
| K2 | CosyVoice 2/3 next candidate | NOT | — | L | M |
| K3 | NC/research-licence engines | REJECTED: licence | — | — | — |

## x-3three_ai — sound sources; earshot is MIT (Leon Lin)
| # | Item | Status | Evidence | V | E |
|---|---|---|---|---|---|
| E1 | earshot code-made SFX bank (252), peak-aimed render | **NOW2** | `factory/lib/sfx_bank.py` → earshot subprocess (`research/x-3three_ai/src` @4ac3d2a) | H | S |
| E2 | earshot timeline/sheet/critique (model-based) | NOT (needs librosa/transformers; X2 covers the waveform) | — | M | M |
| E3 | Pixabay/freesound/soundeffect-lab/Mixkit | NOT (per-file licence or Content ID check needed; CC0 freesound only) | — | L | S |
| E4 | ElevenLabs SFX | REJECTED: paid and external | — | — | — |

## x-claudecode_love — "Claude Skills 67選" article
| # | Item | Status | Evidence | V | E |
|---|---|---|---|---|---|
| L1 | Subtitle reading-speed lint (via the Toolkit audit, manim-skill) | **NOW2** | `captions.lint(cps_max=)` | M | S |
| L2 | Hook/retention copy (marketingskills, claude-youtube) | IN-USE | `factory/unslop/HOOKS.md`, `STYLE_VIDEO.md` | M | S |
| L3 | git guardrails hook | NOT (changes self-configuration, so it needs an owner request) | — | M | S |
| L4 | PRD/plan/issue skills, paid-API skills, karaoke captions | REJECTED: process overhead, paid, or reads as an AI template | — | — | — |

## ref_channel_tierbaekgwa (티어백과) — ideas only
| # | Item | Status | Evidence | V | E |
|---|---|---|---|---|---|
| B1 | Long-form 형량 사다리 series | NOT (CEO/owner format decision) | `research/topic_scores` candidates only | H | S |
| B2 | Premise by 9 s, first rung by 20 s, no title card | partial (Shorts first word only) | `shorts_rules` | M | S |
| B3 | Title/thumbnail showing only the two end points, split thumbnail | NOT | — | M | S |
| B4 | 6.6–6.8 syllables/s | partial (owner range 6.2–6.6 wins) | `qwen_pace.py` 6.4 | — | — |
| B5 | Silhouette + year/place label | IN-USE | `lf3_heist/Kit.tsx` `Silhouette` | M | S |
| B6 | Picture change about every 2.5 s | IN-USE | H14 `pace_policy` | H | S |
| B7 | Progress chip + chapters | **NOW2** (chip) + IN-USE (chapters) | `Overlays.tsx` `StatusChip`, `lib/chapters.py` | M | S |
| B8 | Shorts cut from one rung of the long-form | IN-USE | `lf3_heist/shorts_build.py` | H | M |
| B9 | Ending recalls the opening; comment question; sources in the description | partial | BIBLE callbacks; Shorts `source_line` | M | S |

## Owner URLs without a `research/<name>` REPORT
| URL | Where it was analysed |
|---|---|
| github.com/kaomei/stickman-video-director | `research/tools/stickman_analysis.md` |
| youtu.be/w_LJ_GQObic, youtu.be/OwQm8ZIZfiQ (엑스톨) | `research/format_v4/extol_formula*.md`, `spec_v4.md` |
| youtu.be/qXAtVD3kzKY (티어백과) | `research/ref_channel_tierbaekgwa/REPORT.md` §8 (scored below) |
| github.com/mromidev/claude-animated-shorts | `references/claude-animated-shorts/ANALYSIS.md`; adopted (`THIRD_PARTY.md`) |
| x.com/flxrnc/… | `factory/unslop/MOTION_NUMBERS.md`, `STYLE_VIDEO.md` |
| x.com/claudecode_love/status/2045082723027751079 | Now `research/x-claudecode_love/REPORT.md` |
| x.com/3three_ai/status/2114545802211103044 | Now `research/x-3three_ai/REPORT.md` (earshot cloned in `src/`) |
| HF TTS models, mlx-audio, fish.audio | `research/tts_bakeoff` |

## Implemented in this pass (NOW)
1. **C8a shot rhythm**: `factory/lib/code_lint.py` `check_rhythm`, a report-only `rhythm` check inside CODE_LINT, which `review_gates.evaluate` runs for every review (cinecode MIT header). Test: `factory/tests/test_code_lint.py`. On real data, N18 `film_data_final_v1.json` has cv 0.33 and a run of 8 similar-length shots at **B11.1–B13.2 (56.9–85.9 s)**. The older `film_data.json` had cv 0.25 and a run of 24.
2. **S2/V3 emotion take**: `src/acting.ts` `takeAt` plus the opt-in `ArticulatedGuy take={{at,from,to,amt}}` prop (ClaudeAnimationBase MIT header). Test: `tests/acting_take.test.ts`. Render: `preview/insets/TAKE_STRIP.png`. **This also fixes an engine bug that affects every caller:** an eyelid more than half shut drew the small arc, so blink peaks (about 3 frames per blink, max 0.94) showed an empty white eye instead of a closed lid. Re-renders will show proper blinks.
3. **J1**: `factory/lib/retention.py` raises on an ambiguous axis (no unit in the header, all positions ≤ 100, video ≤ 100 s or no duration) and has a new `--unit`. API path unchanged. Test: `tests/test_yt_agent_adopt.py`.
4. **J2**: attribution lines.

Tests: factory `test_code_lint`, `test_yt_agent_adopt`, `test_review_gates` pass (56/56). Engine `node --test` passes (8/8). `tsc --noEmit` is clean.

## Pass 2 (NOW2) proof
- Factory: `factory/tests/test_absorb2.py` plus the existing code_lint, captions, review_gates and yt tests. 85/85 pass.
- Engine: `production/lf_toon/tests/absorb2.test.ts`; all engine tests pass (17/17) and `tsc` is clean.
- Stills: `preview/insets/model-sheet_f0.png` and `ABSORB_DEMO.png`.
- Nothing under `n18_film/` or `lf3_heist/` was edited. Every new feature is off by default.
- The eyelid fix is the only change that will show up in existing films, and only when they are re-rendered; `ENGINE_CHANGES.md` lists which films.

## Backlog
- **Unused, waiting on film authoring** (N18/LF3 are owned by another agent): A15 MacroInsert, A16 Magnifier, A21 chunk cache (on the next full render: `chunk_cache.py render --cmd "node n18_film/render.cjs range {a}-{b}"`), T5 punchIn, A4 keepInSpace, O1 ease types, S2 take, V2 chip, the sfx_bank/voice_treat mix step.
- **Not adopted, M value:** C8b camera deck, C10 RMS lip-sync, A5 desk IK, A24 thumbnail frame score, U5 Korean hook scorer, S4 crop-at, S5/X3 fixed worst-3 loop, E2 earshot model tools (would need librosa/transformers installs).
- **Owner/CEO decisions:** B1 사다리 series, B3 thumbnail format, L3 git guardrails (self-configuration), N3 Test & Compare (manual in Studio).
- **Defects found by the model sheet:** suit tie drawn on the back view; side view draws both front eyes.
