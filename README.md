# myeotnyeon

Status: scaffold — features below are planned and are not implemented yet.

## Target features

An unattended production pipeline for a Korean-language YouTube Shorts channel that turns real, publicly reported Korean court verdicts into 20–40 second sentencing-quiz videos (case → viewer guesses fine / suspended sentence / prison → actual verdict and the court's stated reasons). The system discovers trending verdicts from news and public discussion signals, confirms every fact against at least two independent news reports, generates and voices a script, renders a vertical video from original code-drawn characters, blocks release unless mechanical quality gates pass, schedules one episode per day, and adjusts topic selection and presentation from the channel's own performance metrics.

Requirements:
- Discovery aggregates heat signals (titles, links, counts, timestamps; no stored post bodies) from news search APIs, news rankings and public trend data, and from public community "best" boards, within each source's robots.txt and terms of service.
- A case is eligible only when at least two independent news reports confirm the verdict. Community posts are never a fact source.
- Hard content exclusions are enforced in code: sexual crimes, minor victims, intimate-partner or domestic violence, stalking, named public figures, and cases without a verdict.
- Every on-screen and spoken factual claim traces to a sentence in an archived source. Archived article text stays out of the repository; only URLs, metadata and short quotes are committed.
- Episode specs are schema-validated data. Cue-sheet gates cover duration (22–40 s), a hook on frame 0, caption width and explicit line breaks, and no answer spoiler before the reveal, in the video or in its title, description and comment.
- Korean display text passes a pinned AI-style linter (im-not-ai v2.3.2 signals C-8, C-11, I-4, E-2 and F-5) and a spelling and number-consistency check. The final mix must match the script under speech recognition.
- Visual gates run on every frame: no text inside phone-hidden UI zones, no clipped text, no text overlap, fixed UI elements stable across frames, and cover/first-frame layout parity.
- Audio and video gates: 1080×1920 at 30 fps, BT.709, integrated loudness −14 ±1 LUFS, true peak ≤ −1 dBTP, no freeze over 2.5 s, no black frames, and a voice-to-music gap of at least 14 dB.
- Publishing is idempotent and verifies the target channel before every write. It never re-uploads a published video.
- A metrics loop ingests per-video retention and subscriber signals and updates topic, hook and template choices through Bayesian bandits with a minimum exploration share. Every learned change is a versioned config commit with its evidence.
- Secrets live outside the repository (OS keychain or environment). Final media outputs, raw archives, licensed music and account data are never committed. A public-safety check enforces this in CI.

Target features become usable only after the corresponding slice is implemented and
verified against its seeded issue and milestone acceptance criteria.

## Verification

These commands verify the bootstrap scaffold only; they do not verify the planned features.
They are declared in `.agent-control-plane/project.json`; this list is a copy for
readers, and the manifest is the contract.

- `test` — `npm test`

## Branches

`main` carries release history. `dev` is the integration branch and the default.
Use `feature/*`, `task/*`, `fix/*`, `release/*` and `hotfix/*` for topic branches.
