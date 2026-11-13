// Multi-channel YouTube Studio upload helper for a Playwright REPL where `st` is the Studio page.
// up(channelId, file, cover, title, desc, dateStr, timeStr) schedules one Short.
//   channelId  target channel id (factory/channels/registry.json channels[].channel_id)
//   dateStr    Studio date-picker text, e.g. "2026. 11. 23."   timeStr  Studio time text, e.g. "오후 7:00"
// Guard: the Studio URL must contain /channel/<channelId> AND #entity-name must equal the registry name.
// Studio follows the active identity, not the URL. If the guard reports another channel, switch identity first:
//   open the avatar menu -> "Switch account" (channel_switcher) -> click the account row whose handle matches
//   the registry handle, then call up() again. Never bypass the guard.
// Replacing a scheduled or published video: never delete the old one. Load priv.js and run setPrivate(oldVideoId)
//   (Studio edit page -> visibility -> Private -> save), then record it:
//   queue.py mark --video OLD --state replaced --note "replaced by NEW"; queue.py record ... --video NEW
// Run this file once in the REPL; it defines up(). It uploads nothing by itself.
// Fill from your registry (channel_id -> exact Studio channel name). Example values only.
var CHANNELS = {
  "UCexampleMainChannel000000": "Example Main",
  "UCexampleExperimentEn00000": "Example Experiment EN"
};
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
var up = async (channelId, file, cover, T, D, dateStr, timeStr) => {
  if (!channelId || !file || !cover || !T || !dateStr || !timeStr) return { stop: "missing argument" };
  await st.goto("https://studio.youtube.com/channel/" + channelId + "/videos/short?d=ud");
  await sleep(8000);
  const bad = await guard(channelId);
  if (bad) return bad;
  await st.locator("input[name=Filedata]").setInputFiles(file);
  for (let i = 0; i < 30; i++) { await sleep(2000); if (await st.evaluate(() => !!document.querySelector("ytcp-uploads-dialog #title-textarea #textbox"))) break; }
  await sleep(3000);
  await st.locator("ytcp-uploads-dialog #title-textarea #textbox").fill(T);
  await st.locator("ytcp-uploads-dialog #description-textarea #textbox").fill(D || "");
  await st.locator("ytcp-uploads-dialog input#file-loader").setInputFiles(cover);
  await sleep(5000);
  await st.locator("ytcp-uploads-dialog tp-yt-paper-radio-button[name=VIDEO_MADE_FOR_KIDS_NOT_MFK]").click(); await sleep(800);
  await st.locator("ytcp-uploads-dialog #toggle-button").click(); await sleep(2500);
  await st.locator("ytcp-uploads-dialog tp-yt-paper-radio-button[name=VIDEO_HAS_ALTERED_CONTENT_YES]").click(); await sleep(1200);
  const pre = await st.evaluate(() => { const d = document.querySelector("ytcp-uploads-dialog"); return { title: d.querySelector("#title-textarea #textbox").innerText, descLen: d.querySelector("#description-textarea #textbox").innerText.length, mfk: d.querySelector("[name=VIDEO_MADE_FOR_KIDS_NOT_MFK]").getAttribute("aria-checked"), ai: d.querySelector("[name=VIDEO_HAS_ALTERED_CONTENT_YES]").getAttribute("aria-checked"), limit: /업로드 한도|upload limit|アップロード.*上限/i.test(d.innerText), ch: document.querySelector("#entity-name")?.innerText?.trim() }; });
  if (pre.limit || pre.mfk !== "true" || pre.ai !== "true" || pre.title !== T || pre.ch !== CHANNELS[channelId]) return { stop: "pre-check failed", pre };
  for (let i = 0; i < 3; i++) { await st.locator("ytcp-uploads-dialog #next-button").click(); await sleep(2500); }
  await st.locator("ytcp-uploads-dialog #second-container-expand-button").first().click(); await sleep(2000);
  await st.locator("ytcp-visibility-scheduler #datepicker-trigger").click(); await sleep(1500);
  const di = st.locator("ytcp-date-picker input").first(); await di.fill(dateStr); await di.press("Enter"); await sleep(1500);
  const ti = st.locator("ytcp-visibility-scheduler #time-of-day-container input").first(); await ti.fill(timeStr); await ti.press("Enter"); await sleep(1500);
  const sch = await st.evaluate(() => { const s = document.querySelector("ytcp-visibility-scheduler"); return { date: s.querySelector("#datepicker-trigger")?.innerText?.trim(), time: s.querySelector("#time-of-day-container input")?.value, tz: [...s.querySelectorAll("yt-icon")].map(i => i.getAttribute("aria-label")).find(a => a && a.includes("GMT")), done: document.querySelector("ytcp-uploads-dialog #done-button")?.innerText?.trim() }; });
  // Studio shows times in the account's time zone; every slot in the registry is KST, so require GMT+0900.
  if (sch.date !== dateStr || sch.time !== timeStr || !(sch.tz || "").includes("GMT+0900") || !/^(예약|Schedule|予約)$/.test(sch.done || "")) return { stop: "schedule check failed", sch };
  await st.locator("ytcp-uploads-dialog #done-button").click(); await sleep(9000);
  const link = await st.evaluate(() => [...document.querySelectorAll("a")].map(a => a.href).find(h => /youtube\.com\/shorts\/|youtu\.be\//.test(h)));
  return { channelId, pre, sch, link };
};
console.log("up(channelId, file, cover, title, desc, dateStr, timeStr) defined");
