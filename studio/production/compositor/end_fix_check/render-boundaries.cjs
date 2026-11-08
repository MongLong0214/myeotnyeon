// Local-only, reduced-size PNGs. No full-length render and no asset downloads.
const fs = require('node:fs'), path = require('node:path');
const root = path.resolve(__dirname, '..');
require('../src/v4/offline.cjs');
require('../node_modules/@remotion/renderer/dist/assets/download-file.js').downloadFile = async ({url}) => {throw Error(`Downloads disabled: ${url}`)};
const {bundle} = require('@remotion/bundler');
const {selectComposition, renderFrames, openBrowser} = require('@remotion/renderer');
const stage = process.argv[2];
if (!['before', 'after'].includes(stage)) throw Error('Use before or after');
const read = file => JSON.parse(fs.readFileSync(path.join(root, 'public', file), 'utf8'));
const cases = [
  {name: 'v3_q003', file: 'q003/render.json'},
  ...['q012', 'q015', 'q016', 'q017'].map(q => ({name: `v52_${q}`, file: `${q}/v52/render_final.json`, hookStyle: 'v51'})),
  // Aligned timing controls are explicitly synthetic; production source data is unchanged.
  ...['q012', 'q017'].map(q => ({name: `aligned_control_${q}`, file: `${q}/v52/render_final.json`, hookStyle: 'v51', aligned: true})),
];
(async () => {
  const serveUrl = await bundle({entryPoint: path.join(__dirname, `entry-${stage}.tsx`), outDir: path.join(__dirname, `bundle-${stage}`), publicDir: path.join(root, 'public'), enableCaching: false});
  const browserExecutable = path.join(root, 'src/v4spike/chromium.sh');
  const browser = await openBrowser('chrome', {browserExecutable, logLevel: 'error'});
  const manifest = [];
  try {
    for (const item of cases) {
      const doc = read(item.file), outro = doc.cues.at(-1);
      if (item.aligned) {doc.durationInFrames = outro.from + 45; outro.dur = 45;}
      doc.audio = null;
      const fullEndFrom = item.hookStyle ? doc.durationInFrames - 45 : null;
      const from = outro.from - 15, to = Math.max(outro.from, fullEndFrom ?? 0) + 15;
      const inputProps = {doc, ...(item.hookStyle ? {hookStyle: item.hookStyle} : {})};
      const opts = {serveUrl, browserExecutable, puppeteerInstance: browser, inputProps, logLevel: 'error'};
      const composition = {...await selectComposition({...opts, id: 'EndBoundary'}), durationInFrames: doc.durationInFrames};
      const outputDir = path.join(__dirname, stage, item.name);
      fs.mkdirSync(outputDir, {recursive: true});
      await renderFrames({...opts, composition, frameRange: [from, to], scale: .25, muted: true, concurrency: 2,
        imageFormat: 'png', outputDir: null, onStart: () => {}, onFrameUpdate: () => {},
        onFrameBuffer: (buffer, frame) => fs.writeFileSync(path.join(outputDir, `f${String(frame).padStart(5, '0')}.png`), buffer)});
      manifest.push({...item, from, to, outroFrom: outro.from, fullEndFrom, frames: to - from + 1, size: [270,480], audioRendered: false});
      fs.writeFileSync(path.join(__dirname, `manifest-${stage}.json`), JSON.stringify(manifest, null, 2));
      console.log(stage, item.name, from, to);
    }
  } finally {await browser.close({silent: true});}
})().catch(e => {console.error(e); process.exitCode = 1});
