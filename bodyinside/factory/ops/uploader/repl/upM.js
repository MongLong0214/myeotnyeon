// Multi-channel YouTube Studio upload helper for a Playwright REPL where `st` is the Studio page.
// upM(channelId, file, cover, title, desc, "PRIVATE", "") uploads one Short privately.
//   channelId  target channel id (factory/channels/registry.json channels[].channel_id)
//   dateStr    Studio date-picker text, e.g. "2026. 11. 23."   timeStr  Studio time text, e.g. "오후 7:00"
// Guard: the Studio URL must contain /channel/<channelId> AND #entity-name must equal the registry name.
// Studio follows the active identity, not the URL. If the guard reports another channel, switch identity first:
//   open the avatar menu -> "Switch account" (channel_switcher) -> click the account row whose handle matches
//   the registry handle, then call up() again. Never bypass the guard.
// Replacing a scheduled or published video: never delete the old one. Load priv.js and run setPrivate(oldVideoId)
//   (Studio edit page -> visibility -> Private -> save), then record it:
//   queue.py mark --video OLD --state replaced --note "replaced by NEW"; queue.py record ... --video NEW
// The video ID is dialog_video_id (read inside the uploads dialog), confirmed by: resolve_upload.py --video-id <id> <channelKey> "<exact title>" <started_at> scheduled. Exit 0 required before linking.
// Run this file once in the REPL; it defines up(). It uploads nothing by itself.
// The loader defines UPLOAD_CHANNELS ({channel_id: name}) and UPLOAD_LANGS ({channel_id: Studio language label})
// from the local factory/channels/registry.json before this file (scripts/bodyinside_publish.py load_helpers).
var CHANNELS = typeof UPLOAD_CHANNELS === "object" && UPLOAD_CHANNELS ? UPLOAD_CHANNELS : {};
var sleep = ms => new Promise(r => setTimeout(r, ms));
var guard = async (channelId) => {
  const name = CHANNELS[channelId];
  if (!name) return { stop: "unknown channel id", channelId };
  const g = await st.evaluate(() => ({ url: location.pathname, ch: document.querySelector("#entity-name")?.innerText?.trim(), dlg: !!document.querySelector("input[name=Filedata]") }));
  if (!g.url.includes("/channel/" + channelId)) return { stop: "channel guard: Studio URL is not the target channel", want: channelId, g };
  if (g.ch !== name) return { stop: "channel guard: active identity is a different channel; switch via channel_switcher", want: name, g };
  if (!g.dlg) return { stop: "upload dialog missing", g };
  return null;
};
// Reads the new video's ID from INSIDE the uploads dialog (never page-wide anchors). Returns {id, filename, href} or null.
// Selector set is UNVERIFIED against the live Studio DOM; several are tried, all scoped under ytcp-uploads-dialog.
var readDialogVideoId = async (timeoutMs) => {
  const end = Date.now() + (timeoutMs || 60000);
  while (Date.now() < end) {
    const r = await st.evaluate(() => {
      const d = document.querySelector("ytcp-uploads-dialog"); if (!d) return null;
      const sels = ['ytcp-video-info a[href*="youtu"]', '.video-url-fadeable a', 'a[href*="youtu.be/"]', 'a[href*="youtube.com/shorts/"]', 'a[href*="youtube.com/watch"]'];
      for (const s of sels) for (const a of d.querySelectorAll(s)) {
        const m = (a.href || "").match(/(?:youtu\.be\/|\/shorts\/|[?&]v=)([A-Za-z0-9_-]{11})(?![A-Za-z0-9_-])/);
        if (m) return { id: m[1], href: a.href, filename: (d.querySelector("ytcp-video-info .filename-label, ytcp-video-info [class*=filename]")?.innerText || "").trim() || null };
      }
      return null;
    });
    if (r) return r;
    await sleep(1500);
  }
  return null;
};
// finishUp: pre-check, schedule and publish the already-filled upload dialog. upM calls it; it can also resume a
// dialog that upM left open after a stop, without uploading the file again.
var finishUp = async (channelId, T, dateStr, timeStr, lang) => {
  const pre = await st.evaluate(() => { const d = document.querySelector("ytcp-uploads-dialog"); return { title: d.querySelector("#title-textarea #textbox").innerText, descLen: d.querySelector("#description-textarea #textbox").innerText.length, mfk: d.querySelector("[name=VIDEO_MADE_FOR_KIDS_NOT_MFK]").getAttribute("aria-checked"), ai: d.querySelector("[name=VIDEO_HAS_ALTERED_CONTENT_YES]").getAttribute("aria-checked"), limit: /업로드 한도|upload limit|アップロード.*上限/i.test(d.innerText), ch: document.querySelector("#entity-name")?.innerText?.trim() }; });
  if (pre.limit || pre.mfk !== "true" || pre.ai !== "true" || pre.title !== T || pre.ch !== CHANNELS[channelId]) return { stop: "pre-check failed", pre, lang };
  for (let i = 0; i < 3; i++) { await st.locator("ytcp-uploads-dialog #next-button").click(); await sleep(2500); }
  // dateStr "PRIVATE": upload only, no schedule (upload and scheduling are separate steps); verify Private and a "저장" done button.
  if (dateStr === "PRIVATE") {
    await st.locator("ytcp-uploads-dialog tp-yt-paper-radio-button[name=PRIVATE]").first().click(); await sleep(1500);
    const pv = await st.evaluate(() => { const d = document.querySelector("ytcp-uploads-dialog"); return { priv: d.querySelector("tp-yt-paper-radio-button[name=PRIVATE]")?.getAttribute("aria-checked"), schedOpen: !!d.querySelector("ytcp-visibility-scheduler #datepicker-trigger")?.offsetParent, done: d.querySelector("#done-button")?.innerText?.trim() }; });
    if (pv.priv !== "true" || pv.schedOpen || !/^(저장|Save|保存)$/.test(pv.done || "")) return { stop: "private check failed", pv };
    await st.locator("ytcp-uploads-dialog #done-button").click(); await sleep(9000);
    return { pre, sch: { private: true, ...pv }, lang };
  }
  await st.locator("ytcp-uploads-dialog #second-container-expand-button").first().click(); await sleep(2000);
  await st.locator("ytcp-visibility-scheduler #datepicker-trigger").click(); await sleep(1500);
  const di = st.locator("ytcp-date-picker input").first(); await di.fill(dateStr); await di.press("Enter"); await sleep(1500);
  const ti = st.locator("ytcp-visibility-scheduler #time-of-day-container input").first(); await ti.fill(timeStr); await ti.press("Enter"); await sleep(1500);
  const sch = await st.evaluate(() => { const s = document.querySelector("ytcp-visibility-scheduler"); return { date: s.querySelector("#datepicker-trigger")?.innerText?.trim(), time: s.querySelector("#time-of-day-container input")?.value, tz: [...s.querySelectorAll("yt-icon")].map(i => i.getAttribute("aria-label")).find(a => a && a.includes("GMT")), done: document.querySelector("ytcp-uploads-dialog #done-button")?.innerText?.trim() }; });
  // Studio shows times in the account's time zone; every slot in the registry is KST, so require GMT+0900.
  if (sch.date !== dateStr || sch.time !== timeStr || !(sch.tz || "").includes("GMT+0900") || !/^(예약|Schedule|予約)$/.test(sch.done || "")) return { stop: "schedule check failed", sch };
  await st.locator("ytcp-uploads-dialog #done-button").click(); await sleep(9000);
  return { pre, sch, lang };
};
var upM = async (channelId, file, cover, T, D, dateStr, timeStr) => {
  if (!channelId || !file || !cover || !T || !dateStr || (!timeStr && dateStr !== "PRIVATE")) return { stop: "missing argument" };
  const started_at = new Date().toISOString();
  await st.goto("https://studio.youtube.com/channel/" + channelId + "/videos/short?d=ud");
  await sleep(8000);
  const bad = await guard(channelId);
  if (bad) return bad;
  await st.locator("input[name=Filedata]").setInputFiles(file);
  for (let i = 0; i < 30; i++) { await sleep(2000); if (await st.evaluate(() => !!document.querySelector("ytcp-uploads-dialog #title-textarea #textbox"))) break; }
  await sleep(3000);
  // Bind the ID to THIS upload session, before anything else and before done. No ID => stop, draft stays, nothing is clicked.
  const dlg = await readDialogVideoId(60000);
  if (!dlg) return { stop: "no dialog-bound video id", started_at };
  const dialog_video_id = dlg.id, dialog_filename = dlg.filename;
  await st.locator("ytcp-uploads-dialog #title-textarea #textbox").fill(T);
  await st.locator("ytcp-uploads-dialog #description-textarea #textbox").fill(D || "");
  // cover "none": keep YouTube's auto frame (new channels cannot set custom thumbnails before phone verification).
  if (cover !== "none") await st.locator("ytcp-uploads-dialog input#file-loader").setInputFiles(cover);
  await sleep(5000);
  await st.locator("ytcp-uploads-dialog tp-yt-paper-radio-button[name=VIDEO_MADE_FOR_KIDS_NOT_MFK]").click(); await sleep(800);
  await st.locator("ytcp-uploads-dialog #toggle-button").click(); await sleep(2500);
  await st.locator("ytcp-uploads-dialog tp-yt-paper-radio-button[name=VIDEO_HAS_ALTERED_CONTENT_YES]").click(); await sleep(1200);
  // Video language + title/description language per channel (lang.js pickLang; Studio UI is Korean). A missing option or a
  // mismatching result stops the upload. Channels not in the map are left unset.
  const LANG = typeof UPLOAD_LANGS === "object" && UPLOAD_LANGS ? UPLOAD_LANGS : {};
  const want = LANG[channelId];
  const lang = !want ? { skipped: true } : typeof pickLang === "function" ? await pickLang(st.locator("ytcp-uploads-dialog"), want) : { stop: "pickLang not loaded (lang.js)" };
  // The upload dialog has only the Video language dropdown (title/description language is on the edit page; setLang).
  if (want && (lang.stop || lang.n < 1 || !lang.shown.every(x => x.endsWith(want)))) return { stop: "language check failed", want, lang };
  const fin = await finishUp(channelId, T, dateStr, timeStr, lang);
  if (fin.stop) return { channelId, started_at, dialog_video_id, dialog_filename, ...fin };
  // Title/description language exists only on the edit page: set it (and re-set video language) once the id exists.
  // A failure is returned with the saved video ID so the caller can repair language without uploading again.
  let post = { skipped: true };
  if (want) {
    if (!dialog_video_id) return { stop: "uploaded but no video id for language step", channelId, started_at, ...fin };
    post = await setLang(dialog_video_id, want);
    if (post.stop || post.n < 2 || !post.shown.every(x => x.endsWith(want)))
      return { stop: "upload saved, but language step failed; run setLang(id) and langcheck.py", video_id: dialog_video_id, want, post, ...fin };
  }
  return { channelId, started_at, dialog_video_id, dialog_filename, ...fin, post_lang: post, next: "run langcheck.py <channel> <id>" };

};
console.log("upM(channelId, file, cover, title, desc, dateStr, timeStr) defined");
