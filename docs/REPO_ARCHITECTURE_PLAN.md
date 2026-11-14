# myeotnyeon repository — current state and design (CTO, 2026-11-06)

> 최신 상태·계약 대조·브랜치 테스트·첫 이관 단위는 [REPO_MIGRATION_AUDIT.md](REPO_MIGRATION_AUDIT.md)를 참조한다. Run A의 공식 상태와 검토 결과는 이 부록에서 구분한다.

## Diagnosis (what is actually true)
- **GitHub `MongLong0214/myeotnyeon`:** `main` and `dev` hold only the genesis commit (README, index.js, smoke test, ACP contract).
  - All work produced through ACP sits in about 20 unmerged local `task/*` branches (factory/discover, score, facts, cluster, lib).
  - Run A (initial import) is held at BLOCK(42); Run B is cancelled.
- **The production system actually running is in `verdict-kr/work`:** the Shorts factory, review gates, analytics loop, topic scoring, the lf_toon cartoon engine and Remotion. It is not in the repo. It only got a local git (5 commits, no remote) today.
- Result: **the channel's actual operating system lives outside the repo.** It cannot be reviewed, has no CI, and has no recovery path. That is the core debt.

## Target structure (single source of truth = myeotnyeon repo)
```
myeotnyeon/
  factory/            # Shorts and long-form factory pipeline (Python)
    short.py  longform_qa.py  review_gates.py  gates.py  topic_score.py
    lib/              # secrets (keychain), robots, frame_qa, audio_mix
    REVIEW_CHECKLIST.md  BEATSHEET.md  unslop/STYLE_VIDEO.md
  engines/
    toon/             # lf_toon: ToonRig, motion, sets, Captions, camera2d, expressions (Remotion/TS)
    shorts/           # Shorts templates derived from q014 comedy (QuizPanels etc.)
  channel/
    analytics/        # api_pull.py, collect_parse, analyze, RULES.md (data in daily/ is excluded)
    ops/              # upload procedure, ledger schema, Studio runbook (no secrets)
  content/            # per-episode scripts, facts tables, shot designs (text only)
  research/           # topic candidates and scores (text only, raw source text by hash reference)
  docs/               # architecture, decisions (ADR), operations
  .github/workflows/project-ci.yml   # npm test + pytest + tsc (approved contract)
```
- **Media and binaries** (mp4/wav/png, renders, models) are never committed. Keep them under local `verdict-kr/work/media` with a manifest (sha256) only. Back up to external storage later.
- **Secrets** live in the keychain only. Keep the existing screen (2,435 candidate files excluded) and add a secret scan to CI.
- **Branches:** dev = integration, main = release (AGENTS.md). Every change goes through a PR plus CI plus CommitLore records.

## Migration (phases; through the ACP contract path)
1. **Phase 0 (now):** keep `verdict-kr/work` as the canonical working copy. Today's local git is the change history. (done)
2. **Phase 1:** clear Run A's 42 BLOCK findings, or close it and re-contract. Bring the minimal skeleton plus factory/lib into dev.
3. **Phase 2:** migrate the operating code in 3 runs:
   - (a) factory gates and checklist;
   - (b) the toon engine and Shorts templates;
   - (c) channel analytics and topic scoring.
   - Each run comes with tests: pytest for gates and parsers, vitest for camera2d and expressions, and a render smoke on 1 sample.
4. **Phase 3:** switch the production working copy to a repo checkout; `verdict-kr/work` becomes the media store only.
5. **Phase 4:** dev → main release tags (semver) and an operating release cycle.

## Maintenance rules
- Changes always come with tests and CommitLore records (Constraint/Rejected/Warn).
- Owner feedback is added to REVIEW_CHECKLIST the same day and wired into a gate.
- Weekly: dependency, keychain and analytics-token health check; disk cleanup; record CommitLore stale.

## Decisions needed
- The ACP contract scope (Run A treatment, re-contract) needs the CEO's decision.
- The owner held the "factory next contract" until 1,000 subscribers (memory: acp-run-b-do-not-run). **Since the owner asked for "설계, 유지보수 잘해" (design and maintain it well), confirm whether that hold should be lifted.**

## Carried acceptance (from CANCELLED run_d0bd710c7cb84bc7a7cd62f7, CEO 2026-11-06)
Not satisfied; attach to the channel/analytics·research migration unit when a new contract exists (do not start early):
- Daily records of real video observations, per segment (distinguish metadata-only / caption-only / actually watched).
- E2E evidence: observation → improvement hypothesis → applied or held in production.
- Tests: idempotent same-day rerun, access failure, empty results, quota exceeded, recovery of runs missed across a restart.
- Readback of the daily schedule plus proof of actual automatic runs.
The owner's daily reference-learning requirement stays in force.

## First migration unit — minimal contract DRAFT (not created; CEO approval required)
Run A (run_b86c2fe…) CANCELLED 2026-11-06 by the CEO. Its evidence, candidate f975ad3d, branches and review are preserved. Its BLOCK 42 is **not** resolved by cancellation.

- **Goal:** make the caption-split API that current production calls (`chunks/wrap/weight/tc`, called by factory/fresh.py:65,96) canonical in the repo, with byte-identical output.
- **Owned paths:**
  - repo `pipeline/tools/layout.py`, which reuses f975ad3d's version: the only diffs are `import os` and a parameterized EPISODE_DIR;
  - repo `test/layout.test.mjs` (new);
  - the existing `test/pipeline.test.mjs` (V1 kept; nothing removed or skipped).
- **Not owned in this unit:** W/factory/fresh.py (switching the local consumer is a separate operations change), gates, toon, ledger, media.
- **Verification:**
  - `npm test` (network deny);
  - `node --test test/layout.test.mjs`;
  - `py_compile`;
  - the parity script in REPO_MIGRATION_AUDIT.md §4.2: W `episodes/S001/layout.py` vs repo `pipeline/tools/layout.py`; texts = edge cases plus every S001 cue narration; maxline 8/11/14; byte-equal JSON hash.
  - Counter-examples: an empty string, an unbroken long string, a short tail, punctuation, newlines.
- **Public safety:** the new and changed files contain no absolute local paths, emails, session/profile IDs, article texts or media. Run the existing public-safe checker over the changed files, plus the symlink-target check (a defect named by the old review).
- **Rollback:** revert the single merge commit on dev. Production does not import the repo path in this unit, so production is unaffected.

| Run A acceptance | This unit | Follow-up owner | Excluded (reason) |
|---|---|---|---|
| ① T1 mapping, V1 py_compile, V2 episode contract, npm PASS at exact HEAD | V1 + npm + layout behaviour tests | V2 → episode/pipeline unit | — |
| ② no article/media/account publication; independent redact review | Yes, for the changed files | Each later unit, for its own files | — |
| ③ space paths, checker self-test, OS-neutral home, large-file counter-examples; no test weakening | Checker run plus the symlink fix if touched | The public-safe checker unit | — |
| ④ no local path/session/environment publication; PR after test/CI and independent review; honest merge readback | Yes | Every unit | — |
| V3 tsc / V4 compositions / V5 stills / V6 AUDIT render | **Not claimed** | Toon/compositor engine unit (needs CI/manifest approval) | Not exercised by layout.py |
| B/C/D discover/score/facts branches (20) | No | Separate decision (preserve only, per audit §2.3) | Not current production |
