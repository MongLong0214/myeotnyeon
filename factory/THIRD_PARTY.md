<!--
MIT License

Copyright (c) 2026 Mr omi

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files
(the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR
IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

-->
# Third-party code and documentation

## Opus 5.5 Motion Lab — @flxrnc (article; ideas only)

Owner reference: 2026-11-07, “참고할만한게있나”. Supplied article text:
[`unslop/ref_flxrnc_motionlab.txt`](unslop/ref_flxrnc_motionlab.txt). No canonical
article URL was supplied; none is inferred. Used only the captured prose for
easing/spring concepts, motion hierarchy, stagger, ambient continuity, holds,
phone-size exaggeration, beat-grid timing, picture-before-sound, named bans and
measurement ideas. Adapted in `unslop/MOTION_NUMBERS.md`, `unslop/STYLE_VIDEO.md`
and the PROPOSED section of `REVIEW_CHECKLIST.md` for our 2D/30fps house rules.
**No copied code.** Code/prompt blocks were images missing from the capture and
were neither used nor reconstructed. Our numerical starting choices are marked
as local adaptations. This article entry is separate from the MIT code below;
no article license or performance claims are inferred.

## claude-animated-shorts — MIT

Source: https://github.com/mromidev/claude-animated-shorts
Local source revision: `e3b817b6afc6`.
Copyright (c) 2026 Mr omi. Full original MIT notice appears below and in each
adapted module/document header.

| Our file | Allowed upstream source | Adaptation |
|---|---|---|
| `lib/frame_qa.py` | `templates/scripts/short_qa.py` | Streaming every-frame analysis, original thresholds, EOF freeze fix, factory shot adapters, advisory results, FFmpeg loudness, contact sheets. |
| `lib/audio_mix.py` | `templates/audio/mix.py`, `templates/audio/dsp.py` | Word-keyed ducking, linked 4x lookahead limiting and DSP gain/peak concepts; FFmpeg BS.1770 measurement replaces the hand-written loudness meter/WAV loader. No score/SFX synthesis imported. |
| `../production/lf_toon/src/camera2d.ts` | `templates/bridge/story.ts` | Independently re-derived 2D smootherstep timelines, push-ins and decaying impact kicks; no 3D dependencies. |
| `../production/lf_toon/src/expressions.ts` | `templates/bridge/toon.ts` | Fourteen-name declarative table pattern, original rig-local geometry, mandatory nose, local intensity control and deterministic expression effects. |
| `BEATSHEET.md` | `templates/SCRIPT_example.md` | Court-case beat sequence; mid-story snap becomes a dispute/evidence turn, sentence disclosure stays in the final segment under H2. |

No upstream `references/` frames, sheets, STYLE_BIBLE or reports were used or
copied. Our regression images come only from our two local delivery videos.
The upstream ANALYSIS.md was read as requested, followed only by allowed
source templates and LICENSE. No dependencies were installed; no upstream
scripts were executed.

## Entry points and integration

From workspace root, with the existing environment:

```sh
.venv/bin/python -m factory.lib.frame_qa upload/v52_q013_n16_unslop.mp4 /tmp/q013_frame_qa
.venv/bin/python -m factory.lib.frame_qa upload/v52_q014_n15_comedy.mp4 /tmp/q014_frame_qa
```

`factory/review_gates.py:evaluate` calls `frame_qa_advisory`, including the
cached-measurement path. The `FRAME_QA` result is always advisory, including on
measurement errors, and remains advisory through calibration. Reports and
contact sheets are written below that review's `frame_qa/` directory. It adds no
required signoff or blocking checklist rule. Remove the diagnostic call if the
measurements cease to help reviewers; preserve the standalone analyzer.

`--metadata` accepts a shot list or `{shots:[...]}` / render.json `{cues:[...]}`.
Shots accept `[a,b)`, `from/dur`, `start/end` in frames or explicit
`start_s/end_s` in seconds. Factory `cue.a` dictionaries are animation anchors,
not frame starts. Optional `planned`, `xfade`, `flash` are frame intervals;
`holds` explicitly marks intended frozen intervals. Planned cuts suppress pop
candidates around a boundary; they are not evidence that the encoded cut is
correct. Black frames remain visible even at planned cuts. Keep an unmasked
report when checking transition defects.

### New audio only

The mixer is an opt-in preprocessing entry point. Existing render pipelines and
running lanes were not edited; archived deliveries and masters were not remixed.
For the **next new render**, use its raw Supertonic master and its own aligned
word timestamps, then point that new render's audio field at the resulting WAV:

```sh
.venv/bin/python -m factory.lib.audio_mix \
  --voice /path/to/new/raw.wav \
  --words /path/to/new/asr_master.json \
  --music /path/to/new/music.wav \
  --sfx /path/to/new/sfx.wav \
  --out /path/to/new/mix_master.wav
```

Music and SFX are optional. Use a **new path**: the command refuses to overwrite
any output. It never reads/writes an MP4. Run it after word alignment and before
publishing the new master to a render's public asset directory. Do not feed
`timing.json` frame intervals as words. Supertonic's `fresh.py` / `prepare_v52.py`
already creates global Whisper `segments[].words[]` in seconds; `word_spans`
accepts these master ASRs directly. A word-only JSON list with `start/end` or
`s/e` seconds is also accepted. For selected per-take ASRs,
`supertonic_words(audio_json, take_asrs_by_item_id)` applies each audio.json
item's `new_start_sample / 48000` offset before ducking. Do not offset a master
ASR again. No TTS model or ASR inference is run by the mixer.

Word activity lowers only the music bed with pre-roll, attack and release;
SFX and voice retain their timing. Voice defines the picture duration: pad it
first, and use stems no longer than it. Output is stereo 48 kHz PCM24. The
master is measured after limiting at −14 LUFS (±0.2 LU measurement tolerance),
true peak ≤−1 dBTP; an unreachable/silent target fails without publishing.
AAC encoding can change peak values, so measure the new encoded delivery via
frame QA as well. This port does not retroactively change existing audio.

Camera import examples and coordinate conventions live in the header of
`production/lf_toon/src/camera2d.ts`; expression adapter notes are in
`expressions.ts`. Neither ToonRig nor FightRig scenes were modified. Captions
and A/B/C UI stay outside the transformed world group.

The existing `.gitignore` ignores `/production/lf_toon/`. These two new TS
modules and their test exist on disk; include them explicitly when committing.
No gitignore rules or staging state were changed by this task.

## Verification

```sh
.venv/bin/python -m unittest discover -s factory/tests -v
node --experimental-strip-types --test production/lf_toon/tests/camera2d.test.ts
production/compositor/node_modules/.bin/tsc --noEmit --strict --target es2020 --skipLibCheck production/lf_toon/src/camera2d.ts production/lf_toon/src/expressions.ts
```

[Regression results and false positives](review_runs/cas_adoption/REPORT.md), including the
pre-existing ledger-dependent legacy test failure (6/7 legacy tests pass).
Tests use existing Python packages, FFmpeg and Node/TypeScript; test audio is
synthetic and written only into temporary directories.

## MIT notice

MIT License

Copyright (c) 2026 Mr omi

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files
(the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify,
merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES
OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR
IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

## Hook and caption distillation — 2026-11-07

Accessed 2026-11-07 through GitHub raw file URLs on `main`. Both repositories
are MIT licensed. The following ideas were summarized and adapted into our own
Korean rules and case examples; no complete source files, code, fonts or media
were copied. Repository license links identify each upstream MIT notice; the
existing Mr omi notice above applies to the separate animated-shorts adaptation.

| Repository / license | Read paths and scope | Local use |
|---|---|---|
| [coreyhaines31/marketingskills](https://github.com/coreyhaines31/marketingskills) · [MIT](https://github.com/coreyhaines31/marketingskills/blob/main/LICENSE) | [`skills/social/references/short-form-video.md`](https://raw.githubusercontent.com/coreyhaines31/marketingskills/main/skills/social/references/short-form-video.md) | Action/question openings; outcome-oriented iteration |
| Same repository · MIT | [`skills/copywriting/SKILL.md`](https://raw.githubusercontent.com/coreyhaines31/marketingskills/main/skills/copywriting/SKILL.md), [`skills/copywriting/references/ai-tells.md`](https://raw.githubusercontent.com/coreyhaines31/marketingskills/main/skills/copywriting/references/ai-tells.md): hook/copy clarity and anti-slop portions | Concrete subjects/actions, supported claims, removal of empty reveals and stock phrases |
| Same repository · MIT | [`skills/ad-creative/SKILL.md`](https://raw.githubusercontent.com/coreyhaines31/marketingskills/main/skills/ad-creative/SKILL.md), [`skills/ad-creative/references/hook-system.md`](https://raw.githubusercontent.com/coreyhaines31/marketingskills/main/skills/ad-creative/references/hook-system.md): hook and anti-slop portions | Visual action + spoken question + accessible subtitle; one-variable tests and conversion checks |
| Same repository · MIT | [`skills/ad-creative/references/short-form-video-specs.md`](https://raw.githubusercontent.com/coreyhaines31/marketingskills/main/skills/ad-creative/references/short-form-video-specs.md): hook/caption presentation and associated pacing portions | White outlined captions without pills; conflicting font sizing, timing and fast-cut defaults explicitly rejected |
| [AgriciDaniel/claude-youtube](https://github.com/AgriciDaniel/claude-youtube) · [MIT](https://github.com/AgriciDaniel/claude-youtube/blob/main/LICENSE) | [`skills/claude-youtube/references/retention-scripting-guide.md`](https://raw.githubusercontent.com/AgriciDaniel/claude-youtube/main/skills/claude-youtube/references/retention-scripting-guide.md) | Immediate premise, promise/payoff continuity; numerical benchmarks not adopted as channel evidence |
| Same repository · MIT | [`skills/claude-youtube/sub-skills/hook.md`](https://raw.githubusercontent.com/AgriciDaniel/claude-youtube/main/skills/claude-youtube/sub-skills/hook.md) | Mid-action story opening and a genuine question; 30-second scripts and unsafe shock/agitation tactics rejected |
| Same repository · MIT | [`skills/claude-youtube/sub-skills/shorts.md`](https://raw.githubusercontent.com/AgriciDaniel/claude-youtube/main/skills/claude-youtube/sub-skills/shorts.md) (exists) | First-frame action, coherent next beat; mandatory loops, fixed durations and predicted PASS thresholds rejected |

The requested `sub-skills/hook.md` and `sub-skills/shorts.md` resolve under
`skills/claude-youtube/`; their repository-root URLs returned 404. No linked
YouTube playbooks or other repository content were followed. License links are
attribution links; license-file contents were outside the requested reading scope.

Adapted documents: [HOOKS.md](unslop/HOOKS.md),
[STYLE_VIDEO.md](unslop/STYLE_VIDEO.md), [analytics RULES.md](../channel/analytics/RULES.md).
Owner rules and REVIEW_CHECKLIST facts/red lines take precedence over all
upstream suggestions. No clone or local upstream download was created, so there
is no temporary clone to remove. No render or upload was performed.

## 2026-11-08 adoption — cinecode (MIT), AI-Video-Factory (MIT), ClaudeAnimationBase (MIT)

Sources cloned under `research/*/src`; reports in `research/*/REPORT.md`. Tesseract (proprietary) contributed
no code or text; OpenToonz (BSD-3) nothing in this batch.

| Our file | Source | Use |
|---|---|---|
| `factory/lib/captions.py` | cinecode @67f9807 `scripts/captions.py`, `references/craft.md` §5 — MIT © 2026 Sarp Yıldız | grouping on pauses/clause ends adapted; Korean rules ours. Full MIT notice in file header |
| `production/lf_toon/tools/scene_check.py` | cinecode `scripts/scene_check.py` (earlier copy) | called by `factory/lib/code_lint.py` |
| `factory/lib/code_lint.py` | AI-Video-Factory @47aa05a `packages/video/src/lint.ts` — MIT © 2026 Ersin KOÇ | check list and thresholds; code new. Notice in file header |
| `production/lf_toon/tools/chunk_cache.py` | AI-Video-Factory `packages/video/src/chunks.ts` | chunk-key idea; code new. Notice in file header |
| `production/lf_toon/src/insetLayout.ts`, `MagnifierInset.tsx`, `MacroInsert.tsx` | AI-Video-Factory `callout.ts` and macro insert | placement rules/thresholds; code new. Notice below |
| `factory/lib/phone_check.py` | ClaudeAnimationBase (x-seeconvm) `render.mjs --strip`, 360 px phone test — MIT | idea only |

AI-Video-Factory notice (applies to the rows above that name it):

    MIT License
    Copyright (c) 2026 Ersin KOÇ
    Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
    documentation files (the "Software"), to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and
    to permit persons to whom the Software is furnished to do so, subject to the following conditions:
    The above copyright notice and this permission notice shall be included in all copies or substantial portions of
    the Software.
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
    THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
    CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
    IN THE SOFTWARE.

## 2026-11-08 adoption — youtube-agent-skill (MIT)

Portions adapted from youtube-agent-skill (MIT, © 2026 UtilLayer; © 2026 Jake Schincariol) @e0ac1e7 v1.2.0, cloned at
`research/youtube-agent-skill/src` (full notice: `src/LICENSE`; analysis: `research/youtube-agent-skill/REPORT.md`, items A–D, H).

| Our file | Source | Use |
|---|---|---|
| `factory/lib/retention.py` | `skills/yt-retention/retention.py`, cue loader from `skills/yt-edit/deadair.py` | curve analysis ported; hook cutoff in seconds (Shorts 2.5 s), sign-off window, API rows, spoken line per drop |
| `channel/analytics/retention_pull.py` | `skills/yt-retention/SKILL.md` (API query) | new code; keychain OAuth as in `api_pull.py` |
| `factory/lib/sourcekit.py` | `skills/yt-research/sourcekit.py` | ported; Korean judgment headings, spacing-insensitive find |
| `factory/FACTCHECK_PROMPT.md` | `skills/yt-research/SKILL.md` §3 | independent fact-check method and five verdicts, in Korean |
| `factory/shorts_rules.py` `check_pair` | `skills/yt-package/title.py` | repeat/length/mobile-40 idea; Korean particle stripping ours |
| `factory/lib/chapters.py` | `skills/yt-chapters/chapters.py` | pause + lexical-shift boundaries and YouTube rules; Korean tokens; no draft titles |
| `channels/myeotnyeon/voice.md`, `channels/_template/voice.md` | `templates/voice.md` | section outline; content ours |

    MIT License
    Copyright (c) 2026 UtilLayer
    Copyright (c) 2026 Jake Schincariol
    Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
    documentation files (the "Software"), to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and
    to permit persons to whom the Software is furnished to do so, subject to the following conditions:
    The above copyright notice and this permission notice shall be included in all copies or substantial portions of
    the Software.
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
    THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
    CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
    IN THE SOFTWARE.

## 2026-11-08 absorption pass — cinecode (MIT), ClaudeAnimationBase (MIT), Jakes youtube-agent-skill (MIT)

Matrix: `research/ABSORPTION_MATRIX.md`.

| Our file | Source | Use |
|---|---|---|
| `factory/lib/code_lint.py` `check_rhythm` | cinecode @67f9807 `scripts/validate_shots.py` `rhythm` — MIT © 2026 Sarp Yıldız | shot-length cv ≥ 0.30, no run of 5+ alike (15 %), acts not all one pace (25 %); report-only `rhythm` check in CODE_LINT. Notice in file header |
| `production/lf_toon/src/acting.ts` `takeAt`, `ToonRig.tsx` `ArticulatedGuy take` | ClaudeAnimationBase `src/core.js` `take()`, `src/clawd.js` `emotions()` — MIT © 2026 John Heibel (via our earlier port in `v4/lf2/seq/adopt2.ts`) | acted emotion change: squint, swap under it, squash/stretch, backOut settle; opt-in prop. Notice in file header |
| `factory/lib/retention.py` (`--unit`, ambiguous-axis refusal) | Jakes youtube-agent-skill finding J1 (`retention.py` axis guess) — MIT © 2026 Jake Schincariol | defect report only; no code copied |

ClaudeAnimationBase notice:

    MIT License
    Copyright (c) 2026 John Heibel
    Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
    documentation files (the "Software"), to deal in the Software without restriction, including without limitation
    the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and
    to permit persons to whom the Software is furnished to do so, subject to the following conditions:
    The above copyright notice and this permission notice shall be included in all copies or substantial portions of
    the Software.
    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO
    THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF
    CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
    IN THE SOFTWARE.

## 2026-11-08 absorption pass 2

| Our file | Source | Licence | What |
|---|---|---|---|
| `factory/lib/code_lint.py` `check_scene_loudness` | cinecode @67f9807 C15 (per-scene loudness), via our `production/lf_toon/tools/scene_check.py sound` | MIT © 2026 Sarp Yıldız | opt-in (`scene_loudness`) report of scenes > 3 LU off the median scene |
| `factory/lib/code_lint.py` `check_variety` | AI-Video-Factory `variety.ts` (idea) | MIT © 2026 Ersin KOÇ | opt-in (`variety`) report of 3+ consecutive shots of one size; written anew |
| `factory/lib/audio_evidence.py` | xilo (idea: waveform/spectrum evidence) | MIT | ffmpeg showwavespic/showspectrumpic + ebur128 numbers; written anew |
| `factory/lib/voice_treat.py` | cinecode @67f9807 `scripts/voice_treat.py` CLEAN chain | MIT © 2026 Sarp Yıldız | ported ffmpeg filter chain + limiter; the full MIT notice is in the file header |
| `factory/lib/sfx_bank.py` | earshot @4ac3d2a (github.com/Leonxlnx/earshot); cinecode `references/sound.md` peak-sync rule | MIT © 2026 Leon Lin; MIT © 2026 Sarp Yıldız | peak-synced cue placement. Earshot is called as a subprocess from a local clone (`EARSHOT_SRC`), not vendored; no earshot code in this tree |
| `factory/lib/captions.py` `lint(cps_max=)` | manim-skill lint-subtitles (idea) | idea only | opt-in reading speed / minimum hold flags; written anew |
| `factory/lib/upload_rules.py` | youtube-agent-skill utillayer U9 | MIT | description bytes, hashtag count, title length, Shorts+music rules; written anew |
| `factory/lib/thumb_check.py` | x-nowlovepan (idea) | no licence: idea only | 160/320 px sheet and downscaled text height; written anew |
| `factory/unslop/HOOKS.md` rule | Jakes youtube-agent-skill finding J3 | MIT © 2026 Jake Schincariol | no unsourced percentages or multiples in hook templates; no code |

## 2026-11-08 absorption pass 2 — engine (production/lf_toon/src), all opt-in

| Our file | Source | Use |
|---|---|---|
| `src/motion.ts` `SPRING`, `springTo` | xilo-opus-video `references/craft-rules.md` — MIT © 2026 周行 (Kianzzz) | four purpose presets (w/z converted to hz) and target stacking v0+Σ(vi−vi−1)·spring(t−ti); numbers only, code ours |
| `src/motion.ts` `arcPoint`, `onN` | OpenToonz (BSD-3) stage-object spline / Xsheet holds | idea only, code ours |
| `src/camera2d.ts` `whipPan`, `whipBlur`, `hermitePath`, `retime`, `irisRadius` | cinecode @67f9807 `references/camera-moves.md`, `film.html` CAM — MIT © 2026 Sarp Yıldız | move durations/behaviour; code ours |
| `src/camera2d.ts` `seamFor` | AI-Video-Factory `cut.ts` — MIT © 2026 Ersin KOÇ | transition cycling idea; code ours |
| `src/beats.ts` | AI-Video-Factory `beats.ts` — MIT © 2026 Ersin KOÇ (our earlier port in `v4/lf2/seq/adopt2.ts`) | constants and beat selection; Korean syllable counter ours. Full notice in file header |
| `src/Overlays.tsx` `SpeechBubble` | AI-Video-Factory `bubble.ts` — MIT © 2026 Ersin KOÇ | idea only; Korean eojeol wrap ours |
| `src/Overlays.tsx` `StatusChip` | x-aiwithvinay year badge, 티어백과 progress chip | ideas only (no licence) |
| `src/ToonRig.tsx` `viseme`, `smear` props; `src/insets_stills.tsx` model sheet | OpenToonz lip-sync idea; our LF2 v4 smear; cinecode `modelSheet` idea (MIT) | code ours |

## 2026-11-08 QA gate (`factory/qa/gate.py`, `factory/qa/subtitle_ko.py`, `factory/qa/vision_probe.py`)

Libraries are called, not vendored. No code copied.

| Used by | Library | Licence | NOTICE |
|---|---|---|---|
| `factory/qa/subtitle_ko.py` (H23 line/cue break lint) | kiwipiepy (Kiwi Korean morphological analyser), pip | Apache-2.0 | NOTICE: kiwipiepy © bab2min (Minchul Lee), Apache License 2.0; model files shipped with the package under the same licence |
| `factory/qa/vision_probe.py` (hand/person/head candidates) | deepghs/imgutils `detect_hands`, `detect_person`, `detect_heads`, installed from source in `research/new_refs/.venv` | code MIT; model weights CreativeML OpenRAIL-M | NOTICE: imgutils © deepghs, MIT; hand/person/head detection weights © deepghs under OpenRAIL-M (use restrictions apply; weights are downloaded from Hugging Face, not redistributed) |
| `factory/qa/vision_probe.py` (text boxes, clipping, size) | RapidOCR with PP-OCRv5 Korean mobile recogniser | Apache-2.0 (RapidOCR and PaddleOCR models) | NOTICE: RapidOCR © RapidAI, Apache License 2.0; PP-OCRv5 models © PaddlePaddle Authors, Apache License 2.0 |
| `factory/qa/gate.py` `scene_cuts` (cut intervals, content_val) | PySceneDetect `ContentDetector`, pip | BSD-3-Clause | NOTICE: PySceneDetect © Brandon Castellano, BSD 3-Clause License |
| `factory/qa/gate.py` face fallback | OpenCV `FaceDetectorYN` with YuNet `face_detection_yunet_2023mar.onnx` (opencv_zoo), in `factory/qa/models/` | Apache-2.0 (OpenCV); MIT (YuNet model) | NOTICE: OpenCV © OpenCV team, Apache 2.0; YuNet © Shiqi Yu et al., MIT |
