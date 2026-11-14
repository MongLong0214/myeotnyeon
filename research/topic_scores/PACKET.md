# Task: data-backed topic selection tool + candidate ranking — W=/Users/isaac/projects/verdict-kr/work

Owner instruction: "소재 결정도 데이터로 입증된 소재들이어야돼 / 실제로사람들이 관심이 많은 소재여야돼" (topics must be proven by data, and people must actually be very interested in them).
Topic choice switches from intuition to measured interest.

## Tool: W/factory/topic_score.py
Use only free, keyless public signals:
1. **YouTube proven demand:**
   - `yt-dlp "ytsearch30:<사건 키워드>" --flat-playlist -J` (/opt/homebrew/bin/yt-dlp).
   - For other channels' videos about the same case, take the view-count sum, max and median, the publication period, and whether any are Shorts.
   - Remove noise by checking that the case keywords match the titles. Do not count this channel's (몇년나옴) own videos.
2. **News reaction:** the number of articles about the case and the comment/reaction counts where public pages expose them (Daum news etc.).
   - Collect without keys or logins, at a low request rate, respecting robots.txt.
   - Do not use the Naver key (held because it was exposed).
3. **Search interest (optional):** Google Trends if it can be fetched without a key. If blocked, skip it and record the reason.
4. Output: a composite score (demand × outrage × confirmed judgment) for each candidate. Keep the raw measurements, the query time and the URLs in `research/topic_scores/<slug>.json`.

## Ranking run
- Candidates:
  - every case in W/research/viral_candidates.md, v3_candidates.md, agent1_case.jsonl and longform_candidates_2026-10-30.md;
  - the topics being prepared in the running lanes (W/episodes/quiz/batch_1107/ and W/research/longform_next/);
  - **plus 20 or more new candidates** — find heavily discussed sentencing cases from the last 3 years via YouTube or news searches.
- Exclusions: sex crimes, child victims, cases with no confirmed sentence, and already-used qids/LF2/N18.
- Calibration check: do this channel's 15 published videos' cases show any correlation between their score and our views? (Use W/channel/analytics/snapshot_2026-11-06.md.) With a small sample, report it as reference only.
- Output: `research/topic_scores/RANKED.md`.
  - Top 15 Shorts candidates and top 6 long-form candidates.
  - For each: the score, the evidence numbers (e.g. "타 채널 동일 사건 영상 조회 합계 1.2M"), the confirmed sentence, and one line on how provocative it is.

The network is for collection only. No paid services. Final message: short, in Korean.
