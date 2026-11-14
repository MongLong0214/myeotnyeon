# RESEARCH — radar → candidate → facts (sources + quotes)

Goal: one case that passes policy, with 2+ sources and verbatim quotes saved locally. Output: the `case`, `sources`
and `facts` blocks of `episodes/specs/<id>.json` plus `episodes/specs/<id>.sources/S*.txt`.

## Commands
1. `python3 factory/topic_radar.py report --scan "$(ls -t research/topic_radar/scan_*.json | head -1)" --top 15` (the newest scan; `report` fails without `--scan`) → pick the top row that is **not** excluded.
2. Find 2-3 news articles on the verdict (search the case name + 판결/징역/sentenced).
3. Write `sources` (S1..S3: outlet, url, published) into a new spec `episodes/specs/<id>.json` copied from a golden spec in `factory/specs/golden/` (q044 ko, en001 en, ja001 ja, bc001 animal). Copy only from `factory/specs/golden/`, never from another episode's spec.
4. `.venv/bin/python factory/make_short.py fetch episodes/specs/<id>.json` — it fetches every URL into `<id>.sources/` even while
   the rest of the spec is unfinished (validate would stop at the schema first). fetch reads each page and, when the page body is drawn by script, retries through a reader service automatically.
   If a source still says `could not read the page`, or a quote is "not found" in a file with only a few thousand chars: fetch the article with Tavily extract (or a browser), paste the article
   text into `episodes/specs/<id>.sources/S<n>.txt` with first line `url: <url>`, rerun fetch.
5. Write `facts`: one fact = one claim + 1-4 quotes **copied character for character** from the saved text
   (`grep -o '.\{60\}징역.\{60\}' episodes/specs/<id>.sources/S1.txt` to find them).
   Every number you will show needs a `values` entry whose `text` is copied from a quote (`3억원`, `12차례`, `2020년 12월`, `징역 3년`, `30 days`, `four felonies`).
6. `case`: `sentence_fact` = the fact quoting the sentence, quoted by **2 different sources**. `finality`/`instance`:
   only what a source says; otherwise `항소 미확인` / `심급 미표기` (en `appeal_unknown`).

## Never do
- Never pick sex crimes or child victims (`sexual_offence`, `victim_minor` must be false; the linter also scans words).
- Never paraphrase inside `quotes[].text`; never type a number that no quote contains.
- Never call a verdict final (`확정`, `final`) unless a source says so.
- Never reuse the previous episode's stage (validate tells you).

## Done when
`validate` prints `PASS facts` and `PASS policy`. Errors name the field and the fix; apply exactly that fix.
