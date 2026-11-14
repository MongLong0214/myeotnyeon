# Task: upload packages for the 2 long-forms (metadata and thumbnails) — W=/Users/isaac/projects/verdict-kr/work

No uploads, no network publishing, and no edits to any video. Output only to `W/upload/longform/<lf2|n18>/`.
Inputs:
- LF2: `episodes/lf2_daejeon_bank/` — facts.md, the cartoon_v6 script/alignment, and the v6fix MP4. A v6fix2 is in progress; use it if it appears.
- N18: `episodes/v4/n18/` — facts.md, facts_enrich.md, cartoon_v6.
- Existing Shorts metadata style: `upload/*_meta_final.txt`.

Produce, for each film:
1. `meta.txt`
   - Title: Korean, provocative, at most 60 characters. Click-bait yes, but nothing false. No victim names.
   - Description: a 2-line hook, chapters (mm:ss, re-measured against the final MP4), sources (at least 2 independent ones per film, from the facts tables), and a disclaimer: "사실에 근거한 재구성 · 인물 비식별 · AI 음성/그래픽 사용".
   - 10–15 tags.
   - Settings: not made for kids; altered/synthetic content disclosure = yes.
2. `thumb_A.jpg` and `thumb_B.jpg`: 1280x720, at most 2 MB, PIL re-save (no EXIF).
   - Build from a high-tension frame of the final MP4 (shot, collapse, courtroom reaction).
   - Large Korean text of at most 8 characters. Match the Shorts visual style.
   - No gore; victims not identifiable.
3. `facts_check.md`: every claim in the title, description and thumbnail mapped to its facts row.
4. `READY.txt`: list of files with sha256. Note any element that must be recomputed after v6fix2, such as the chapter timestamps.

Final message: short, in Korean, with both title options and the thumbnail paths.
