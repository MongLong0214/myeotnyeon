var setSched = async (vid, dateStr, timeStr) => {
  const wait = ms => new Promise(resolve => setTimeout(resolve, ms));
  await st.goto("https://studio.youtube.com/video/" + vid + "/edit", {waitUntil: "domcontentloaded", timeout: 60000});
  await wait(10000);
  if (await st.evaluate(() => location.pathname) !== "/video/" + vid + "/edit")
    return {vid, stop: "wrong video edit page"};
  await st.locator("ytcp-video-metadata-visibility").first().click();
  await wait(3000);
  const dlg = st.locator("tp-yt-paper-dialog").filter({hasText: "저장 또는 게시"}).first();
  if (!await dlg.locator("#datepicker-trigger").first().isVisible())
    await dlg.locator("#second-container-expand-button").first().click();
  await dlg.locator("#datepicker-trigger").click();
  const date = st.locator("ytcp-date-picker input").first();
  await date.fill(dateStr);
  await date.press("Enter");
  const time = dlg.locator("#time-of-day-container input").first();
  await time.fill(timeStr);
  await time.press("Enter");
  await wait(1200);
  const chk = await st.evaluate(() => {
    const d = [...document.querySelectorAll("tp-yt-paper-dialog")].find(x =>
      /저장 또는 게시/.test(x.innerText) && x.getBoundingClientRect().width > 0);
    const scheduler = d?.querySelector("ytcp-visibility-scheduler");
    return {
      date: d?.querySelector("#datepicker-trigger")?.innerText?.trim(),
      time: d?.querySelector("#time-of-day-container input")?.value,
      tz: [...(scheduler || d || document).querySelectorAll("yt-icon")]
        .map(icon => icon.getAttribute("aria-label")).find(e => e?.includes("GMT")),
    };
  });
  if (chk.date !== dateStr || chk.time !== timeStr || !/GMT\+09:?00/.test(chk.tz || "")) {
    await st.keyboard.press("Escape");
    return {vid, stop: "schedule check failed", chk};
  }
  await dlg.locator("#save-button").click();
  await wait(2500);
  const disabled = await st.evaluate(() => document.querySelector("#save")?.hasAttribute("disabled"));
  if (disabled === false) {
    await st.locator("#save").click();
    await wait(6000);
  }
  return {vid, chk, saved: disabled === false};
};
