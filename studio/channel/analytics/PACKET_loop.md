# Task: an automated analytics → self-improvement loop for the channel — W=.

Inputs:
- Today's snapshot: W/channel/analytics/snapshot_2026-11-06.md
- The 10-30 analysis memo (if present, find it via W/PROJECT_STATUS.md and DECISIONS.md)
- Per-video production records: W/upload/pkg/*, W/upload/*_meta*.txt, episode facts and scripts
- The owner-praised standard: the q014 comedy reenactment

## Build
1. `W/channel/analytics/collect.md` + `collect_parse.py`: a parser that turns the text the CTO collects read-only from Studio (content list, video analytics: views, average view duration and %, viewed vs swiped away, subscribers, traffic sources) into `daily/YYYY-MM-DD.json`.
   - Collection itself is done by the CTO through the Aside repl. The lane does not touch the browser or the network.
   - Write down the exact field schema and the collection procedure.
2. `features.json`: per-video production features from the local records — topic type (death/violence/fraud/animal …), the hook's first 2 s (text and picture), title pattern, length, reenactment present or not (comedy rig vs static panels), answer type, publish date.
3. `analyze.py`: features × performance. With a sample of only 15, do not claim statistical significance. Output a **hypothesis table** (direction, strength, the comparison videos behind it) plus **experiment proposals for the next 7 videos** (A/B axes: hook, reenactment, title, length).
4. `RULES.md`: the factory rules derived from the analysis — topic score, hook rules, title rules, reenactment standard, and a "result-confirmation date" for each hypothesis.
   - Note where each rule needs wiring into factory/short.py, but do not change the code; integration is a separate task.
5. `REPORT_2026-11-06.md`: one page in Korean — the 3 bottlenecks, 3 high-confidence hypotheses, the next week's experiment plan, and the KPI path to 1,000 subscribers.

No invented numbers; label every source. No network. Final message: short, in Korean.
