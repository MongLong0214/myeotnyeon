// setLang(vid, label): set Studio "Video language" and "Title and description language" to `label` (default "영어" = English)
// on the video edit page, save, and return what the two dropdowns show. Metadata only; touches nothing else.
// pickLang(scope, label) is shared with upM (upload dialog) so new uploads get the same setting.
var pickLang = async (scope, label) => {
  const out = [];
  const inputs = scope.locator("ytcp-form-language-input");
  const n = await inputs.count();
  for (let i = 0; i < n; i++) {
    await inputs.nth(i).locator("ytcp-dropdown-trigger").first().click();
    await new Promise(r => setTimeout(r, 1500));
    const hit = await st.evaluate((lb) => {
      const it = [...document.querySelectorAll("tp-yt-paper-listbox tp-yt-paper-item, ytcp-text-menu tp-yt-paper-item")].find(e => e.offsetParent && e.innerText.trim() === lb);
      if (!it) return false; it.click(); return true;
    }, label);
    if (!hit) { await st.keyboard.press("Escape"); return { stop: "language option not found", label, i }; }
    await new Promise(r => setTimeout(r, 1200));
    out.push((await inputs.nth(i).innerText()).replace(/\s+/g, " ").trim());
  }
  return { n, shown: out };
};
var setLang = async (vid, label = "영어") => {
  try { await st.goto("https://studio.youtube.com/video/" + vid + "/edit", { waitUntil: "domcontentloaded", timeout: 60000 }); } catch (e) {}
  await new Promise(r => setTimeout(r, 12000));
  await st.locator("#toggle-button").first().click().catch(() => {});
  await new Promise(r => setTimeout(r, 3000));
  const res = await pickLang(st.locator("ytcp-video-metadata-editor"), label);
  if (res.stop) return { vid, ...res };
  const dis = await st.evaluate(() => document.querySelector("#save")?.hasAttribute("disabled"));
  if (!dis) { await st.locator("#save").click(); await new Promise(r => setTimeout(r, 6000)); }
  const after = await st.evaluate(() => document.querySelector("#save")?.hasAttribute("disabled"));
  return { vid, ...res, changed: !dis, savedDisabledAfter: after };
};
console.log("setLang defined");
