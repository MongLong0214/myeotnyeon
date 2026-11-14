# BUILD — spec → package

Input: `episodes/specs/<id>.json` that passed `validate`. Output: `upload/pkg/<id>_B/` with `video.mp4`, `cover.jpg`,
`meta.txt`, `subs.srt`, `cues.md`, `sheets/`, `sheet_1fps.jpg`, `gate/`, `shorts_checks.md`, `build.json`, `READY.txt`.

## Command (run from `/Users/isaac/projects/verdict-kr/work`)
```
.venv/bin/python factory/make_short.py build episodes/specs/<id>.json
```
Takes ~25-40 min (ko TTS ~15 min, render ~4 min, gate ~5 min). Run it in the background and wait; do not run two
builds of the same id. Each step prints `PASS <step>` or stops with `FAIL <step>` and a list of fixes.

| FAIL at | What you do |
|---|---|
| schema / facts / policy / compile (layout) | edit the spec field named in the message, rerun `build` (or `--from compile`) |
| voice | message shows what whisper heard. If it says "applied synonym rewrite", rerun exactly the printed command. Otherwise rewrite that line with plainer words, rerun `--from compile --force-tts` |
| timing | follow the message (merge commas, lengthen or shorten a line), rerun `--from compile` |
| render | a card is empty or an actor mismatches: fix the line, rerun `--from compile`. "subtitle covers a face" on the open/loop line = stage layout bug: pick another stage and report it; on other lines change that line's shots |
| post | read `upload/pkg/<id>_B/shorts_checks.md`; each FAIL row names a number and its limit. Change shots of the named line (more shots for static/bg rate, react instead of a wide stage shot for subject size), rerun `--from compile`. A FAIL on L01 is the stage itself (L01 shots are ignored): change spec `stage` and report it |
| gate | gate.py crashed: send `gate.log` tail to the coordinator; do not retry more than once |

Reruns reuse TTS takes (`raw/<id>/`) unless you pass `--force-tts` (needed after changing any line text).

## Never do
- Never edit `b_format/specs/<id>.json`, `case.json`, TSX, or gate thresholds to make a check pass.
- Never build a golden id (`q044`, `en001`, `ja001`, `bc001`): the builder refuses legacy packages; use a new id.
- Never write `READY.txt` yourself. Never upload from BUILD.
- Beast Clash (`variant: BC`, en) builds with the same command. ja needs the VOICEVOX engine; the builder starts it
  (port 50121) and stops with a message if it cannot.

## Done when
The last line is `PASS` and `READY.txt` exists. Go to REVIEW.md.
