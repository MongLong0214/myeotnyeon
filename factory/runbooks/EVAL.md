# EVAL — same case through a Haiku and a Sonnet operator

Purpose: prove that output quality comes from the system. A coordinator (any model or a human) runs one new case
through two operators that see only the runbooks, then compares numbers. No step may rely on the operator's taste.

## Setup (coordinator)
1. Case pack: `factory/specs/eval/CASE_ko_eval1.md` (raw facts + URLs, no spec). For a new pack, copy its shape: pick a
   case from `python3 factory/topic_radar.py report --scan <latest scan>` that passes policy; write only raw facts, URLs,
   channel and an answer key for yourself. Golden specs per format: `factory/specs/golden/{q044,en001,ja001,bc001}.json`.
2. Ids: `zzh<NNN>` for Haiku, `zzs<NNN>` for Sonnet (same NNN = the next free number of the channel, so the
   history checks see the same previous episodes). `zz` ids are never uploaded and never match the queue globs.
3. Start two fresh sessions (`claude --model haiku`, `claude --model sonnet`) in `/Users/isaac/projects/verdict-kr/work`
   with this packet only: the case name, URLs, channel, id, and "Follow factory/runbooks/RESEARCH.md, SPEC.md,
   BUILD.md, REVIEW.md in order. Stop at REVIEW. Report the path of review.json." No other context, no golden-spec hints.
4. Limit: 3 hours wall clock each; count every `make_short.py` invocation (from `build.json` history and the shell log).

## Compare (coordinator, mechanical)
| metric | source | pass rule |
|---|---|---|
| reached READY.txt | `upload/pkg/<id>_B/READY.txt` | both yes |
| builder runs to PASS | count of `build`/`validate` calls | report; ≤ 12 each |
| motion %, bg changes/min, longest same bg, still max, loop seam | `shorts_checks.json` metrics | both inside LIMITS; difference ≤ 3 points motion, ≤ 15/min bg |
| gate PASS items | `shorts_checks.json` gate_pass | difference ≤ 2 |
| fact errors | every number on screen traced in `facts_source.md` (coordinator checks 5 random numbers against the article) | 0 |
| review answers | `review.json` R1-R9, then the coordinator answers R1-R9 on the same sheet | agreement ≥ 8/9 |
| spec differences | `diff` of the two specs: stage, defendant, quiz answer, number of fact lines | report only |

Quality parity = both reach READY, both pass every LIMIT, and the coordinator's own R1-R9 count of "yes" differs by
at most 1. If one operator fails, the failure point is a system gap: add a check or a clearer error message for that
exact step, then rerun only the failed operator. Record each gap in `factory/runbooks/EVAL_LOG.md` (date, step, error
text, fix commit).

## Reference parity (run 2026-11-13; same gate.py version for both sides)
| | q044 hand | zzq044 spec | en001 hand | zzen001 spec |
|---|---|---|---|---|
| motion % | 98.1 | 98.2 | 99.6 | 99.6 |
| bg changes/min | 45.4 | 48.2 | 51.9 | 51.1 |
| longest same bg s | 3.63 | 3.13 | 3.77 | 4.23 |
| loop seam /255 | 6.4 | 6.3 | 10.7 | 11.0 |
| gate.py PASS /24 | 15 | 14 (OCR noise on hands, frame 675) | 15 | 15 |
| own review defects (1 fps sheet) | 2 | 0 | 2 | 2 |
| READY | shipped | yes | shipped | no: post blocks subtitle over face (scan stage) |
q044 hand defects the builder now blocks: Hangul numeral pop `19억 5천` (H16) and a 0.25 s `정답 B,` cue. en001 defects
in both: the `scan` stage puts faces in the subtitle band (library fix), the tally of 4 sits under the `14 felony
charges.` cue. Packages: `upload/pkg/zzq044_B`, `upload/pkg/zzen001_B` (`shorts_checks.json`, `build.json`).
