# UPLOAD — queue → uploader → readback

Input: a package with `READY.txt`, `review.json` verdict PASS and `CTO_PASS` (written by the CTO after CEO review,
never by you). Output: a scheduled Short and a ledger record.

## Commands (from `/Users/isaac/projects/verdict-kr/work`)
1. `python3 factory/ops/queue.py status --channel <key>` → the package must show `approved`.
2. `python3 factory/ops/queue.py next-slots --channel <key> --n 1` → date and time (KST).
3. Upload in the Playwright Studio session: load `factory/ops/uploader/upfn_multi.js`, then
   `up(channelId, file, cover, title, desc, dateStr, timeStr)` with `file = upload/pkg/<id>_B/video.mp4`,
   `cover = cover.jpg`, title and description from `meta.txt` ([제목], [설명]). `channelId` comes from
   `factory/channels/registry.json`. If the guard returns `stop`, follow its message (switch identity); never bypass it.
4. Pin the comment from `meta.txt` [고정 댓글].
5. `python3 factory/ops/queue.py record --pkg upload/pkg/<id>_B --video <VIDEO_ID> --publish-at <ISO> --channel <key>`
6. Readback: `python3 factory/ops/queue.py verify --channel <key>` must show the video `scheduled` at that time.

## Never do
- One upload per day per channel (count today's uploads first). Never upload `zz*` ids (evaluation builds).
- Never delete a video; replacing = set the old one private (`priv.js`) and `queue.py mark --state replaced`.
- Never upload without `CTO_PASS`. Never print keys or tokens.
