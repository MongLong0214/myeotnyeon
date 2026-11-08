# T4 internal evaluation set: fixed before any scoring run

Fixed on 2026-10-27 01:5x KST, before any run of `factory/score` on this set. The CEO ruling is msg_01960cf6 (Buzz be82cbde, 2026-10-26T16:53Z).

**Scope.** This is an internal set tied to the T4 acceptance, not an external benchmark. It measures whether the scorer reproduces the editorial choice of 2026-10-26. It does not show that the scorer predicts views or subscriber growth.

**Disclosure.** I saw the raw recorded field values while choosing which fields exist (comment counts, publisher counts). I have not run or computed any scorer output on this set.

## Acceptance text

`~/.hermes/cache/scratch/myeotnyeon-tickets.md` T4 (written 2026-10-26 about 13:42 KST):

> a labelled fixture set of the 14 V2 cases plus the 3 shelved car cases. The ranking puts the 5 we actually used into the top 7.

## Population: 17 candidates

- **The 14 V2 cases** come from `research/viral_candidates.json`.
- **The 3 shelved car cases** come from the `SHELVED` entries k003, k004 and k005 in `episodes/quiz/episodes.py`. They were shelved at 2026-10-26T01:42:59Z, per transcript c9f4c740: "Shelved … (owner: too many car cases in a row)".
  - k003 uses source A3-013.
  - k004 uses sources A3-020 and A3-052. These are the 1심 and 항소심 reports of the same event (전주, 경찰 매달고 200m 도주). That makes one candidate with two source records, not two candidates.
  - k005 uses source A3-003.
- **Duplicate check.** No V2 case is the same event as a car case. V2 has no 음주운전 or 경찰관-dragging case.

## Label: used = true for 5 cases

The 5 used cases are V2-05 (#3), V2-11 (#4), V2-01 (#5), V2-02 (#6) and V2-10 (old #7). These were the V2 episodes on the channel when the ticket was written:
- old #7 E4zk6oCIbjA was first seen at 02:59Z;
- #6 1niGnkTw6BA was first seen at 03:06Z;
- the ticket was written about 04:42Z.

The other 12 cases are labelled false.

**Definition note, reported rather than changed.** By the time the ticket was written, V2-15 (q008), V2-07 (q009) and V2-08 (q010) had also been produced, between 11:41 and 12:02 KST. They were not uploaded; handoff §0 says "#8–#10 are not uploaded". The ticket counts 5, so their label stays false.

## Scorer input: `clusters.json`

Each cluster has the following fields. Labels, case ids with meaning, hooks, ranks and editorial fields are never part of the input.
- **`id`** is an opaque `c01…c17`, assigned in sorted order of the source ids. The lexical tie-break in `rankClusters` therefore carries no label.
- **`articles`** is a list of `{ title }`: the recorded news titles, which are `sources[].title` for V2 and `title` for A3.
  - No `headline` or `summary` is set.
  - No leads are set: no lead field was recorded at selection time, and extracting one now would be a new rule chosen after the fact.
- **`verdictConfirmed`** is true for every case. All 17 had a reported verdict; for A3-003 the date is 미확인 but the sentence is reported.
- **`signals`** has three values. Everything else is `null`: velocity, trendSlope, expectationGap (no injected function), reversal, recency (the scorer contract defines no decay constant), drawability and youtubeCompetition.
  - `engagement` = log1p(max_naver_comments) / log1p(max of that field over the population). It is null for the car cases, because their comment counts were not recorded.
  - `crossPlatformSpread` = independent_publishers / max of that field over the population. This counts news outlets only; community spread was not recorded. It is null for the car cases.
  - `outrageMarkers` is null in the input, so the scorer computes it from the titles.

**Known bias.** The car cases are missing engagement and spread, which lowers their scores. All 5 used cases are V2, so this bias favours a PASS.

## Measurement

- **k** is 7.
- **The population** is all 17 candidates. Held and rejected candidates stay in the population but are not ranked.
- **A used case is in the top 7 only if** it is ranked (neither held nor rejected) AND fewer than 7 other ranked candidates have a score ≥ its score. This is the pessimistic tie rule. The id tie-break in `rankClusters` is not relied on.
- **PASS** means all 5 used cases are in the top 7. Anything else is a FAIL.
- **Primary result.** The first run on the final frozen candidate HEAD is the T4 result, and it is recorded as-is.
- **Sensitivity run.** A second, symmetric run sets engagement and crossPlatformSpread to null for all 17 cases. It is reported beside the primary result and never replaces it.
- **Later changes.** Any later change to the scorer or config made after seeing a result is reported separately from this first measurement.
